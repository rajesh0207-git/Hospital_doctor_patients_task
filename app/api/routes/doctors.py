from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.doctor import Doctor 
from app.api.deps import get_current_user
from fastapi import HTTPException
from app.schemas.doctor import DoctorCreate
from fastapi import Query
from app.utils.pagination import paginate
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import handle_db_exception
from app.models.association import doctor_patient
from app.models.patient import Patient
from app.models.doctor import Doctor

router = APIRouter(prefix="/doctors", tags=["Doctors"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/")
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="User not allowed")

    doctor = Doctor(**data.dict())

    try:
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        return doctor

    except Exception as e:
        db.rollback()
        raise handle_db_exception(e)




@router.get("/")
def list_doctors(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    specialization: str = Query(None),
    is_active: bool = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor).filter(Doctor.is_active==True)

    # ✅ Filtering (already implemented)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))

    if is_active is not None:
        query = query.filter(Doctor.is_active == True)

    # ✅ Total count BEFORE pagination
    total = query.count()

    # ✅ Pagination logic
    offset = (page - 1) * limit
    doctors = query.offset(offset).limit(limit).all()

    return paginate(query, page, limit)

@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    for key, value in data.items():
        setattr(doctor, key, value)

    db.commit()
    db.refresh(doctor)

    return doctor

@router.get("/{doctor_id}")
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Doctor not found")

    return doctor

@router.get("/{doctor_id}/patients")
def get_doctor_patients(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    # ❌ Doctor not found
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ❌ Doctor inactive
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor is inactive")

    # ✅ Return patients
    return doctor.patients

# ✅ PUT → FULL UPDATE
@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # FULL UPDATE (overwrite all fields)
    doctor.name = data.get("name")
    doctor.email = data.get("email")
    doctor.specialization = data.get("specialization")

    db.commit()
    db.refresh(doctor)

    return doctor


# ✅ PATCH → PARTIAL UPDATE
@router.patch("/{doctor_id}")
def partial_update_doctor(
    doctor_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # PARTIAL UPDATE (only provided fields)
    for key, value in data.items():
        setattr(doctor, key, value)

    db.commit()
    db.refresh(doctor)

    return doctor


# ✅ DELETE → SOFT DELETE
@router.delete("/{doctor_id}")
def soft_delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ✅ SOFT DELETE
    doctor.is_active = False

    db.commit()

    return {"message": "Doctor deactivated (soft delete)"}



# ASSIGN PATIENT
@router.post("/{doctor_id}/patients/{patient_id}")
def assign_patient(
    doctor_id: int,
    patient_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    # ✅ Check existence
    if not doctor or not patient:
        raise HTTPException(status_code=404, detail="Doctor or Patient not found")

    # ✅ NEW: Check doctor is active
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor is inactive")

    # ✅ Optional: Check patient is not deleted (if using soft delete)
    if hasattr(patient, "is_deleted") and patient.is_deleted:
        raise HTTPException(status_code=400, detail="Patient is deleted")

    # ✅ Prevent duplicate assignment (IMPORTANT)
    existing = db.execute(
        doctor_patient.select().where(
            (doctor_patient.c.doctor_id == doctor_id) &
            (doctor_patient.c.patient_id == patient_id)
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already assigned")

    # ✅ Assign
    db.execute(doctor_patient.insert().values(
        doctor_id=doctor_id,
        patient_id=patient_id
    ))
    db.commit()

    return {"message": "Patient assigned to doctor"}

@router.get("/{doctor_id}/patients")
def get_doctor_patients(doctor_id: int, db: Session = Depends(get_db)):
    patients = db.query(Patient).join(doctor_patient).filter(
        doctor_patient.c.doctor_id == doctor_id
    ).all()

    return patients    


@router.put("/{doctor_id}/restore")
def restore_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # ✅ Only admin
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    # 🔍 Find doctor (including inactive)
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ❗ Check already active
    if doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor already active")

    # ✅ Restore
    doctor.is_active = True
    db.commit()

    return {"message": "Doctor restored successfully"}

