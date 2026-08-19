from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import re


class ConfidenceLevel(Enum):
    """OCR extraction confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractionMetadata:
    """Metadata describing extraction quality."""

    field_name: str
    confidence: ConfidenceLevel
    pattern_matched: bool
    raw_text_snippet: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ClinicalContext:
    """Clinical context establishing why SDOH factors matter."""

    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None
    medical_history: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    provider_notes: Optional[str] = None


@dataclass
class PatientInfo:
    """Patient demographic and identification information."""

    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    mrn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


@dataclass
class VitalSigns:
    """Vital signs and biometric measurements."""

    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[str] = None
    bmi: Optional[float] = None


@dataclass
class MedicalProblems:
    """Active and historical medical conditions."""

    active_conditions: Optional[List[str]] = None
    chronic_diseases: Optional[List[str]] = None
    previous_surgeries: Optional[List[str]] = None
    hospitalizations: Optional[List[str]] = None


@dataclass
class Medications:
    """Medication information."""

    current_medications: Optional[List[str]] = None
    dosages: Optional[Dict[str, str]] = None
    allergies: Optional[List[str]] = None
    adverse_reactions: Optional[List[str]] = None


@dataclass
class PreventiveHealth:
    """Preventive care and immunization status."""

    vaccination_status: Optional[str] = None
    vaccinations: Optional[List[str]] = None
    last_screening: Optional[Dict[str, str]] = None
    preventive_visits: Optional[List[str]] = None


@dataclass
class SocialDeterminants:
    """Social Determinants of Health."""

    insurance_status: Optional[str] = None
    employment_status: Optional[str] = None
    housing_status: Optional[str] = None
    food_security: Optional[str] = None
    education_level: Optional[str] = None
    language_spoken: Optional[str] = None
    transportation: Optional[str] = None
    income_level: Optional[str] = None


@dataclass
class LabResults:
    """Laboratory test result."""

    test_name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: Optional[str] = None


@dataclass
class ExtractionResult:
    patient_info: PatientInfo
    clinical_context: ClinicalContext
    vital_signs: VitalSigns
    medical_problems: MedicalProblems
    medications: Medications
    preventive_health: PreventiveHealth
    social_determinants: SocialDeterminants
    lab_results: Optional[List[LabResults]] = None
    metadata: Optional[List[ExtractionMetadata]] = None
    extraction_timestamp: str = None
    document_type: Optional[str] = None
    page_count: Optional[int] = None

    def __post_init__(self):
        if self.extraction_timestamp is None:
            self.extraction_timestamp = datetime.now().isoformat()
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary and remove None values."""

        result = asdict(self)

        def clean(value):
            if isinstance(value, dict):
                return {
                    key: clean(item)
                    for key, item in value.items()
                    if item is not None
                }

            if isinstance(value, list):
                return [
                    clean(item)
                    for item in value
                    if item is not None
                ]

            if isinstance(value, Enum):
                return value.value

            return value

        return clean(result)


class MedicalDocParser(ABC):
    """
    Base class for medical document parsers.

    Provides:
    - regex-based extraction
    - confidence scoring
    - extraction metadata
    """

    def __init__(self, text: str):
        self.text = text
        self.metadata: List[ExtractionMetadata] = []

    @abstractmethod
    def parse(self) -> ExtractionResult:
        """Parse document text."""
        raise NotImplementedError

    def extract_with_confidence(
        self,
        field_name: str,
        pattern: str,
        flags: int = re.IGNORECASE,
        processor=None,
    ):
        """Extract a value using regex and calculate confidence."""

        try:
            matches = re.findall(
                pattern,
                self.text,
                flags=flags,
            )

            if not matches:
                metadata = ExtractionMetadata(
                    field_name=field_name,
                    confidence=ConfidenceLevel.LOW,
                    pattern_matched=False,
                    notes="Pattern not found in text",
                )

                self.metadata.append(metadata)

                return None, ConfidenceLevel.LOW, metadata

            raw_value = matches[0]

            if isinstance(raw_value, tuple):
                raw_value = raw_value[0]

            value = raw_value.strip() if raw_value else None

            if processor and value:
                value = processor(value)

            if len(matches) == 1 and value:
                confidence = ConfidenceLevel.HIGH
            elif len(matches) > 1:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW

            metadata = ExtractionMetadata(
                field_name=field_name,
                confidence=confidence,
                pattern_matched=True,
                raw_text_snippet=str(value)[:100]
                if value is not None
                else None,
            )

            self.metadata.append(metadata)

            return value, confidence, metadata

        except Exception as exc:

            metadata = ExtractionMetadata(
                field_name=field_name,
                confidence=ConfidenceLevel.LOW,
                pattern_matched=False,
                notes=f"Extraction error: {exc}",
            )

            self.metadata.append(metadata)

            return None, ConfidenceLevel.LOW, metadata

    def get_metadata(self):
        """Return extraction metadata."""

        return self.metadata