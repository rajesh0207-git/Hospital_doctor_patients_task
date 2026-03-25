from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.api.routes import auth, doctors, patients
from app.api.routes import appointments

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)