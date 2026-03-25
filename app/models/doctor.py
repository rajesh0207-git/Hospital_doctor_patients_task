from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    specialization = Column(String(100))
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    patients = relationship("Patient", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")