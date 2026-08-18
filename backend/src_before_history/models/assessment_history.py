from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, func
from ..core.database import Base


class AssessmentHistory(Base):
    __tablename__ = "assessment_history"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Foreign Key -> users.id
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Patient details
    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)

    # Health conditions
    diabetes = Column(String(50), nullable=True)
    hypertension = Column(String(50), nullable=True)
    heart_disease = Column(String(50), nullable=True)
    asthma = Column(String(50), nullable=True)

    # Physical measurements
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zipcode = Column(String(20), nullable=True)

    # Additional patient information
    previous_admission = Column(String(50), nullable=True)
    er_visits = Column(Integer, nullable=True)
    medication_adherence = Column(Integer, nullable=True)

    # Optional notes
    notes = Column(Text, nullable=True)

    # Keeps any additional frontend fields
    extra_data = Column(JSON, nullable=True)

    # Automatically generated for EVERY submission
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )