from pydantic import BaseModel, Field
from typing import Optional, Literal

class BillingCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None

    consultation_fee: float = Field(gt=0)
    additional_charges: float = 0

    payment_mode: Literal["cash", "card", "upi"]


class BillingUpdate(BaseModel):
    consultation_fee: Optional[float]
    additional_charges: Optional[float]
    payment_status: Optional[Literal["pending", "paid", "cancelled"]]
    payment_mode: Optional[Literal["cash", "card", "upi"]]