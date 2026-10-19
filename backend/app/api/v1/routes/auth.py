from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthorizeUser, SessionDep
from app.core.config import settings
from app.schemas.auth import Token
from app.schemas.user import RegisterUserPOSTRequest, UserResponseSchema
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def register(
    session: SessionDep,
    request: RegisterUserPOSTRequest = Body(),
) -> Token:
    """
    Register a new user and return an OAuth2 compatible token for future requests
    """

    return AuthService(session).register(request=request)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    Authenticate user and return an OAuth2 compatible token for future requests
    """

    return AuthService(session).authenticate(
        email=form_data.username, password=form_data.password
    )


if settings.FASTAPI_ENV == "development":

    @router.post(
        "/test-token",
        responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
    )
    def test_token(
        current_user: Annotated[
            UserResponseSchema,
            Depends(AuthorizeUser(required_permissions=[])),
        ],
    ) -> UserResponseSchema:
        """
        Test access token
        """
        return current_user


@router.post(
    "/password-recovery/{email}",
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def recover_password(session: SessionDep, email: str):
    """
    Password Recovery
    """
    raise NotImplementedError("Method not implemented")


@router.post(
    "/reset-password/",
    responses=settings.HTTP_EXCEPTION_RESPONSES_SET["post"],
)
def reset_password(session: SessionDep):
    """
    Password Recovery
    """
    raise NotImplementedError("Method not implemented")
