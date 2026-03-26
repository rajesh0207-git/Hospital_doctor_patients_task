from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from datetime import datetime
from app.db.base import Base

class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    __table_args__ = (
        UniqueConstraint("appointment_id", name="unique_appointment_billing"),
    )

    consultation_fee = Column(Float, nullable=False)
    additional_charges = Column(Float, default=0)
    total_amount = Column(Float)

    payment_status = Column(String(20), default="pending")  # pending, paid, cancelled
    payment_mode = Column(String(20))  # cash, card, upi

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)