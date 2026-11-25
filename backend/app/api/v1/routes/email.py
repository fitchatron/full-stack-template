from typing import Annotated

from fastapi import APIRouter, Body, status

from app.api.deps import SessionDep
from app.core.config import settings
from app.schemas.email import EmailTemplateMessageSchema
from app.services.email import FastApiMailService

router = APIRouter(prefix="/email", tags=["Email"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
async def send_email(
    session: SessionDep,
    body: Annotated[
        EmailTemplateMessageSchema,
        Body(description="List of email addresses to send to"),
    ],
) -> dict[str, str]:

    service = FastApiMailService(session=session)
    # result = await service.send_email(body)
    result = await service.send_email_template(body)
    return {"message": f"{result.message}"}
