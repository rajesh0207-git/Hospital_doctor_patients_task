from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    age = Column(Integer)
    phone = Column(String(10))
    is_deleted = Column(Boolean, default=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"))

    doctor = relationship("Doctor", back_populates="patients")

    appointments = relationship("Appointment", back_populates="patient")