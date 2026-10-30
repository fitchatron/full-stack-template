from typing import Annotated
from uuid import UUID

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

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get_all"],
)
def get_all_roles(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__ROLES])),
    ],
) -> RoleSchemaPaginated:
    """
    Get a list of all roles.
    """
    sort_by = [OrderByCondition(column="role_id", orientation=OrderOperator.asc_)]
    
    raise NotImplementedError("Method not implemented")


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def create_role(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.CREATE__ROLES])),
    ],
    body: Annotated[
        RoleSchemaPOSTRequest, Body(description="Request body for creating the role")
    ],
) -> RoleSchema:
    """
    Create a new role
    """
    
    raise NotImplementedError("Method not implemented")


@router.get(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_role_by_id(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__ROLES])),
    ],
    role_id: Annotated[UUID, Path(description="ID of the target role")],
) -> RoleSchema:
    """
    Get a role by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.put(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["put"],
)
def update_role_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__ROLES])),
    ],
    role_id: Annotated[UUID, Path(description="ID of the target role to be updated")],
    body: Annotated[
        RoleSchemaPUTRequest, Body(description="Request body for updating the role")
    ],
) -> RoleSchema:
    """
    Update a role by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.patch(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["patch"],
)
def patch_role_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__ROLES])),
    ],
    role_id: Annotated[UUID, Path(description="ID of the target role to be patched")],
    body: Annotated[
        RoleSchemaPATCHRequest, Body(description="Request body for patching the role")
    ],
) -> RoleSchema:
    """
    Patch a role by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_role_by_id(
    session: SessionDep,
    role_id: Annotated[UUID, Path(description="ID of the target role to be deleted")],
    current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.DELETE__ROLES])),
    ],
) -> None:
    """
    Delete a role by ID.
    """

    raise NotImplementedError("Method not implemented")
