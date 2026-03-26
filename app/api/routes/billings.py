from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Query
from datetime import datetime
from app.db.session import SessionLocal
from app.models.billing import Billing
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.schemas.billing import BillingCreate, BillingUpdate
from app.api.deps import get_current_user
from fastapi.responses import FileResponse
import os
from app.utils.pdf import generate_invoice
from sqlalchemy import func
from app.models.billing import Billing
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
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    try:
        # 🔒 START TRANSACTION

        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        if not doctor.is_active:
            raise HTTPException(status_code=400, detail="Doctor inactive")

        appointment = None

        if data.appointment_id:
            appointment = db.query(Appointment).filter(
                Appointment.id == data.appointment_id
            ).first()

            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")

            if appointment.status == "cancelled":
                raise HTTPException(status_code=400, detail="Cancelled appointment")

            # ❌ duplicate billing
            existing = db.query(Billing).filter(
                Billing.appointment_id == data.appointment_id
            ).first()

            if existing:
                raise HTTPException(status_code=400, detail="Billing already exists")

        # ✅ CALCULATE TOTAL
        total_amount = data.consultation_fee + data.additional_charges

        billing = Billing(
            **data.dict(),
            total_amount=total_amount
        )

        db.add(billing)

        # ✅ UPDATE APPOINTMENT STATUS
        if appointment:
            appointment.status = "completed"

        db.commit()   # ✅ COMMIT EVERYTHING TOGETHER

        db.refresh(billing)

        return billing

    except Exception as e:
        db.rollback()   # ❌ ROLLBACK if ANY failure

        raise HTTPException(
            status_code=500,
            detail=f"Transaction failed: {str(e)}"
        )



@router.get("/")
def list_billings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),

    payment_status: str = Query(None),
    doctor_id: int = Query(None),
    patient_id: int = Query(None),
    from_date: datetime = Query(None),
    to_date: datetime = Query(None),

    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(Billing)

    # 🔍 FILTERS
    if payment_status:
        query = query.filter(Billing.payment_status == payment_status)

    if doctor_id:
        query = query.filter(Billing.doctor_id == doctor_id)

    if patient_id:
        query = query.filter(Billing.patient_id == patient_id)

    if from_date:
        query = query.filter(Billing.created_at >= from_date)

    if to_date:
        query = query.filter(Billing.created_at <= to_date)

    # 📊 TOTAL COUNT
    total = query.count()

    # 📄 PAGINATION
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": data
    }


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


from sqlalchemy import func
from fastapi import APIRouter

report_router = APIRouter(prefix="/reports", tags=["Reports"])

from datetime import datetime

@report_router.get("/revenue")
def revenue_report(
    doctor_id: int = None,
    from_date: str = None,
    to_date: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # 🔒 ADMIN ONLY
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(Billing)

    # ✅ FILTER BY DOCTOR
    if doctor_id:
        query = query.filter(Billing.doctor_id == doctor_id)

    # ✅ FILTER BY DATE RANGE
    if from_date:
        query = query.filter(Billing.created_at >= from_date)

    if to_date:
        query = query.filter(Billing.created_at <= to_date)

    total = query.with_entities(func.sum(Billing.total_amount)).scalar()

    return {
        "doctor_id": doctor_id,
        "total_revenue": float(total or 0)
    }




@report_router.get("/revenue-per-doctor")
def revenue_per_doctor(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # 🔒 ADMIN CHECK
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    result = db.query(
        Billing.doctor_id,
        func.sum(Billing.total_amount).label("total_revenue")
    ).group_by(Billing.doctor_id).all()

    # ✅ FIX JSON ERROR
    return [
        {
            "doctor_id": r.doctor_id,
            "total_revenue": float(r.total_revenue)
        }
        for r in result
    ]


@report_router.get("/revenue-per-day")
def revenue_per_day(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # 🔒 ADMIN ONLY
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    result = db.query(
        func.date(Billing.created_at).label("date"),
        func.sum(Billing.total_amount).label("total_revenue")
    ).group_by(func.date(Billing.created_at)).all()

    return [
        {
            "date": str(r.date),
            "total_revenue": float(r.total_revenue)
        }
        for r in result
    ]




@router.get("/{billing_id}/invoice")
def download_invoice(
    billing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    billing = db.query(Billing).filter(Billing.id == billing_id).first()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    patient = db.query(Patient).filter(Patient.id == billing.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == billing.doctor_id).first()

    file_path = f"invoice_{billing_id}.pdf"

    generate_invoice(file_path, billing, patient, doctor)

    return FileResponse(file_path, media_type="application/pdf", filename=file_path)


@router.post("/{billing_id}/pay")
def make_payment(
    billing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    billing = db.query(Billing).filter(Billing.id == billing_id).first()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    if billing.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Already paid")

    # 🔥 SIMULATE PAYMENT SUCCESS
    billing.payment_status = "paid"

    db.commit()
    db.refresh(billing)

    return {
        "message": "Payment successful",
        "billing_id": billing.id,
        "status": billing.payment_status
    }


