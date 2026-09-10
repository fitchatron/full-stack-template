from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager
from typing import Type
from app.repositories.generic import CRUDRepository
from app.models.model import User
from app.schemas.user import UserSchema


class UserRepository(CRUDRepository[User, UserSchema]):
    """
    User repository
    """

    def __init__(self, session: Session, model: Type[User]) -> None:
        """
        User Repository constructor
        """
        super().__init__(session, model)
