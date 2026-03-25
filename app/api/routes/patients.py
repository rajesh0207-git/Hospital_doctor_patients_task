from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.patient import Patient
from fastapi import HTTPException
from fastapi import Query
from app.utils.pagination import paginate
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import handle_db_exception
from app.models.doctor import Doctor

router = APIRouter(prefix="/patients", tags=["Patients"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/")
def create_patient(data: dict, db: Session = Depends(get_db)):

    # ✅ Check doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == data.get("doctor_id")).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ✅ Check doctor active
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="Doctor is inactive")

    try:
        # ✅ CREATE PATIENT (THIS WAS MISSING)
        patient = Patient(**data)

        db.add(patient)        # ✅ add patient
        db.commit()
        db.refresh(patient)

        return patient         # ✅ return patient

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    age_gt: int = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Patient).filter(Patient.is_deleted == False)

    # ✅ Filtering
    if age_gt is not None:
        query = query.filter(Patient.age > age_gt)

    # ✅ Total count
    total = query.count()

    # ✅ Pagination
    offset = (page - 1) * limit
    patients = query.offset(offset).limit(limit).all()

    return paginate(query, page, limit)

@router.put("/{patient_id}")
def update_patient(patient_id: int, data: dict, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Patient not found")

    for key, value in data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)

    return patient

@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_deleted = True
    db.commit()

    return {"message": "Patient Soft deleted successfully"}

@router.put("/patients/{id}/restore")
def restore_patient(id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Not found")

    patient.is_deleted = False
    db.commit()

    return {"message": "Patient restored"}

