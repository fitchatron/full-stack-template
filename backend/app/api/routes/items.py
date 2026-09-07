import uuid

from fastapi import APIRouter, HTTPException
from app.core.config import settings

router = APIRouter(prefix="/items", tags=["items"])


"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

@router.get("/{item_id}")
def read_item(item_id: int, db: Annotated[Session, Depends(get_db)]):
    ...

"""


@router.get("/{item_id}")
def read_item(item_id: int, q: str | None = None):
    if item_id < 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "q": q, "FASTAPI_ENV": settings.FASTAPI_ENV}
