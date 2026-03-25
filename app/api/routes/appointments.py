from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from datetime import datetime
from app.api.deps import get_current_user

router = APIRouter(prefix="/appointments", tags=["Appointments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # ✅ Check doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ✅ Check doctor active
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor is inactive")

    # ✅ Check patient exists
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ✅ Prevent overlapping
    existing = db.query(Appointment).filter(
        Appointment.doctor_id == data.doctor_id,
        Appointment.appointment_date == data.appointment_date,
        Appointment.status != "cancelled"
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Doctor already has an appointment at this time"
        )

    appointment = Appointment(**data.dict())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment

@router.get("/")
def list_appointments(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] == "admin":
        return db.query(Appointment).all()

    elif user["role"] == "doctor":
        # assuming doctor user linked via email or id
        return db.query(Appointment).filter(
            Appointment.doctor_id == user["id"]
        ).all()

    else:
        raise HTTPException(status_code=403, detail="Not allowed")

@router.put("/{appointment_id}")
def update_appointment(
    appointment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update")

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for key, value in data.items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)

    return appointment

@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.delete(appointment)
    db.commit()

    return {"message": "Appointment deleted"}


@router.get("/doctors/{doctor_id}")
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return doctor.appointments


@router.get("/patients/{patient_id}")
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient.appointments