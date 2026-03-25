def filter_doctors(db, specialization=None, is_active=None):
    query = db.query(Doctor)

    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))

    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)

    return query.all()