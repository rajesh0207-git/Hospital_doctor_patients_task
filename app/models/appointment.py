from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"))
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))

    appointment_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="scheduled")  
    # scheduled, completed, cancelled

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")