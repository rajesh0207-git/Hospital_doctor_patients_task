from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

def handle_db_exception(e):
    if isinstance(e, IntegrityError):
        return HTTPException(status_code=400, detail="Duplicate or invalid data")

    return HTTPException(status_code=500, detail="Database error")