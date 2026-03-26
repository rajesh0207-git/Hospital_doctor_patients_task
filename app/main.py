from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.api.routes import auth, doctors, patients, billings
from app.api.routes import appointments
from app.api.routes.billings import router as billing_router
from app.api.routes.billings import report_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(billings.router)
app.include_router(billing_router)
app.include_router(report_router)