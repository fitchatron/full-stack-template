import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager
from typing import Type
from app.repositories.generic import CRUDRepository
from app.models.model import User
from app.schemas.user import UserSchema, RegisterUserSchema


class UserRepository(CRUDRepository[User, UserSchema]):
    """
    User repository
    """

    def __init__(self, session: Session, model: Type[User]) -> None:
        """
        User Repository constructor
        """

        super().__init__(session, model)

    def read_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Read user by user_id
        """

        sql = select(self.model).where(self.model.user_id == user_id)
        result = self.session.scalars(sql).first()
        return result

    def read_user_by_email(self, email: str) -> User | None:
        """
        Read a single user by email
        """

        sql = select(self.model).where(self.model.email == email)
        result = self.session.scalars(sql).first()
        return result

    def create_user(self, user_data: RegisterUserSchema) -> User | None:
        """
        Create a new user with the given values
        """

        new_user = self.model(
            email=user_data.email,
            username=user_data.username,
            given_name=user_data.given_name,
            family_name=user_data.family_name,
            hashed_password=user_data.hashed_password.get_secret_value(),
            salt=user_data.salt,
        )
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user
