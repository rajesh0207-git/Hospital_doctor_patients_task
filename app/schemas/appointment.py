from pydantic import BaseModel
from datetime import datetime

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime

class AppointmentUpdate(BaseModel):
    appointment_date: datetime | None = None
    status: str | None = None