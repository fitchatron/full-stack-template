from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.schemas.user import UserResponseSchema
from app.schemas.user_role import (
    UserRoleSchema,
    UserRoleSchemaPaginated,
    UserRoleSchemaPATCHRequest,
    UserRoleSchemaPOSTRequest,
)
from app.services.user_role import UserRoleService

router = APIRouter(prefix="/users", tags=["User Roles"])


@router.get(
    "/{user_id}/roles",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_all_user_roles(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__USER_ROLES])),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user")],
) -> UserRoleSchemaPaginated:
    """
    Get a list of all roles for user.
    """
    sort_by = [OrderByCondition(column="user_role_id", orientation=OrderOperator.asc_)]

    return UserRoleService(session).read_all(user_id=user_id, sort_by=sort_by)


@router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def create_user_role(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.CREATE__USER_ROLES])
        ),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user")],
    body: Annotated[
        UserRoleSchemaPOSTRequest,
        Body(description="Request body for creating the user role"),
    ],
) -> UserRoleSchema:
    """
    Create a new user role.
    """

    return UserRoleService(session).create_user_role(
        current_user=current_user, user_id=user_id, request_body=body
    )


@router.patch(
    "/{user_id}/roles/{user_role_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["patch"],
)
def patch_user_role(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.UPDATE__USER_ROLES])
        ),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user")],
    user_role_id: Annotated[
        UUID, Path(description="ID of the target user role to be patched")
    ],
    body: Annotated[
        UserRoleSchemaPATCHRequest,
        Body(description="Request body for patching the user role"),
    ],
) -> UserRoleSchema:
    """
    Patch the dates of a user role. Active user roles can only change their end date.
    """

    return UserRoleService(session).patch_by_id(
        current_user=current_user,
        user_id=user_id,
        user_role_id=user_role_id,
        request_body=body,
    )


@router.delete(
    "/{user_id}/roles/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_user_role(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.DELETE__USER_ROLES])
        ),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user")],
    user_role_id: Annotated[
        UUID, Path(description="ID of the user role to be revoked")
    ],
) -> None:
    """
    Revoke a role from a user. Active user roles end now and are kept for audit,
    scheduled user roles are deleted.
    """

    return UserRoleService(session).delete_by_id(
        current_user=current_user, user_id=user_id, user_role_id=user_role_id
    )
