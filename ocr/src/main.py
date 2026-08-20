import os
import tempfile
from datetime import datetime

import pytesseract
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .extractor import extract


# ============================================================
# Environment Configuration
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# ============================================================
# Tesseract Verification
# ============================================================

try:
    version = pytesseract.get_tesseract_version()
    print(f"Tesseract OCR detected: {version}")

except Exception as exc:
    print(
        f"WARNING: Tesseract OCR not found: {exc}"
    )

# ============================================================
# Groq API Verification
# ============================================================

if GROQ_API_KEY:
    print(f"Groq API key configured")
else:
    print(f"WARNING: Groq API key not configured. LLM extraction will be unavailable.")


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="CareEquity Medical Data Extraction API",
    description=(
        "OCR-based extraction of patient, clinical, "
        "and Social Determinants of Health information. "
        "Uses Tesseract OCR + Regex patterns, with Groq LLM fallback."
    ),
    version="2.0.0",
)


# ============================================================
# Supported Formats
# ============================================================

ALLOWED_FORMATS = {
    "patient_details",
    "prescription",
}


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
    }


# ============================================================
# API Information
# ============================================================

@app.get("/info")
def api_info():

    return {
        "name": "CareEquity Medical Data Extraction API",
        "version": "2.0.0",

        "supported_document_types": [
            "PDF",
            "DOCX",
        ],

        "supported_formats": sorted(
            ALLOWED_FORMATS
        ),

        "capabilities": [
            "Patient Demographics",
            "Clinical Context",
            "Vital Signs",
            "Medical Problems",
            "Medications",
            "Preventive Health",
            "Social Determinants of Health",
            "Extraction Quality Metrics",
        ],
    }


# ============================================================
# Document Extraction
# ============================================================

@app.post("/extract")
async def extract_from_document(
    file: UploadFile = File(...),
    file_format: str = "patient_details",
):

    # ========================================================
    # Validate logical document format
    # ========================================================

    if file_format not in ALLOWED_FORMATS:

        raise HTTPException(
            status_code=400,
            detail=(
                "file_format must be one of: "
                + ", ".join(
                    sorted(ALLOWED_FORMATS)
                )
            ),
        )


    # ========================================================
    # Validate filename
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file has no filename.",
        )


    # ========================================================
    # Validate extension
    # ========================================================

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF and DOCX files are supported. "
                f"Received: {extension or 'unknown'}"
            ),
        )


    # ========================================================
    # Validate MIME type
    # ========================================================

    content_type = (
        file.content_type or ""
    ).lower()

    allowed_content_types = {
        "application/pdf",

        (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

        # Some browsers may send DOCX as generic binary.
        "application/octet-stream",
    }

    if content_type not in allowed_content_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported content type. "
                "Only PDF and DOCX files are supported. "
                f"Received: {content_type or 'unknown'}"
            ),
        )


    # ========================================================
    # Temporary file
    # ========================================================

    temp_path = None


    try:

        # ====================================================
        # Save uploaded file
        # ====================================================

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:

            temp_path = temp_file.name

            content = await file.read()

            if not content:

                raise ValueError(
                    "Uploaded file is empty."
                )

            temp_file.write(content)


        # ====================================================
        # Run extraction
        # ====================================================

        result = extract(
            temp_path,
            file_format,
            use_adaptive_preprocessing=True,
        )


        # ====================================================
        # Extraction Metadata
        # ====================================================

        metadata = (
            result.metadata or []
        )


        high_confidence = sum(
            1
            for item in metadata
            if item.confidence.value == "high"
        )


        medium_confidence = sum(
            1
            for item in metadata
            if item.confidence.value == "medium"
        )


        low_confidence = sum(
            1
            for item in metadata
            if item.confidence.value == "low"
        )


        # ====================================================
        # Page Count
        # ====================================================

        page_count = getattr(
            result,
            "page_count",
            None,
        )


        # ====================================================
        # Return Response
        # ====================================================

        return JSONResponse(
            status_code=200,

            content={
                "success": True,

                "filename": file.filename,

                "file_extension": extension,

                "file_format": file_format,

                "timestamp": (
                    datetime.now().isoformat()
                ),

                "data": result.to_dict(),

                "extraction_metadata": {

                    "total_fields_extracted": len(
                        metadata
                    ),

                    "confidence_scores": {

                        "high": (
                            high_confidence
                        ),

                        "medium": (
                            medium_confidence
                        ),

                        "low": (
                            low_confidence
                        ),
                    },

                    "page_count": page_count,

                    "document_type": (
                        result.document_type
                    ),
                },
            },
        )


    # ========================================================
    # Known Errors
    # ========================================================

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File processing error: {exc}"
            ),
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Validation error: {exc}"
            ),
        )


    except NotImplementedError as exc:

        raise HTTPException(
            status_code=501,
            detail=(
                f"Feature not implemented: {exc}"
            ),
        )


    # ========================================================
    # Unexpected Errors
    # ========================================================

    except Exception as exc:

        print(
            "Document extraction error: "
            f"{exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document extraction failed: "
                f"{exc}"
            ),
        )


    # ========================================================
    # Cleanup
    # ========================================================

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:

                os.remove(
                    temp_path
                )

            except Exception as exc:

                print(
                    "Warning: Could not delete "
                    f"temporary file: {exc}"
                )