"""
OCR Utility Functions
====================
Helper functions for OCR processing and data formatting.

Functions:
  - Format extracted data for downstream processing
  - Convert between data formats
  - Quality assessment utilities
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: DATA FORMATTING
# ============================================================================

def format_for_prediction_pipeline(extracted_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert extracted health report to format expected by ML prediction pipeline.
    
    Maps OCR-extracted fields to feature format required by models.
    
    Args:
        extracted_report: ExtractedHealthReport dict
    
    Returns:
        Dictionary formatted for ML pipeline input
    """
    demographics = extracted_report.get("demographics", {})
    vital_signs = extracted_report.get("vital_signs", {})
    lab_values = extracted_report.get("lab_values", {})
    medical_history = extracted_report.get("medical_history", {})
    
    # Convert categorical fields
    gender_map = {"Male": 1, "Female": 0, "Other": -1}
    smoking_map = {"Never": 0, "Former": 1, "Current": 2, "Unknown": -1}
    yes_no_map = {"Yes": 1, "No": 0, "Unknown": -1}
    
    formatted = {
        # Demographics
        "age": demographics.get("age"),
        "gender": gender_map.get(demographics.get("gender"), -1),
        "zipcode": demographics.get("zipcode"),
        
        # Vital Signs
        "systolic_bp": vital_signs.get("systolic_bp"),
        "diastolic_bp": vital_signs.get("diastolic_bp"),
        "heart_rate": vital_signs.get("heart_rate"),
        "temperature": vital_signs.get("temperature"),
        "height_cm": vital_signs.get("height_cm"),
        "weight_kg": vital_signs.get("weight_kg"),
        "bmi": vital_signs.get("bmi"),
        
        # Lab Values
        "glucose_mg_dl": lab_values.get("glucose_mg_dl"),
        "hba1c_percent": lab_values.get("hba1c_percent"),
        "total_cholesterol_mg_dl": lab_values.get("total_cholesterol_mg_dl"),
        "ldl_mg_dl": lab_values.get("ldl_mg_dl"),
        "hdl_mg_dl": lab_values.get("hdl_mg_dl"),
        "triglycerides_mg_dl": lab_values.get("triglycerides_mg_dl"),
        
        # Medical History
        "diabetes": yes_no_map.get(medical_history.get("diabetes"), -1),
        "hypertension": yes_no_map.get(medical_history.get("hypertension"), -1),
        "heart_disease": yes_no_map.get(medical_history.get("heart_disease"), -1),
        "asthma": yes_no_map.get(medical_history.get("asthma"), -1),
        "smoking_status": smoking_map.get(medical_history.get("smoking_status"), -1),
    }
    
    # Remove None values for cleaner output
    formatted = {k: v for k, v in formatted.items() if v is not None}
    
    return formatted


def format_for_rag_context(extracted_report: Dict[str, Any]) -> str:
    """
    Convert extracted report to formatted text for RAG chatbot context.
    
    Creates readable summary of patient health for context retrieval.
    
    Args:
        extracted_report: ExtractedHealthReport dict
    
    Returns:
        Formatted text summary
    """
    demographics = extracted_report.get("demographics", {})
    vital_signs = extracted_report.get("vital_signs", {})
    lab_values = extracted_report.get("lab_values", {})
    medical_history = extracted_report.get("medical_history", {})
    
    summary = []
    
    # Demographics section
    if demographics.get("patient_name"):
        summary.append(f"Patient: {demographics['patient_name']}")
    if demographics.get("age"):
        summary.append(f"Age: {demographics['age']} years")
    if demographics.get("gender"):
        summary.append(f"Gender: {demographics['gender']}")
    if demographics.get("zipcode"):
        summary.append(f"Zipcode: {demographics['zipcode']}")
    
    summary.append("\n--- Vital Signs ---")
    if vital_signs.get("systolic_bp"):
        summary.append(f"Blood Pressure: {vital_signs['systolic_bp']}/{vital_signs['diastolic_bp']} mmHg")
    if vital_signs.get("heart_rate"):
        summary.append(f"Heart Rate: {vital_signs['heart_rate']} bpm")
    if vital_signs.get("bmi"):
        summary.append(f"BMI: {vital_signs['bmi']}")
    
    summary.append("\n--- Lab Results ---")
    if lab_values.get("glucose_mg_dl"):
        summary.append(f"Glucose: {lab_values['glucose_mg_dl']} mg/dL")
    if lab_values.get("hba1c_percent"):
        summary.append(f"HbA1c: {lab_values['hba1c_percent']}%")
    if lab_values.get("total_cholesterol_mg_dl"):
        summary.append(f"Total Cholesterol: {lab_values['total_cholesterol_mg_dl']} mg/dL")
    
    summary.append("\n--- Medical History ---")
    if medical_history.get("diabetes"):
        summary.append(f"Diabetes: {medical_history['diabetes']}")
    if medical_history.get("hypertension"):
        summary.append(f"Hypertension: {medical_history['hypertension']}")
    if medical_history.get("smoking_status"):
        summary.append(f"Smoking: {medical_history['smoking_status']}")
    
    return "\n".join(summary)


def format_for_neo4j_enrichment(extracted_report: Dict[str, Any], 
                               patient_id: str) -> Dict[str, Any]:
    """
    Format extracted data for Neo4j patient node creation.
    
    Args:
        extracted_report: ExtractedHealthReport dict
        patient_id: Unique patient identifier
    
    Returns:
        Dictionary with Neo4j node properties
    """
    demographics = extracted_report.get("demographics", {})
    vital_signs = extracted_report.get("vital_signs", {})
    lab_values = extracted_report.get("lab_values", {})
    medical_history = extracted_report.get("medical_history", {})
    
    return {
        "patient_id": patient_id,
        "name": demographics.get("patient_name"),
        "age": demographics.get("age"),
        "gender": demographics.get("gender"),
        "zipcode": demographics.get("zipcode"),
        "systolic_bp": vital_signs.get("systolic_bp"),
        "diastolic_bp": vital_signs.get("diastolic_bp"),
        "heart_rate": vital_signs.get("heart_rate"),
        "bmi": vital_signs.get("bmi"),
        "glucose": lab_values.get("glucose_mg_dl"),
        "hba1c": lab_values.get("hba1c_percent"),
        "cholesterol": lab_values.get("total_cholesterol_mg_dl"),
        "has_diabetes": medical_history.get("diabetes") == "Yes",
        "has_hypertension": medical_history.get("hypertension") == "Yes",
        "has_asthma": medical_history.get("asthma") == "Yes",
        "smoking_status": medical_history.get("smoking_status"),
        "extracted_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# SECTION 2: QUALITY ASSESSMENT
# ============================================================================

def assess_data_completeness(extracted_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess how complete the extracted data is.
    
    Returns:
        Completeness score and breakdown by section
    """
    demographics = extracted_report.get("demographics", {})
    vital_signs = extracted_report.get("vital_signs", {})
    lab_values = extracted_report.get("lab_values", {})
    medical_history = extracted_report.get("medical_history", {})
    
    # Count non-None values in each section
    demo_count = sum(1 for v in demographics.values() if v is not None)
    vitals_count = sum(1 for v in vital_signs.values() if v is not None)
    labs_count = sum(1 for v in lab_values.values() if v is not None)
    history_count = sum(1 for v in medical_history.values() if v is not None)
    
    # Calculate percentages
    demo_pct = (demo_count / 5) * 100 if len(demographics) > 0 else 0
    vitals_pct = (vitals_count / 7) * 100 if len(vital_signs) > 0 else 0
    labs_pct = (labs_count / 6) * 100 if len(lab_values) > 0 else 0
    history_pct = (history_count / 5) * 100 if len(medical_history) > 0 else 0
    
    overall_pct = (demo_count + vitals_count + labs_count + history_count) / 23 * 100
    
    return {
        "overall_completeness": round(overall_pct, 1),
        "demographics_completeness": round(demo_pct, 1),
        "vital_signs_completeness": round(vitals_pct, 1),
        "lab_values_completeness": round(labs_pct, 1),
        "medical_history_completeness": round(history_pct, 1),
        "missing_critical_fields": identify_missing_critical_fields(
            extracted_report
        ),
    }


def identify_missing_critical_fields(extracted_report: Dict[str, Any]) -> List[str]:
    """
    Identify critical fields that are missing.
    
    Critical fields needed for health risk prediction.
    """
    critical_fields = [
        ('demographics', 'age'),
        ('demographics', 'zipcode'),
        ('vital_signs', 'systolic_bp'),
        ('vital_signs', 'weight_kg'),
        ('lab_values', 'glucose_mg_dl'),
        ('medical_history', 'diabetes'),
    ]
    
    missing = []
    
    for section, field in critical_fields:
        section_data = extracted_report.get(section, {})
        if section_data.get(field) is None:
            missing.append(f"{section}.{field}")
    
    return missing


def generate_extraction_report(extracted_report: Dict[str, Any]) -> str:
    """
    Generate human-readable extraction report with quality metrics.
    
    Returns:
        Formatted report text
    """
    confidence = extracted_report.get("confidence_overall", 0)
    quality = extracted_report.get("extraction_quality", "unknown")
    
    completeness = assess_data_completeness(extracted_report)
    
    report_lines = [
        "=== OCR EXTRACTION REPORT ===",
        f"Overall Confidence: {confidence:.1%}",
        f"Quality Grade: {quality.upper()}",
        "",
        "--- Data Completeness ---",
        f"Overall: {completeness['overall_completeness']:.1f}%",
        f"Demographics: {completeness['demographics_completeness']:.1f}%",
        f"Vital Signs: {completeness['vital_signs_completeness']:.1f}%",
        f"Lab Values: {completeness['lab_values_completeness']:.1f}%",
        f"Medical History: {completeness['medical_history_completeness']:.1f}%",
    ]
    
    if completeness['missing_critical_fields']:
        report_lines.append("")
        report_lines.append("--- Missing Critical Fields ---")
        for field in completeness['missing_critical_fields']:
            report_lines.append(f"  • {field}")
    
    if extracted_report.get("notes"):
        report_lines.append("")
        report_lines.append("--- Warnings ---")
        for warning in extracted_report["notes"].split(" | "):
            report_lines.append(f"  ⚠ {warning}")
    
    return "\n".join(report_lines)


# ============================================================================
# SECTION 3: EXPORT & SERIALIZATION
# ============================================================================

def export_to_json(extracted_report: Dict[str, Any], 
                   filepath: str) -> None:
    """Export extracted report to JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(extracted_report, f, indent=2, default=str)
        logger.info(f"Exported report to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to export report: {str(e)}")
        raise


def export_to_csv(extracted_reports: List[Dict[str, Any]], 
                  filepath: str) -> None:
    """
    Export multiple extracted reports to CSV.
    
    Flattens nested structure for tabular format.
    """
    import csv
    
    if not extracted_reports:
        return
    
    try:
        # Flatten first report to get field names
        flattened = []
        for report in extracted_reports:
            flat = _flatten_dict(report)
            flattened.append(flat)
        
        # Get all unique field names
        all_fields = set()
        for flat_report in flattened:
            all_fields.update(flat_report.keys())
        
        all_fields = sorted(list(all_fields))
        
        # Write CSV
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_fields)
            writer.writeheader()
            writer.writerows(flattened)
        
        logger.info(f"Exported {len(extracted_reports)} reports to: {filepath}")
    
    except Exception as e:
        logger.error(f"Failed to export to CSV: {str(e)}")
        raise


def _flatten_dict(d: Dict[str, Any], 
                  parent_key: str = '', 
                  sep: str = '_') -> Dict[str, Any]:
    """Helper function to flatten nested dictionaries"""
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, (list, tuple)):
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    
    return dict(items)
