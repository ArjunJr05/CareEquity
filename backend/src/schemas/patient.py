from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    name: str = Field(..., example="Jane Doe")
    age: int = Field(..., example=45)
    gender: str = Field("Female", example="Female")
    diabetes: str = Field("No", example="No")
    hypertension: str = Field("No", example="No")
    heart_disease: str = Field("No", example="No")
    asthma: str = Field("No", example="No")
    previous_admission: str = Field("No", example="No")
    er_visits: int = Field(0, example=1)
    lat: float = Field(..., example=41.4993)
    long: float = Field(..., example=-81.6944)
    medication_adherence: int = Field(85, example=90)
    height_cm: Optional[float] = Field(170.0, example=170.0)
    weight_kg: Optional[float] = Field(70.0, example=70.0)
    notes: Optional[str] = Field(None, example="Patient requires housing assistance.")

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True
