import asyncio

from app.core.celery import celery_app
from app.schemas.email import EmailMessageSchema
from app.services.email import FastApiMailService


@celery_app.task(name="send_email")
def send_email(msg: str) -> dict:
    """
    Send an email from a worker. `msg` is an EmailMessageSchema serialised
    with `model_dump_json()` so it can travel through the broker.
    """
    message = EmailMessageSchema.model_validate_json(msg)
    email_service = FastApiMailService()
    result = asyncio.run(email_service.send_email(msg=message))
    return result.model_dump()
