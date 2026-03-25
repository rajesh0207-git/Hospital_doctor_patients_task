from pydantic import BaseModel, Field, constr

class PatientCreate(BaseModel):
    name: str
    age: int = Field(gt=0)
    phone: constr(regex="^[0-9]{10}$")  # ✅ validation only
    doctor_id: int