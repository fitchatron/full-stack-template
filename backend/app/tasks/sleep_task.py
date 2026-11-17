import logging
from time import sleep

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="sleep_task")
def sleep_task(sleeping_time_in_seconds: int, success: bool):
    try:
        sleep(sleeping_time_in_seconds)
        if not success:
            raise Exception("Task failed intentionally")
        return "Task completed successfully"
    except Exception as exception:
        logger.exception(f"Error in sleep_task: {exception}")
        raise exception
