from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.api.deps import SessionDep
from app.schemas.api import HTTPExceptionSchema

health = APIRouter(prefix="/health", tags=["health"])


@health.get(
    "",
    status_code=status.HTTP_200_OK,
)
def health_check():
    return {"status": "ok"}


@health.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    responses={
        503: {"model": HTTPExceptionSchema},
    },
)
def readiness_check(
    session: SessionDep,
):
    try:
        time = session.execute(text("SELECT NOW();")).first()
        if time is None:
            raise Exception("Database is not ready")

        return {"status": "ok", "timestamp": time[0]}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        )
