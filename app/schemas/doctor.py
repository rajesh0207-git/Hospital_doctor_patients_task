from pydantic import BaseModel, EmailStr

class DoctorCreate(BaseModel):
    name: str
    specialization: str
    email: EmailStr   # ✅ validates email format