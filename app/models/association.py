from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.base import Base

doctor_patient = Table(
    "doctor_patient",
    Base.metadata,
    Column("doctor_id", Integer, ForeignKey("doctors.id")),
    Column("patient_id", Integer, ForeignKey("patients.id"))
)