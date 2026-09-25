import pytest
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.app_permissions import AppPermissions
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from app.core.db import engine
from app.models.model import Role, User, UserRole, Permission
from app.core.security import create_access_token
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
def grant_permissions(db_session):
    """
    Give a user a new role with exactly the given permissions.

    usage: grant_permissions(user, [AppPermissions.READ__USERS])
    """

    def _grant(
        user: User,
        permissions: list[AppPermissions],
        **user_role_kwargs,
    ) -> UserRole:
        wanted = set(permissions)
        db_permissions = (
            db_session.scalars(
                select(Permission).where(or_(*(p.to_filter_clause() for p in wanted)))
            ).all()
            if wanted
            else []
        )

        if len(db_permissions) != len(wanted):
            found = {(p.action, p.resource) for p in db_permissions}
            missing = [p for p in wanted if p.get_action_resource() not in found]
            raise ValueError(f"Permissions not seeded: {missing}")

        role = RoleFactory.build()
        for permission in db_permissions:
            db_session.add(
                RolePermissionFactory.build(role=role, permission=permission)
            )
        user_role = UserRoleFactory.build(user=user, role=role, **user_role_kwargs)
        db_session.add(user_role)
        db_session.flush()
        return user_role

    return _grant


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


@pytest.fixture
def act_as_admin(act_as_user, db_session):
    admin_role = db_session.get(Role, "admin")
    db_session.add(UserRoleFactory.build(user=act_as_user, role=admin_role))
    db_session.flush()
    return act_as_user


@pytest.fixture
def auth_headers(act_as_user):
    token = create_access_token(str(act_as_user.user_id), timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}
