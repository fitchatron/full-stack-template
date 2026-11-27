from abc import ABC, abstractmethod
from typing import cast

from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)
from pydantic import SecretStr

from app.core.config import settings
from app.schemas.email import EmailMessageSchema, SendResult


class EmailService(ABC):
    @abstractmethod
    async def send_email(self, msg: EmailMessageSchema) -> SendResult:
        """Send an email with the given message details"""


class FastApiMailService(EmailService):
    def __init__(self) -> None:
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=settings.USE_CREDENTIALS,
            VALIDATE_CERTS=settings.VALIDATE_CERTS,
        )

        self.fm = FastMail(self.conf)

    @classmethod
    def get_message_type(cls, subtype: str = "html"):
        match subtype:
            case "text":
                return MessageType.plain
            case "html":
                return MessageType.html
            case _:
                return MessageType.plain

    async def send_email(self, msg: EmailMessageSchema) -> SendResult:
        """Send an email with the given message details"""
        try:
            await self.fm.send_message(
                MessageSchema(
                    recipients=cast(list[NameEmail], msg.to),
                    cc=cast(list[NameEmail], msg.cc),
                    bcc=cast(list[NameEmail], msg.bcc),
                    subject=msg.subject,
                    body=msg.body,
                    subtype=self.get_message_type(msg.subtype),
                )
            )

            return SendResult(success=True, message="Email has been sent")

        except Exception as e:
            return SendResult(success=False, message=f"{e}")
