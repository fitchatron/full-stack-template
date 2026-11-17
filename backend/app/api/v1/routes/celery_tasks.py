from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.schemas.role import (
    RoleSchema,
    RoleSchemaPaginated,
    RoleSchemaPATCHRequest,
    RoleSchemaPOSTRequest,
    RoleSchemaPUTRequest,
)
from app.schemas.user import UserResponseSchema
from app.services.celery_task import CeleryTaskService

router = APIRouter(prefix="/celery-tasks", tags=["Celery Tasks"])


@router.get(
    "{task_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get_all"],
)
def get_all_roles(
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=None)),
    ],
    task_id: str = Path(),
) -> RoleSchemaPaginated:
    """
    Get a celery worker task by ID.
    """

    return CeleryTaskService().read(task_id=task_id)


"""
TODO: Add a dev route for
from app.tasks import add

result = add.delay(2, 2)
"""
