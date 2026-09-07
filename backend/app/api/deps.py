from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
from collections.abc import Generator
from app.core.db import SessionLocal


# FastAPI dependency: yields a session per request, closing it afterwards
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]
