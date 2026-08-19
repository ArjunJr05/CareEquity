from sqlalchemy import Column, Integer, String, DateTime, func
from ..core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event = Column(String(255), nullable=False)
    user = Column(String(255), nullable=False)
    ip_address = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
