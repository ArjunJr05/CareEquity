from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime
from datetime import datetime
from ..core.database import Base

class PlanConfig(Base):
    __tablename__ = "plan_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)  # 'free', 'basic', 'pro'
    title = Column(String, nullable=False)
    icon = Column(String, default="shield")
    monthly_price = Column(Float, default=0.0)
    yearly_price = Column(Float, default=0.0)
    subtitle = Column(String, default="")
    features = Column(JSON, default=list)
    button_text = Column(String, default="Get Started")
    button_class = Column(String, default="btn-primary")
    is_popular = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
