from sqlalchemy.orm import Session


def get_or_create[T](
    db: Session, model: type[T], defaults: dict | None = None, **lookup
) -> tuple[T, bool]:
    """
    Idempotent fetch-or-insert by exact-match `lookup` kwargs. Flushes
    immediately so the returned instance has its PK populated.

    Returns (instance, created).
    """
    instance = db.query(model).filter_by(**lookup).one_or_none()
    if instance is not None:
        return instance, False

    instance = model(**{**lookup, **(defaults or {})})
    db.add(instance)
    db.flush()
    return instance, True
