from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import AuthorizeUser, SessionDep
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.schemas.user import (
    UserResponseSchema,
    UserResponseSchemaPaginated,
    UserSchemaPATCHRequest,
    UserSchemaPUTRequest,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_all_users(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__USERS])),
    ],
) -> UserResponseSchemaPaginated:
    """
    Get a list of all users.
    """
    sort_by = [OrderByCondition(column="user_id", orientation=OrderOperator.asc_)]
    return UserService(session).read_all(sort_by=sort_by)


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_user_by_id(
    session: SessionDep,
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__USERS])),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user")],
) -> UserResponseSchema:
    """
    Get a user by ID.
    """

    return UserService(session).read_by_id(user_id=user_id)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["put"],
)
def update_user_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__USERS])),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user to be updated")],
    body: Annotated[
        UserSchemaPUTRequest, Body(description="Request body for updating the user")
    ],
) -> UserResponseSchema:
    """
    Update a user by ID.
    """

    return UserService(session).update_by_id(
        current_user=current_user, user_id=user_id, request_body=body
    )


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["patch"],
)
def patch_user_by_id(
    session: SessionDep,
    current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__USERS])),
    ],
    user_id: Annotated[UUID, Path(description="ID of the target user to be patched")],
    body: Annotated[
        UserSchemaPATCHRequest, Body(description="Request body for patching the user")
    ],
) -> UserResponseSchema:
    """
    Patch a user by ID.
    """

    return UserService(session).patch_by_id(
        current_user=current_user, user_id=user_id, request_body=body
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_user_by_id(
    session: SessionDep,
    user_id: Annotated[UUID, Path(description="ID of the target user to be deleted")],
    _current_user: Annotated[
        UserResponseSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.DELETE__USERS])),
    ],
) -> None:
    """
    Delete a user by ID.
    """

    return UserService(session).delete_by_id(user_id=user_id)
