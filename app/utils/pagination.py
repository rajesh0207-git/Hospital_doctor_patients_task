def paginate(query, page: int, limit: int):
    total = query.count()
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": data
    }