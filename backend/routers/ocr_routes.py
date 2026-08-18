"""
OCR API Routes
==============
FastAPI router for document upload and OCR processing endpoints.

Endpoints:
  - POST /api/v1/ocr/upload: Single document upload
  - POST /api/v1/ocr/batch: Batch document processing
  - GET /api/v1/ocr/status/{processing_id}: Check processing status
  - GET /api/v1/ocr/results/{processing_id}: Retrieve results
"""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from services.ocr_service import OCRPipeline, ProcessingConfig
from schemas.models import (
    OCRProcessResult,
    ExtractedHealthReport,
    OCRMetadata,
    PatientDemographics,
    VitalSigns,
    LabValues,
    MedicalHistory,
)

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER INITIALIZATION
# ============================================================================

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])

# Global OCR pipeline instance
ocr_pipeline = OCRPipeline(config=ProcessingConfig())

# Storage for processing results (in production: use database)
PROCESSING_RESULTS = {}
UPLOAD_DIR = Path("./uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# SECTION 1: HELPER FUNCTIONS
# ============================================================================

def generate_processing_id() -> str:
    """Generate unique processing ID"""
    return f"proc_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"


def save_uploaded_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file to disk.
    
    Returns: Path to saved file
    """
    file_id = uuid.uuid4().hex[:8]
    file_extension = Path(upload_file.filename).suffix
    saved_filename = f"{file_id}{file_extension}"
    saved_path = UPLOAD_DIR / saved_filename
    
    try:
        with open(saved_path, "wb") as f:
            f.write(upload_file.file.read())
        logger.info(f"Saved uploaded file: {saved_path}")
        return str(saved_path)
    except Exception as e:
        logger.error(f"Failed to save upload file: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Failed to save file: {str(e)}")


def build_extracted_health_report(ocr_result: dict, 
                                  processing_id: str) -> ExtractedHealthReport:
    """
    Convert OCR processing result to ExtractedHealthReport model.
    
    Handles:
      - Field normalization
      - Confidence calculation
      - Validation warnings
    """
    extracted_fields = ocr_result.get("extracted_fields", {})
    
    # Build demographics
    demographics = PatientDemographics(
        patient_name=extracted_fields.get("patient_name"),
        date_of_birth=extracted_fields.get("date_of_birth"),
        age=extracted_fields.get("age"),
        gender=extracted_fields.get("gender"),
        zipcode=extracted_fields.get("zipcode"),
    )
    
    # Build vital signs
    vital_signs = VitalSigns(
        systolic_bp=extracted_fields.get("blood_pressure", [None])[0] 
                   if isinstance(extracted_fields.get("blood_pressure"), tuple) 
                   else None,
        diastolic_bp=extracted_fields.get("blood_pressure", [None, None])[1]
                    if isinstance(extracted_fields.get("blood_pressure"), tuple) 
                    else None,
        heart_rate=extracted_fields.get("heart_rate"),
        temperature=extracted_fields.get("temperature"),
        height_cm=extracted_fields.get("height"),
        weight_kg=extracted_fields.get("weight"),
        bmi=extracted_fields.get("bmi"),
    )
    
    # Build lab values
    lab_values = LabValues(
        glucose_mg_dl=extracted_fields.get("glucose"),
        hba1c_percent=extracted_fields.get("hba1c"),
        total_cholesterol_mg_dl=extracted_fields.get("cholesterol"),
        ldl_mg_dl=extracted_fields.get("ldl"),
        hdl_mg_dl=extracted_fields.get("hdl"),
        triglycerides_mg_dl=extracted_fields.get("triglycerides"),
    )
    
    # Build medical history
    medical_history = MedicalHistory(
        diabetes=extracted_fields.get("diabetes"),
        hypertension=extracted_fields.get("hypertension"),
        smoking_status=extracted_fields.get("smoking"),
    )
    
    # Calculate confidence and quality
    confidence = ocr_result.get("confidence", 0.5)
    extraction_quality = calculate_extraction_quality(confidence)
    
    # Validate and collect warnings
    warnings = []
    warnings.extend(validate_vital_signs(vital_signs))
    warnings.extend(validate_lab_values(lab_values))
    
    notes = " | ".join(warnings) if warnings else None
    
    # Build OCR metadata
    ocr_metadata = OCRMetadata(
        confidence_score=confidence,
        rotation_angle=ocr_result.get("rotation_angle", 0.0),
        processing_time_seconds=ocr_result.get("processing_time", 0.0),
        tesseract_version="5.2.0",  # Should be detected dynamically
    )
    
    # Build complete report
    return ExtractedHealthReport(
        demographics=demographics,
        vital_signs=vital_signs,
        lab_values=lab_values,
        medical_history=medical_history,
        raw_ocr_text=ocr_result.get("raw_text", ""),
        ocr_metadata=ocr_metadata,
        source_document=ocr_result.get("source_file", "unknown"),
        confidence_overall=confidence,
        extraction_quality=extraction_quality,
        notes=notes,
    )


# ============================================================================
# SECTION 2: SINGLE DOCUMENT UPLOAD ENDPOINT
# ============================================================================

@router.post("/upload", response_model=OCRProcessResult)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    patient_id: str = Query(None, description="Optional patient ID")
) -> OCRProcessResult:
    """
    Upload and process a single health document.
    
    Workflow:
      1. Save uploaded file
      2. Run OCR pipeline
      3. Extract health fields
      4. Return results
    
    Args:
        file: Document image (JPG, PNG, PDF)
        patient_id: Optional patient identifier
    
    Returns:
        OCRProcessResult with extracted data or error
    """
    processing_id = generate_processing_id()
    
    try:
        logger.info(f"[{processing_id}] Received upload: {file.filename}")
        
        # Validate file
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. "
                       f"Use: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        file_path = save_uploaded_file(file)
        logger.info(f"[{processing_id}] File saved: {file_path}")
        
        # Run OCR pipeline
        logger.info(f"[{processing_id}] Starting OCR processing...")
        ocr_result = ocr_pipeline.process_document(file_path)
        logger.info(f"[{processing_id}] OCR complete. "
                   f"Confidence: {ocr_result['confidence']:.2%}")
        
        # Build response model
        extracted_report = build_extracted_health_report(ocr_result, processing_id)
        
        # Store result
        PROCESSING_RESULTS[processing_id] = {
            'extracted_data': extracted_report,
            'patient_id': patient_id,
            'file_path': file_path,
            'created_at': datetime.utcnow(),
        }
        
        # Add to RAG vector store so chatbot can query it!
        try:
            rag_service = getattr(request.app.state, "rag_service", None)
            if rag_service and extracted_report.raw_ocr_text:
                from langchain.schema import Document
                doc = Document(
                    page_content=extracted_report.raw_ocr_text,
                    metadata={
                        "source": file.filename,
                        "patient_id": patient_id or "DEMO001",
                        "processing_id": processing_id,
                        "type": "uploaded_patient_report"
                    }
                )
                success = rag_service.add_documents([doc])
                logger.info(f"[{processing_id}] Added document to RAG: {success}")
        except Exception as e:
            logger.error(f"[{processing_id}] Failed to add document to RAG: {str(e)}")

        logger.info(f"[{processing_id}] Processing complete")
        
        return OCRProcessResult(
            success=True,
            extracted_data=extracted_report,
            processing_id=processing_id,
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"[{processing_id}] Processing failed: {str(e)}")
        return OCRProcessResult(
            success=False,
            error=str(e),
            processing_id=processing_id,
        )


# ============================================================================
# SECTION 3: BATCH PROCESSING ENDPOINT
# ============================================================================

@router.post("/batch")
async def batch_upload(
    files: list[UploadFile] = File(...),
    patient_ids: list[str] = Query(None, description="Optional patient IDs")
):
    """
    Upload and process multiple documents in batch.
    
    Args:
        files: List of document images
        patient_ids: Optional list of patient IDs (must match file count)
    
    Returns:
        Batch processing status with per-document results
    """
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    logger.info(f"[{batch_id}] Starting batch processing of {len(files)} files")
    
    results = []
    successful = 0
    failed = 0
    
    for idx, file in enumerate(files):
        patient_id = patient_ids[idx] if patient_ids and idx < len(patient_ids) else None
        
        try:
            # Save file
            file_path = save_uploaded_file(file)
            
            # Process
            ocr_result = ocr_pipeline.process_document(file_path)
            extracted_report = build_extracted_health_report(ocr_result, batch_id)
            
            processing_id = generate_processing_id()
            
            # Store
            PROCESSING_RESULTS[processing_id] = {
                'extracted_data': extracted_report,
                'patient_id': patient_id,
                'file_path': file_path,
                'created_at': datetime.utcnow(),
            }
            
            results.append(OCRProcessResult(
                success=True,
                extracted_data=extracted_report,
                processing_id=processing_id,
            ))
            successful += 1
            
        except Exception as e:
            logger.error(f"[{batch_id}] File {file.filename} failed: {str(e)}")
            processing_id = generate_processing_id()
            
            results.append(OCRProcessResult(
                success=False,
                error=str(e),
                processing_id=processing_id,
            ))
            failed += 1
    
    logger.info(f"[{batch_id}] Batch complete: "
               f"{successful} success, {failed} failed")
    
    return {
        "batch_id": batch_id,
        "total_documents": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


# ============================================================================
# SECTION 4: STATUS & RESULTS ENDPOINTS
# ============================================================================

@router.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """
    Check processing status for a document.
    
    Returns: Processing metadata and status
    """
    if processing_id not in PROCESSING_RESULTS:
        raise HTTPException(status_code=404, 
                          detail=f"Processing ID {processing_id} not found")
    
    result = PROCESSING_RESULTS[processing_id]
    
    return {
        "processing_id": processing_id,
        "status": "completed",
        "created_at": result['created_at'],
        "patient_id": result.get('patient_id'),
        "confidence": result['extracted_data'].confidence_overall,
        "quality": result['extracted_data'].extraction_quality,
    }


@router.get("/results/{processing_id}")
async def get_processing_results(processing_id: str):
    """
    Retrieve complete OCR processing results.
    
    Returns: Full ExtractedHealthReport
    """
    if processing_id not in PROCESSING_RESULTS:
        raise HTTPException(status_code=404,
                          detail=f"Processing ID {processing_id} not found")
    
    result = PROCESSING_RESULTS[processing_id]
    
    return {
        "processing_id": processing_id,
        "success": True,
        "extracted_data": result['extracted_data'],
        "patient_id": result.get('patient_id'),
    }


# ============================================================================
# SECTION 5: CLEANUP & HEALTH ENDPOINT
# ============================================================================

@router.get("/health")
async def ocr_health_check():
    """Check OCR service health"""
    return {
        "status": "healthy",
        "service": "OCR",
        "version": "1.0.0",
        "cached_results": len(PROCESSING_RESULTS),
    }


@router.post("/cleanup")
async def cleanup_old_results(days: int = Query(7, description="Delete results older than N days")):
    """
    Clean up old processing results and uploaded files.
    
    Args:
        days: Delete results older than this many days
    
    Returns: Number of results cleaned
    """
    from datetime import timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    cleaned_count = 0
    
    for proc_id, result in list(PROCESSING_RESULTS.items()):
        if result['created_at'] < cutoff_time:
            # Delete file
            try:
                file_path = Path(result['file_path'])
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete file {result['file_path']}: {e}")
            
            # Delete result
            del PROCESSING_RESULTS[proc_id]
            cleaned_count += 1
    
    logger.info(f"Cleaned {cleaned_count} old results")
    
    return {
        "cleaned": cleaned_count,
        "cutoff_date": cutoff_time,
        "remaining_results": len(PROCESSING_RESULTS),
    }
