"""
LLM-based parser using Groq for efficient entity extraction.
Extracts medical data using Groq's API instead of regex patterns.
"""

import json
import os
import re
from typing import Dict, Any

from groq import Groq

from .parser_generic import (
    MedicalDocParser,
    ExtractionResult,
    PatientInfo,
    ClinicalContext,
    VitalSigns,
    MedicalProblems,
    Medications,
    PreventiveHealth,
    SocialDeterminants,
    ExtractionMetadata,
    ConfidenceLevel,
)


class LLMPatientDetailsParser(MedicalDocParser):
    """
    Extract patient information using Groq LLM API.
    More accurate than regex for complex/varied document formats.
    """

    def __init__(self, text: str):
        super().__init__(text)
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def parse(self) -> ExtractionResult:
        """Parse text using LLM and return structured data."""

        extraction = self._extract_medical_data_llm()

        # Map new schema to existing dataclass structure
        patient_info = PatientInfo(
            age=extraction.get("demographics", {}).get("age"),
            gender=extraction.get("demographics", {}).get("sex"),
        )
        
        vital_signs = VitalSigns(
            height=extraction.get("vitals", {}).get("height_cm"),
            weight=extraction.get("vitals", {}).get("weight_kg"), 
            bmi=extraction.get("vitals", {}).get("bmi"),
            heart_rate=extraction.get("vitals", {}).get("resting_heart_rate_bpm"),
            blood_pressure=f"{extraction.get('vitals', {}).get('systolic_bp_mmhg')}/{extraction.get('vitals', {}).get('diastolic_bp_mmhg')}" 
                           if extraction.get('vitals', {}).get('systolic_bp_mmhg') and extraction.get('vitals', {}).get('diastolic_bp_mmhg') 
                           else None
        )
        
        # Put lab values in clinical context notes
        lab_data = {
            **extraction.get("metabolic_panel", {}),
            **extraction.get("kidney_panel", {}), 
            **extraction.get("blood_liver_panel", {})
        }
        
        clinical_context = ClinicalContext(
            provider_notes=f"Lab values extracted: {lab_data}" if any(lab_data.values()) else None
        )

        metadata = self._build_metadata_from_extraction(extraction)

        return ExtractionResult(
            patient_info=patient_info,
            clinical_context=clinical_context,
            vital_signs=vital_signs,
            medical_problems=MedicalProblems(),
            medications=Medications(),
            preventive_health=PreventiveHealth(),
            social_determinants=SocialDeterminants(),
            metadata=metadata,
            document_type="patient_details",
        )

    def _extract_medical_data_llm(self) -> Dict[str, Any]:
        """Use Groq to extract specific medical lab values with enhanced targeting."""

        # Pre-scan text for numerical patterns to guide LLM
        numerical_matches = self._find_numerical_patterns()
        
        # Create targeted extraction based on what we found
        if numerical_matches:
            context_hint = f"Found these numbers in text: {numerical_matches[:10]}"  # First 10 matches
        else:
            context_hint = "No clear numerical values found - extract any available demographic info"

        json_template = (
            '{"demographics":{"age":null,"sex":null,"race_ethnicity":null,"smoking_status":null,'
            '"alcohol_use":null,"sedentary_time_min":null},'
            '"vitals":{"height_cm":null,"weight_kg":null,"bmi":null,"waist_circumference_cm":null,'
            '"systolic_bp_mmhg":null,"diastolic_bp_mmhg":null,"resting_heart_rate_bpm":null},'
            '"metabolic_panel":{"hba1c_percent":null,"fasting_glucose_mgdl":null,'
            '"total_cholesterol_mgdl":null,"ldl_cholesterol_mgdl":null,"hdl_cholesterol_mgdl":null,'
            '"triglycerides_mgdl":null},'
            '"kidney_panel":{"creatinine_mgdl":null,"egfr_ml_min":null,"bun_mgdl":null,'
            '"urine_albumin_mgl":null,"urine_creatinine_mgdl":null,"acr_mgg":null},'
            '"blood_liver_panel":{"hemoglobin_gdl":null,"hematocrit_percent":null,'
            '"wbc_count_k_ul":null,"platelet_count_k_ul":null,"mcv_fl":null,"alt_ul":null,'
            '"ast_ul":null,"albumin_gdl":null,"total_bilirubin_mgdl":null}}'
        )

        # Optimized prompt for medical value extraction
        prompt = (
            "Extract medical lab values and demographics from this text. "
            "Look for numbers next to medical terms. Return only raw JSON.\n"
            f"{context_hint}\n\n"
            "Template: " + json_template + "\n\n"
            f"TEXT:\n{self.text[:2500]}\n\nJSON:"
        )

        response_text = ""
        try:
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Deterministic for numerical extraction
                max_tokens=2000,
            )

            response_text = message.choices[0].message.content.strip()

            # Clean response and extract JSON
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text).strip()

            print(f"LLM extracted values: {len([v for section in json.loads(response_text).values() for v in (section.values() if isinstance(section, dict) else []) if v is not None])}")

            extracted_data = json.loads(response_text)
            
            # Enhance with regex fallback for common patterns
            enhanced_data = self._enhance_with_regex_fallback(extracted_data)
            
            return enhanced_data

        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")
            print(f"Response: {response_text[:500]}")
            # Try regex-only extraction as fallback
            return self._regex_only_extraction()

        except Exception as e:
            print(f"LLM API error: {e}")
            return self._regex_only_extraction()

    def _find_numerical_patterns(self) -> list:
        """Pre-scan text for medical numerical patterns."""
        patterns = [
            r'\b\d+\.\d+\b',  # Decimal numbers (7.2, 120.5)
            r'\b\d+/\d+\b',   # BP ratios (120/80)  
            r'\b\d+\s*%\b',   # Percentages (5.7%)
            r'\b\d+\s*mg/dL\b', # mg/dL units
            r'\b\d+\s*mmHg\b',  # mmHg units
        ]
        
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, self.text, re.IGNORECASE))
        
        return list(set(matches))  # Remove duplicates

    def _enhance_with_regex_fallback(self, llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance LLM extraction with regex patterns for missed values."""
        
        # Common medical value patterns
        regex_patterns = {
            # Demographics
            'age': r'(?:age|Age)\s*:?\s*(\d+)',
            'sex': r'(?:sex|gender|Sex|Gender)\s*:?\s*(male|female|M|F)',
            
            # Vitals  
            'height_cm': r'(?:height|Height)\s*:?\s*(\d+(?:\.\d+)?)\s*(?:cm|CM)',
            'weight_kg': r'(?:weight|Weight)\s*:?\s*(\d+(?:\.\d+)?)\s*(?:kg|KG)',
            'bmi': r'(?:BMI|bmi)\s*:?\s*(\d+(?:\.\d+)?)',
            'systolic_bp': r'(?:BP|Blood Pressure)\s*:?\s*(\d+)/\d+',
            'diastolic_bp': r'(?:BP|Blood Pressure)\s*:?\s*\d+/(\d+)',
            
            # Lab values
            'hba1c': r'(?:HbA1c|A1C)\s*:?\s*(\d+(?:\.\d+)?)\s*%?',
            'glucose': r'(?:glucose|Glucose)\s*:?\s*(\d+)\s*mg/dL',
            'creatinine': r'(?:creatinine|Creatinine)\s*:?\s*(\d+(?:\.\d+)?)',
            'cholesterol': r'(?:cholesterol|Cholesterol)\s*:?\s*(\d+)',
        }
        
        enhanced = llm_data.copy()
        
        for field, pattern in regex_patterns.items():
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Convert to appropriate type
                if field in ['age', 'glucose', 'cholesterol']:
                    value = int(value) if value.isdigit() else float(value)
                elif field in ['height_cm', 'weight_kg', 'bmi', 'hba1c', 'creatinine']:
                    value = float(value)
                
                # Map to correct schema location
                if field == 'age':
                    enhanced['demographics']['age'] = value
                elif field == 'sex':
                    enhanced['demographics']['sex'] = value.upper()
                elif field in ['height_cm', 'weight_kg', 'bmi']:
                    enhanced['vitals'][field] = value
                elif field == 'systolic_bp':
                    enhanced['vitals']['systolic_bp_mmhg'] = int(value)
                elif field == 'diastolic_bp':
                    enhanced['vitals']['diastolic_bp_mmhg'] = int(value)
                elif field == 'hba1c':
                    enhanced['metabolic_panel']['hba1c_percent'] = value
                elif field == 'glucose':
                    enhanced['metabolic_panel']['fasting_glucose_mgdl'] = value
                elif field == 'creatinine':
                    enhanced['kidney_panel']['creatinine_mgdl'] = value
                elif field == 'cholesterol':
                    enhanced['metabolic_panel']['total_cholesterol_mgdl'] = value
        
        return enhanced

    def _regex_only_extraction(self) -> Dict[str, Any]:
        """Fallback to regex-only extraction when LLM fails."""
        print("Using regex-only fallback extraction")
        base_structure = self._empty_extraction()
        return self._enhance_with_regex_fallback(base_structure)

    def _build_metadata_from_extraction(self, extraction: Dict[str, Any]):
        """Build metadata list from extracted data."""

        metadata = []

        def add_metadata(field_name: str, value: Any, confidence_str: str = "high"):
            # Convert string to ConfidenceLevel enum
            confidence_map = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM, 
                "low": ConfidenceLevel.LOW
            }
            confidence = confidence_map.get(confidence_str, ConfidenceLevel.HIGH)
            
            if value is not None and value != "" and value != [] and value != {}:
                meta = ExtractionMetadata(
                    field_name=field_name,
                    confidence=confidence,
                    pattern_matched=True,
                    raw_text_snippet=str(value)[:100],
                    notes=None,
                )
            else:
                meta = ExtractionMetadata(
                    field_name=field_name,
                    confidence=ConfidenceLevel.LOW,
                    pattern_matched=False,
                    raw_text_snippet=None,
                    notes="Not found in text",
                )
            metadata.append(meta)

        for section, fields in extraction.items():
            if isinstance(fields, dict):
                for field_name, value in fields.items():
                    add_metadata(f"{section}.{field_name}", value, "high" if value else "low")
            elif isinstance(fields, list):
                add_metadata(section, fields, "high" if fields else "low")

        return metadata

    @staticmethod
    def _empty_extraction() -> Dict[str, Any]:
        """Return empty extraction structure for the new schema."""
        return {
            "demographics": {},
            "vitals": {},
            "metabolic_panel": {},
            "kidney_panel": {},
            "blood_liver_panel": {},
        }
