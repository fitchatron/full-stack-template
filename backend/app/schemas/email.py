from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchemaModel


class Attachment(BaseSchemaModel):
    filename: str
    content: bytes
    content_type: str


class EmailMessageSchema(BaseSchemaModel):
    """
    Schema for an email message to send
    """

    to: list[str] = Field(default=[], description="The TO recipients in the email")
    cc: list[str] = Field(default=[], description="The CC recipients in the email")
    bcc: list[str] = Field(default=[], description="The BCC recipients in the email")
    subject: str = Field(
        description="The email subject", examples=["This is a test email"]
    )
    body: str = Field(
        description="The email body",
        examples=["<p>Hi this test mail, thanks for using Fastapi-mail</p>"],
    )
    subtype: Literal["text", "html"] = Field(
        default="html", description="The message embed type"
    )
    attachments: list[Attachment] = Field(default=[], description="Email attachments")


class SendResult(BaseSchemaModel):
    """
    Schema for an email message to send
    """

    message_id: int | None = Field(
        default=None, description="The TO recipients in the email"
    )
    success: bool = Field(
        description="Whether the message was successfully sent or not"
    )
    message: str | None = Field(
        default=None, description="The response message to send"
    )
