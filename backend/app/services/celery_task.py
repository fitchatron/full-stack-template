from celery.result import AsyncResult

from app.core.celery import celery_app
from app.schemas.celery_task import CeleryTaskSchema
from app.utils.exception import NotFoundError


class CeleryTaskService:
    """
    Service for asynchronous operations.
    """

    def read(self, task_id: str) -> CeleryTaskSchema:
        """
        Function to read the status of a task using its ID.
        """

        task_result = AsyncResult(task_id, app=celery_app)

        if not task_result:
            raise NotFoundError("Task not found")

        result = {
            "task_id": task_result.id,
            "task_status": task_result.status,
            "task_result": task_result.result,
        }
        return CeleryTaskSchema.model_validate(result)
