from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser
from app.core.config import settings
from app.schemas.celery_task import (
    AddTaskPOSTRequest,
    CeleryTaskSchema,
    CeleryTaskSchemaPOSTRequest,
    SleepTaskPOSTRequest,
)
from app.schemas.user import UserResponseSchema
from app.services.celery_task import CeleryTaskService

router = APIRouter(prefix="/celery-tasks", tags=["Celery Tasks"])


@router.get(
    "{task_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get_all"],
)
def get_task_by_id(
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=None)),
    ],
    task_id: str = Path(),
) -> CeleryTaskSchema:
    """
    Get a celery worker task by ID.
    """

    return CeleryTaskService().read(task_id=task_id)


if settings.FASTAPI_ENV == "development":

    @router.post(
        "sandbox/sleep",
        status_code=status.HTTP_201_CREATED,
        responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
    )
    async def sleep(
        _current_user: Annotated[
            UserResponseSchema,
            Depends(AuthorizeUser(required_permissions=None)),
        ],
        request: SleepTaskPOSTRequest = Body(),
    ) -> CeleryTaskSchemaPOSTRequest:
        """
        Simulate a sleep operation to test asynchronous behaviour.
        This endpoint is used for testing purposes and does not perform any real operation.
        """

        return CeleryTaskService().trigger_sleep_task(request=request)

    @router.post(
        "sandbox/add",
        status_code=status.HTTP_201_CREATED,
        responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
    )
    async def add(
        _current_user: Annotated[
            UserResponseSchema,
            Depends(AuthorizeUser(required_permissions=None)),
        ],
        request: AddTaskPOSTRequest = Body(),
    ) -> CeleryTaskSchemaPOSTRequest:
        """
        Simulate an add operation to test asynchronous behaviour.
        This endpoint is used for testing purposes and does not perform any real operation.
        """

        return CeleryTaskService().trigger_add_task(request=request)
