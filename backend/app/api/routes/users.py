from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import AuthorizeUser
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.schemas.user import UserResponseSchema, UserSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_all_users(
    current_user: Annotated[
        UserSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__USERS])),
    ],
) -> list[UserResponseSchema]:
    """
    Get a list of all users.
    """

    raise NotImplementedError("Method not implemented")


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["get"],
)
def get_user_by_id(
    user_id: UUID,
    current_user: Annotated[
        UserSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.READ__USERS])),
    ],
) -> UserResponseSchema:
    """
    Get a user by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["put"],
)
def update_user_by_id(
    user_id: UUID,
    current_user: Annotated[
        UserSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__USERS])),
    ],
) -> UserResponseSchema:
    """
    Update a user by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["patch"],
)
def patch_user_by_id(
    user_id: UUID,
    current_user: Annotated[
        UserSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.UPDATE__USERS])),
    ],
) -> None:
    """
    Patch a user by ID.
    """

    raise NotImplementedError("Method not implemented")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["delete"],
)
def delete_user_by_id(
    user_id: UUID,
    current_user: Annotated[
        UserSchema,
        Depends(AuthorizeUser(required_permissions=[AppPermissions.DELETE__USERS])),
    ],
) -> None:
    """
    Delete a user by ID.
    """

    raise NotImplementedError("Method not implemented")
