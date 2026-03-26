from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.billing import Billing
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.schemas.billing import BillingCreate, BillingUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/billings", tags=["Billings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_billing(
    data: BillingCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # 🔒 Admin only
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create billing")

    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor is inactive")

    # ✅ Appointment validation
    if data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == data.appointment_id
        ).first()

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appointment.doctor_id != data.doctor_id or appointment.patient_id != data.patient_id:
            raise HTTPException(status_code=400, detail="Appointment mismatch")

        if appointment.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot bill cancelled appointment")

        # ❌ Prevent duplicate billing
        existing = db.query(Billing).filter(
            Billing.appointment_id == data.appointment_id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Billing already exists for this appointment")

    # ✅ Auto calculate
    total_amount = data.consultation_fee + data.additional_charges

    billing = Billing(
        **data.dict(),
        total_amount=total_amount
    )

    db.add(billing)
    db.commit()
    db.refresh(billing)

    return billing

@router.get("/{billing_id}")
def get_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    billing = db.query(Billing).filter(Billing.id == billing_id).first()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    return billing


@router.get("/patients/{patient_id}")
def get_patient_billings(
    patient_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return db.query(Billing).filter(Billing.patient_id == patient_id).all()


@router.get("/doctors/{doctor_id}")
def get_doctor_billings(
    doctor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Doctor can only see their data
    if user["role"] == "doctor" and user["id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return db.query(Billing).filter(Billing.doctor_id == doctor_id).all()

@router.put("/{billing_id}")
def update_billing(
    billing_id: int,
    data: BillingUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update")

    billing = db.query(Billing).filter(Billing.id == billing_id).first()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(billing, key, value)

    # ✅ Recalculate
    billing.total_amount = billing.consultation_fee + billing.additional_charges

    db.commit()
    db.refresh(billing)

    return billing


@router.delete("/{billing_id}")
def delete_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    billing = db.query(Billing).filter(Billing.id == billing_id).first()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    billing.is_active = False

    db.commit()

    return {"message": "Billing soft deleted"}

