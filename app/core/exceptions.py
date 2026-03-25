from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

def handle_db_exception(e: Exception):
    if isinstance(e, IntegrityError):
        return HTTPException(
            status_code=400,
            detail="Doctor with this email already exists"
        )
    
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )