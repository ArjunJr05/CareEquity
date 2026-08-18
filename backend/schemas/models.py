"""
Pydantic models for data validation and serialization.
Defines request/response schemas for the pipeline.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class GenderEnum(str, Enum):
    """Gender enum for patient demographics."""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class YesNoEnum(str, Enum):
    """Yes/No enum for medical conditions."""
    YES = "Yes"
    NO = "No"
    UNKNOWN = "Unknown"


class SmokingStatusEnum(str, Enum):
    """Smoking status enum."""
    NEVER = "Never"
    FORMER = "Former"
    CURRENT = "Current"
    UNKNOWN = "Unknown"


# ==================== Health Data Models ====================

class HealthMetrics(BaseModel):
    """Individual health metrics from medical records."""
    
    age: int = Field(..., ge=0, le=150)
    gender: Literal["Male", "Female", "Other"]
    race_ethnicity: Optional[Literal["White", "Black", "Hispanic", "Asian", "Other"]] = None
    zipcode: str
    height_cm: float
    weight_kg: float
    bmi: Optional[float] = None
    waist_cm: Optional[float] = None
    hba1c_percent: Optional[float] = None
    glucose_mg_dl: Optional[float] = None
    total_cholesterol_mg_dl: Optional[float] = None
    smoking_history: Literal["Smoker", "Non-Smoker", "Former Smoker"]
    income_poverty_ratio: Optional[float] = None
    
    # Medical history flags (used in different models)
    diabetes: Optional[Literal["Yes", "No", "Unknown"]] = None
    diabetes_diagnosed: Optional[float] = None  # 0 or 1 for numeric version
    hypertension: Optional[Literal["Yes", "No", "Unknown"]] = None
    heart_disease: Optional[Literal["Yes", "No", "Unknown"]] = None
    asthma: Optional[Literal["Yes", "No", "Unknown"]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 43, "gender": "Male", "race_ethnicity": "White", "zipcode": "84620",
                "height_cm": 185.9, "weight_kg": 82.4, "bmi": 23.8,
                "waist_cm": 90.9, "hba1c_percent": 5.5, "glucose_mg_dl": 102,
                "total_cholesterol_mg_dl": 176, "smoking_history": "Smoker",
                "income_poverty_ratio": 4.05,
                "diabetes": "No", "hypertension": "No", "heart_disease": "No", "asthma": "No"
            }
        }


class VitalSigns(BaseModel):
    """Extracted vital signs."""
    systolic_bp: Optional[float] = Field(None, ge=40, le=250)
    diastolic_bp: Optional[float] = Field(None, ge=20, le=180)
    heart_rate: Optional[float] = Field(None, ge=30, le=200)
    temperature: Optional[float] = Field(None, ge=35, le=42)


class LabValues(BaseModel):
    """Extracted laboratory test results."""
    glucose_mg_dl: Optional[float] = Field(None, ge=20, le=500)
    hba1c_percent: Optional[float] = Field(None, ge=3, le=15)
    total_cholesterol_mg_dl: Optional[float] = Field(None, ge=50, le=400)
    ldl_mg_dl: Optional[float] = Field(None, ge=0, le=300)
    hdl_mg_dl: Optional[float] = Field(None, ge=0, le=200)
    triglycerides_mg_dl: Optional[float] = Field(None, ge=0, le=1000)


class MedicalHistory(BaseModel):
    """Extracted medical history."""
    diabetes: Optional[YesNoEnum] = None
    hypertension: Optional[YesNoEnum] = None
    heart_disease: Optional[YesNoEnum] = None
    asthma: Optional[YesNoEnum] = None
    smoking_status: Optional[SmokingStatusEnum] = None


class PatientDemographics(BaseModel):
    """Extracted patient demographic information."""
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[GenderEnum] = None
    zipcode: Optional[str] = None


class PatientProfile(BaseModel):
    """Complete patient profile."""
    patient_id: str
    age: int
    gender: str
    zipcode: str
    bmi: float
    glucose: float
    hba1c: float
    cholesterol: float
    smoking_history: str
    diabetes: Optional[str] = None
    hypertension: Optional[str] = None


class SDOHScores(BaseModel):
    """Social Determinants of Health scores for a community."""
    
    economic_stability_score: float = Field(..., ge=0, le=1)
    healthcare_access_quality_score: float = Field(..., ge=0, le=1)
    education_access_quality_score: float = Field(..., ge=0, le=1)
    neighborhood_built_environment_score: float = Field(..., ge=0, le=1)
    food_security_score: float = Field(..., ge=0, le=1)
    social_community_context_score: float = Field(..., ge=0, le=1)


class HealthReportUpload(BaseModel):
    """Health report uploaded by user containing metrics and member ID."""
    
    member_id: str
    health_metrics: HealthMetrics
    year: int = Field(default=2023, ge=2000, le=2030)


# ==================== Prediction Models ====================

class RiskFactor(BaseModel):
    """Individual risk factor with evidence."""
    
    factor_name: str
    factor_category: str
    risk_contribution: float = Field(..., ge=0, le=1)
    evidence_strength: Literal["Strong", "Moderate", "Suggestive"]


class PredictionResult(BaseModel):
    """Model prediction output for disease risk."""
    
    member_id: str
    disease: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: Literal["Low", "Medium", "High", "Very High"]
    confidence: float = Field(..., ge=0, le=1)
    top_risk_factors: List[RiskFactor]
    sdoh_scores: Optional[SDOHScores] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Knowledge Graph Models ====================

class KBGraphNode(BaseModel):
    """Represents a node in the knowledge graph."""
    
    node_id: str
    node_type: str
    properties: Dict[str, Any]


class KBGraphPath(BaseModel):
    """Represents a path/relationship in the knowledge graph."""
    
    source_node: KBGraphNode
    relationship: str
    target_node: KBGraphNode
    properties: Optional[Dict[str, Any]] = None


class ReasoningChain(BaseModel):
    """Chain of reasoning from KB graph for risk explanation."""
    
    paths: List[KBGraphPath]
    summary: str
    confidence: float


# ==================== RAG Models ====================

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    
    role: Literal["user", "assistant"]
    content: str


class ChatHistory(BaseModel):
    """Conversation history."""
    
    messages: List[ChatMessage] = []
    member_id: Optional[str] = None
    context_type: Literal["general", "personal_health"] = "general"


class ChatResponse(BaseModel):
    """Response from RAG-based chatbot."""
    
    response: str
    source_type: Literal["kb_graph", "rag_documents", "health_data", "combined"]
    confidence: float
    references: Optional[List[str]] = None


# ==================== OCR Models ====================

class OCRMetadata(BaseModel):
    """Metadata about OCR processing."""
    
    confidence_score: float = Field(..., ge=0, le=1)
    rotation_angle: float = Field(...)
    processing_time_seconds: float = Field(..., ge=0)
    tesseract_version: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractedHealthReport(BaseModel):
    """Complete health report extracted from document."""
    
    demographics: PatientDemographics
    vital_signs: VitalSigns
    lab_values: LabValues
    medical_history: MedicalHistory
    raw_ocr_text: str
    ocr_metadata: OCRMetadata
    source_document: str
    confidence_overall: float = Field(..., ge=0, le=1)
    extraction_quality: str
    notes: Optional[str] = None


class OCRProcessResult(BaseModel):
    """Response model for OCR processing."""
    
    success: bool
    extracted_data: Optional[ExtractedHealthReport] = None
    error: Optional[str] = None
    processing_id: str


# ==================== Pipeline Models ====================

class PipelineInput(BaseModel):
    """Complete input for the prediction pipeline."""
    
    health_report: HealthReportUpload
    include_reasoning: bool = True
    include_recommendations: bool = True


class PipelineOutput(BaseModel):
    """Complete output from the prediction pipeline."""
    
    prediction: PredictionResult
    reasoning_chain: Optional[ReasoningChain] = None
    recommendations: Optional[List[str]] = None
    health_guidelines: Optional[List[str]] = None

