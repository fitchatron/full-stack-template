import pytest
from datetime import datetime
from app.core.config import settings
from app.core.app_permissions import AppPermissions
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from app.core.db import engine
from app.models.model import User, UserRole, Permission
from seeding.factories import (
    RoleFactory,
    RolePermissionFactory,
    UserFactory,
    UserRoleFactory,
)
from seeding.plan import SeedPlan
from seeding.seeder import DatabaseSeeder


@pytest.fixture(scope="session", autouse=True)
def _core_data():
    """Reset the schema and seed required reference data once for the whole run."""
    with Session(engine) as session:
        DatabaseSeeder(
            session=session,
        ).seed(plan=SeedPlan(include_mock_data=False))


@pytest.fixture
def db_session():
    """
    Fixture to create SQLAlchemy session for talking to the database directly
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_role_fixture(db_session):
    """
    Fixture for granting a user a role, looked up by name

    usage: user_role_factory(user, settings.ROLES.ADMIN)
    """

    def _create(
        user: User,
        permissions: list[AppPermissions],
        role_name: str | None = None,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> UserRole:

        # get permissions
        filter = [permission.to_filter_clause() for permission in permissions]
        db_permissions = db_session.scalars(
            select(Permission).where(or_(*filter))
        ).all()
        if len(db_permissions) != len(permissions):
            raise ValueError(
                "No permissions found matching the provided AppPermissions"
            )

        # create role with those permissions
        role = RoleFactory.build(name=role_name)
        role_permissions = RolePermissionFactory.build_batch(
            size=len(db_permissions),
            role=role,
            permission=db_permissions,
        )

        # create user role with the role
        user_role = UserRoleFactory.build(
            user=user,
            role=role,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        db_session.add_all(role_permissions)
        db_session.flush()

        return user_role

    return _create


@pytest.fixture
def act_as_user(db_session):
    """
    Fixture to act as a user in tests.
    """

    user = UserFactory.build(
        email=settings.EMAIL_TEST_USER, password=settings.EMAIL_TEST_USER_PASSWORD
    )
    db_session.add(user)
    db_session.flush()
    yield user


# TODO: start tests from cli
@pytest.fixture
def act_as_admin(act_as_user, user_role_fixture):
    """
    Fixture to act as an admin user in tests.
    """
    user_role_fixture(act_as_user, permissions=[AppPermissions.ASTERISK__ASTERISK])
    return act_as_user
