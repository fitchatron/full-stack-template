from abc import ABC, abstractmethod
from typing import Any, cast

from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)
from jinja2 import Template
from jsonschema import validate
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.model import EmailTemplate
from app.repositories.generic import CRUDRepository
from app.schemas.email import EmailMessageSchema, EmailTemplateMessageSchema, SendResult
from app.utils.exception import NotFoundError


class EmailService:
    pass


class BaseMailService(ABC):
    @abstractmethod
    async def send_email(self, message: EmailMessageSchema) -> SendResult:
        """Send an email with the given message details"""

    def render_email_template(
        self, *, template_body: str, context: dict[str, Any]
    ) -> str:
        template: Template = Template(template_body)
        html_content = template.render(context)
        return html_content


class FastApiMailService(BaseMailService):
    def __init__(self, session: Session) -> None:
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
        self.repository = CRUDRepository(session, EmailTemplate)

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

    async def send_email_template(self, msg: EmailTemplateMessageSchema) -> SendResult:
        """Send an email with the given message details"""
        try:
            email_template = self.repository.read_single_item(
                filters=(EmailTemplate.template_name == msg.template_name)
            )

            if email_template is None:
                raise NotFoundError("Email template not found")

            """
            validate subject context matches row json schema
            as subject_context_schema could be optional,
            perform the null check before validating schemas
            """

            subject = email_template.subject_template
            if email_template.subject_context_schema is not None:
                validate(
                    instance=msg.subject_context,
                    schema=email_template.subject_context_schema,
                )
                subject = self.render_email_template(
                    template_body=email_template.subject_template,
                    context=msg.subject_context,
                )

            """
            validate body context matches row json schema
            as body_context_schema could be optional,
            perform the null check before validating schemas
            """

            body = email_template.body_template
            if email_template.body_context_schema is not None:
                validate(
                    instance=msg.body_context,
                    schema=email_template.body_context_schema,
                )
                body = self.render_email_template(
                    template_body=email_template.body_template,
                    context=msg.body_context,
                )

            await self.fm.send_message(
                MessageSchema(
                    recipients=cast(list[NameEmail], msg.to),
                    cc=cast(list[NameEmail], msg.cc),
                    bcc=cast(list[NameEmail], msg.bcc),
                    subject=subject,
                    body=body,
                    subtype=self.get_message_type(email_template.subtype),
                )
            )

            return SendResult(success=True, message="Email has been sent")

        except Exception as e:
            return SendResult(success=False, message=f"{e}")
