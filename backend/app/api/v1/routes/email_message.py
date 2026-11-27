from typing import Annotated

from fastapi import APIRouter, Body, status

from app.api.deps import SessionDep
from app.core.config import settings
from app.schemas.email import EmailTemplateMessageSchema
from app.services.email import FastApiMailService
from app.services.email_message import EmailMessageService

router = APIRouter(prefix="/email", tags=["Email"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
async def send_email_template(
    session: SessionDep,
    body: Annotated[
        EmailTemplateMessageSchema,
        Body(description="List of email addresses to send to"),
    ],
) -> dict[str, str]:
    """
    Sends an email by template name
    """
    email_service = FastApiMailService(session=session)
    service = EmailMessageService(session=session, email_service=email_service)
    # result = await service.send_email(body)
    result = await service.send_email_template_by_name(msg=body)
    return {"message": f"{result.message}"}
