"""
LLM-based parser using Groq for efficient entity extraction.
Extracts medical data using Groq's API instead of regex patterns.
"""

import json
import os
from typing import Optional, Dict, Any
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
        self.model = "openai/gpt-oss-120b"

    def parse(self) -> ExtractionResult:
        """Parse text using LLM and return structured data."""

        # Extract all data using single LLM call
        extraction = self._extract_medical_data_llm()

        # Convert to dataclass objects
        patient_info = PatientInfo(**extraction.get("patient_info", {}))
        clinical_context = ClinicalContext(**extraction.get("clinical_context", {}))
        vital_signs = VitalSigns(**extraction.get("vital_signs", {}))
        medical_problems = MedicalProblems(**extraction.get("medical_problems", {}))
        medications = Medications(**extraction.get("medications", {}))
        preventive_health = PreventiveHealth(**extraction.get("preventive_health", {}))
        social_determinants = SocialDeterminants(**extraction.get("social_determinants", {}))

        # Build metadata for each field
        metadata = self._build_metadata_from_extraction(extraction)

        return ExtractionResult(
            patient_info=patient_info,
            clinical_context=clinical_context,
            vital_signs=vital_signs,
            medical_problems=medical_problems,
            medications=medications,
            preventive_health=preventive_health,
            social_determinants=social_determinants,
            metadata=metadata,
            document_type="patient_details",
        )

    def _extract_medical_data_llm(self) -> Dict[str, Any]:
        """Use Groq to extract medical data from text."""

        prompt = f"""
You are a medical data extraction expert. Extract all medical information from the following document text.
Return ONLY valid JSON with this exact structure (null for missing values):

{{
  "patient_info": {{
    "name": "string or null",
    "date_of_birth": "MM/DD/YYYY or null",
    "age": "integer or null",
    "gender": "Male/Female or null",
    "mrn": "string or null",
    "phone": "string or null",
    "email": "string or null",
    "address": "string or null"
  }},
  "clinical_context": {{
    "chief_complaint": "string or null",
    "reason_for_visit": "string or null",
    "medical_history": ["list of conditions or null"],
    "current_medications": ["list or null"],
    "allergies": ["list or null"],
    "provider_notes": "string or null"
  }},
  "vital_signs": {{
    "blood_pressure": "systolic/diastolic or null",
    "heart_rate": "integer or null",
    "temperature": "float or null",
    "respiratory_rate": "integer or null",
    "oxygen_saturation": "float or null",
    "weight": "float or null",
    "height": "string or null",
    "bmi": "float or null"
  }},
  "medical_problems": {{
    "active_conditions": ["list or null"],
    "chronic_diseases": ["list or null"],
    "previous_surgeries": ["list or null"],
    "hospitalizations": ["list or null"]
  }},
  "medications": {{
    "current_medications": ["list or null"],
    "allergies": ["list or null"],
    "adverse_reactions": ["list or null"]
  }},
  "preventive_health": {{
    "vaccination_status": "string or null",
    "vaccinations": ["list or null"],
    "last_screening": {{"type": "string", "date": "MM/DD/YYYY"}} or null
  }},
  "social_determinants": {{
    "insurance_status": "Yes/No/Unknown or null",
    "employment_status": "string or null",
    "housing_status": "string or null",
    "food_security": "string or null",
    "education_level": "string or null",
    "language_spoken": "string or null",
    "transportation": "Yes/No or null",
    "income_level": "string or null"
  }}
}}

DOCUMENT TEXT:
{self.text[:4000]}

Return ONLY the JSON, no other text.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            extracted_data = json.loads(response_text)
            return extracted_data

        except json.JSONDecodeError:
            # If JSON parsing fails, return empty structure
            print(f"Failed to parse LLM response as JSON")
            return self._empty_extraction()
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return self._empty_extraction()

    def _build_metadata_from_extraction(self, extraction: Dict[str, Any]):
        """Build metadata list from extracted data."""

        metadata = []
        
        # Helper to add metadata
        def add_metadata(field_name: str, value: Any, confidence: str = "high"):
            # Convert string confidence to enum
            conf_level = confidence if confidence in ["high", "medium", "low"] else "high"
            
            if value is not None and value != "":
                meta = ExtractionMetadata(
                    field_name=field_name,
                    confidence=conf_level,
                    pattern_matched=True,
                    raw_text_snippet=str(value)[:100],
                    notes=None
                )
            else:
                meta = ExtractionMetadata(
                    field_name=field_name,
                    confidence="low",
                    pattern_matched=False,
                    raw_text_snippet=None,
                    notes="Not found in text"
                )
            metadata.append(meta)

        # Flatten all fields and add metadata
        for section, fields in extraction.items():
            if isinstance(fields, dict):
                for field_name, value in fields.items():
                    add_metadata(f"{section}.{field_name}", value)
            elif isinstance(fields, list):
                add_metadata(section, fields)

        return metadata

    @staticmethod
    def _empty_extraction() -> Dict[str, Any]:
        """Return empty extraction structure."""
        return {
            "patient_info": {},
            "clinical_context": {},
            "vital_signs": {},
            "medical_problems": {},
            "medications": {},
            "preventive_health": {},
            "social_determinants": {}
        }