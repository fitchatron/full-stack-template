from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.email import EmailTemplateMessageSchema, SendResult
from app.schemas.user import UserResponseSchema
from app.services.email_message import EmailMessageService

router = APIRouter(prefix="/email", tags=["Email"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def send_email_template(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.CREATE__EMAIL])),
    ],
    body: Annotated[
        EmailTemplateMessageSchema,
        Body(description="List of email addresses to send to"),
    ],
) -> SendResult:
    """
    Sends an email by template name. Email will be queued and processed by a celery broker
    """
    service = EmailMessageService(session=session)
    result = service.send_email_template_by_name(msg=body)

    return result
