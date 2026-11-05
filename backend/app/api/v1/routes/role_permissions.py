from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.schemas.permission import PermissionSchemaPaginated
from app.schemas.role_permission import (
    RolePermissionSchema,
    RolePermissionSchemaPOSTRequest,
)
from app.schemas.user import UserResponseSchema
from app.services.role_permission import RolePermissionService

router = APIRouter(prefix="/roles", tags=["Role Permissions"])


@router.get(
    "/{role_id}/permissions",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_role_permissions(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.READ__ROLE_PERMISSIONS])
        ),
    ],
    role_id: Annotated[str, Path(description="ID of the target role")],
) -> PermissionSchemaPaginated:
    """
    Get a list of all permissions of a role.
    """
    sort_by = [OrderByCondition(column="permission_id", orientation=OrderOperator.asc_)]

    return RolePermissionService(session).read_all(role_id=role_id, sort_by=sort_by)


@router.post(
    "/{role_id}/permissions",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def create_role_permission(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(
                required_permissions=[AppPermissions.CREATE__ROLE_PERMISSIONS]
            )
        ),
    ],
    role_id: Annotated[str, Path(description="ID of the target role")],
    body: Annotated[
        RolePermissionSchemaPOSTRequest,
        Body(description="Request body for creating the role permission"),
    ],
) -> RolePermissionSchema:
    """
    Create a new role permission
    """

    return RolePermissionService(session).create_role_permission(
        current_user=current_user, role_id=role_id, request_body=body
    )


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_role_permission(
    session: SessionDep,
    role_id: Annotated[str, Path(description="ID of the target role")],
    permission_id: Annotated[
        UUID, Path(description="ID of the permission to be removed from the role")
    ],
    _current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(
                required_permissions=[AppPermissions.DELETE__ROLE_PERMISSIONS]
            )
        ),
    ],
) -> None:
    """
    Delete a role permission by role ID and permission ID.
    """

    return RolePermissionService(session).delete_by_id(
        role_id=role_id, permission_id=permission_id
    )
