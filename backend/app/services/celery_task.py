from celery.result import AsyncResult

from app.core.celery import celery_app
from app.schemas.celery_task import (
    AddTaskPOSTRequest,
    CeleryTaskSchema,
    CeleryTaskSchemaPOSTRequest,
    SleepTaskPOSTRequest,
)
from app.tasks import sleep_task, add_task
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

    def trigger_sleep_task(
        self, request: SleepTaskPOSTRequest
    ) -> CeleryTaskSchemaPOSTRequest:
        """
        Function to trigger a sleep_task calery task
        """

        task = sleep_task.delay(request.sleeping_time_in_seconds, request.success)
        return CeleryTaskSchemaPOSTRequest.model_validate({"task_id": task.id})

    def trigger_add_task(
        self, request: AddTaskPOSTRequest
    ) -> CeleryTaskSchemaPOSTRequest:
        """
        Function to trigger a sleep_task calery task
        """

        task = add_task.delay(request.a, request.b)
        return CeleryTaskSchemaPOSTRequest.model_validate({"task_id": task.id})
