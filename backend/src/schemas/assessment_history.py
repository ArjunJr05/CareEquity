from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AssessmentHistoryCreate(BaseModel):
    user_id: Optional[int] = None
    user_email: Optional[str] = None

    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    diabetes: Optional[str] = None
    hypertension: Optional[str] = None
    heart_disease: Optional[str] = None
    asthma: Optional[str] = None

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zipcode: Optional[str] = None

    previous_admission: Optional[str] = None
    er_visits: Optional[int] = None
    medication_adherence: Optional[int] = None

    notes: Optional[str] = None

    # Any additional fields coming from the frontend
    extra_data: Optional[dict[str, Any]] = None


class AssessmentHistoryResponse(BaseModel):
    id: int
    user_id: int

    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    diabetes: Optional[str] = None
    hypertension: Optional[str] = None
    heart_disease: Optional[str] = None
    asthma: Optional[str] = None

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zipcode: Optional[str] = None

    previous_admission: Optional[str] = None
    er_visits: Optional[int] = None
    medication_adherence: Optional[int] = None

    notes: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None
    is_favorite: Optional[Any] = False

    timestamp: datetime

    class Config:
        from_attributes = True