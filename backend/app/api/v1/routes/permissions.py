from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.schemas.permission import (
    PermissionSchema,
    PermissionSchemaPaginated,
    PermissionSchemaPATCHRequest,
    PermissionSchemaPOSTRequest,
    PermissionSchemaPUTRequest,
)
from app.schemas.user import UserResponseSchema
from app.services.permission import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get_all"],
)
def get_all_permissions(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__PERMISSIONS])),
    ],
) -> PermissionSchemaPaginated:
    """
    Get a list of all permissions.
    """
    sort_by = [OrderByCondition(column="permission_id", orientation=OrderOperator.asc_)]

    return PermissionService(session).read_all(sort_by=sort_by)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def create_permission(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.CREATE__PERMISSIONS])
        ),
    ],
    body: Annotated[
        PermissionSchemaPOSTRequest,
        Body(description="Request body for creating the permission"),
    ],
) -> PermissionSchema:
    """
    Create a new permission
    """

    return PermissionService(session).create_permission(
        current_user=current_user, request_body=body
    )


@router.get(
    "/{permission_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_permission_by_id(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__PERMISSIONS])),
    ],
    permission_id: Annotated[UUID, Path(description="ID of the target permission")],
) -> PermissionSchema:
    """
    Get a permission by ID.
    """

    return PermissionService(session).read_by_id(permission_id=permission_id)


@router.put(
    "/{permission_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["put"],
)
def update_permission_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.UPDATE__PERMISSIONS])
        ),
    ],
    permission_id: Annotated[
        UUID, Path(description="ID of the target permission to be updated")
    ],
    body: Annotated[
        PermissionSchemaPUTRequest,
        Body(description="Request body for updating the permission"),
    ],
) -> PermissionSchema:
    """
    Update a permission by ID.
    """

    return PermissionService(session).update_by_id(
        current_user=current_user, permission_id=permission_id, request_body=body
    )


@router.patch(
    "/{permission_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["patch"],
)
def patch_permission_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.UPDATE__PERMISSIONS])
        ),
    ],
    permission_id: Annotated[
        UUID, Path(description="ID of the target permission to be patched")
    ],
    body: Annotated[
        PermissionSchemaPATCHRequest,
        Body(description="Request body for patching the permission"),
    ],
) -> PermissionSchema:
    """
    Patch a permission by ID.
    """

    return PermissionService(session).patch_by_id(
        current_user=current_user, permission_id=permission_id, request_body=body
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_permission_by_id(
    session: SessionDep,
    permission_id: Annotated[
        UUID, Path(description="ID of the target permission to be deleted")
    ],
    _current_user: Annotated[
        UserResponseSchema,
        Depends(
            AuthorizeUser(required_permissions=[AppPermissions.DELETE__PERMISSIONS])
        ),
    ],
) -> None:
    """
    Delete a permission by ID.
    """

    return PermissionService(session).delete_by_id(permission_id=permission_id)
