from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func
from ..core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    diabetes = Column(String(50), nullable=False)
    hypertension = Column(String(50), nullable=False)
    heart_disease = Column(String(50), nullable=False)
    asthma = Column(String(50), nullable=False)
    previous_admission = Column(String(50), nullable=False)
    er_visits = Column(Integer, nullable=False)
    lat = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    medication_adherence = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
