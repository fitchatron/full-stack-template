from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, NameEmail, SecretStr

from app.core.config import settings

router = APIRouter(prefix="/email", tags=["Email"])


class EmailSchema(BaseModel):
    email: list[NameEmail]


conf = ConnectionConfig(
    MAIL_USERNAME="",
    MAIL_PASSWORD=SecretStr(""),
    MAIL_FROM="test@email.com",
    MAIL_PORT=1025,
    MAIL_SERVER="localhost",
    MAIL_FROM_NAME="Test Email",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False,
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
async def sned_email(
    body: Annotated[
        EmailSchema,
        Body(description="List of email addresses to send to"),
    ],
) -> dict[str, str]:
    html = """<p>Hi this test mail, thanks for using Fastapi-mail</p> """

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=body.email,
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "email has been sent"}
