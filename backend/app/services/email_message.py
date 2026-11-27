from typing import Any

from jinja2 import Template
from jsonschema import validate
from sqlalchemy.orm import Session

from app.models import EmailTemplate
from app.repositories.generic import CRUDRepository
from app.schemas.email import EmailMessageSchema, EmailTemplateMessageSchema, SendResult
from app.services.celery_task import CeleryTaskService
from app.utils.exception import NotFoundError


class EmailMessageService:
    def __init__(self, session: Session) -> None:
        """
        EmailMessageService constructor.
        """
        self.repository = CRUDRepository(session, EmailTemplate)

    def _render_email_template(
        self, *, template_body: str, context: dict[str, Any]
    ) -> str:
        template: Template = Template(template_body)
        html_content = template.render(context)
        return html_content

    def send_email_template_by_name(
        self, msg: EmailTemplateMessageSchema
    ) -> SendResult:
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
                subject = self._render_email_template(
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
                body = self._render_email_template(
                    template_body=email_template.body_template,
                    context=msg.body_context,
                )

            compiled_message = EmailMessageSchema(
                to=msg.to,
                cc=msg.cc,
                bcc=msg.bcc,
                subject=subject,
                body=body,
                attachments=msg.attachments,
                subtype=email_template.subtype,
            )
            result = CeleryTaskService().trigger_send_email(msg=compiled_message)
            return SendResult(
                message_id=result.task_id, success=True, message="Email queued"
            )

        except Exception as e:
            return SendResult(success=False, message=f"{e}")
