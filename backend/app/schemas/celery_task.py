from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchemaModel


class CeleryTaskSchema(BaseSchemaModel):
    """
    Base celery task schema.
    This schema is used to dump the task status and result from Celery.
    """

    task_id: str = Field(description="Task ID")
    task_status: str = Field(description="Task status")
    task_result: Any | None = Field(description="Task result")


class CeleryTaskSchemaPOSTRequest(BaseSchemaModel):
    """
    Celery Task schema for POST request to create a task.
    Use this schema to return the task ID after creating a task.
    This should be the schema that is used in all ascynchronous API.
    """

    task_id: str = Field(description="Task ID")


class SleepTaskPOSTRequest(BaseSchemaModel):
    """
    Schema for a POST request triggering a sleep_task celery task
    """

    sleeping_time_in_seconds: int = Field(
        default=10, description="Time to sleep in seconds"
    )
    success: bool = Field(
        default=True, description="Indicates if the task should succeed"
    )


class AddTaskPOSTRequest(BaseSchemaModel):
    """
    Schema for a POST request triggering an add celery task
    """

    a: int = Field(default=5, description="First integer")
    b: int = Field(default=4, description="Second integer")
