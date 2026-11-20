from typing import Annotated

from fastapi import APIRouter, Body, status

from app.core.config import settings
from app.schemas.email import EmailMessageSchema
from app.services.email import FastApiMailService

router = APIRouter(prefix="/email", tags=["Email"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
async def sned_email(
    body: Annotated[
        EmailMessageSchema,
        Body(description="List of email addresses to send to"),
    ],
) -> dict[str, str]:

    service = FastApiMailService()
    result = await service.send_email(body)
    return {"message": f"{result.message}"}
