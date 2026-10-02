import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.model import Permission, Role, User, UserRole
from seeding import DatabaseManager, DatabaseSeeder, SeedPlan
from seeding.factories import (
    RoleFactory,
    RolePermissionFactory,
    UserFactory,
    UserRoleFactory,
)


@pytest.fixture(scope="session", autouse=True)
def db_manager():
    """
    Recreate test_{POSTGRES_DB} and seed required reference data once for the
    whole run.
    """
    manager = DatabaseManager.for_tests()
    manager.reset(
        seed=lambda session: DatabaseSeeder(session).seed(
            SeedPlan(include_mock_data=False)
        ),
        recreate_db=True,
    )
    yield manager
    manager.dispose()


@pytest.fixture
def db_session(db_manager):
    """
    Fixture to create SQLAlchemy session for talking to the database directly.
    Everything a test does (including commits) is rolled back afterwards.
    """
    connection = db_manager.engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    Fixture to setup client. Requests share the test's db_session, so they hit
    the test database and are rolled back with it.
    """

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


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
def act_as_user(db_session, request):
    """
    Fixture to act as a user in tests.
    """

    slug = re.sub(r"[^a-z0-9]+", "-", request.node.name.lower()).strip("-")
    user = UserFactory.build(
        email=f"{slug}@test.example.com", password=settings.EMAIL_TEST_USER_PASSWORD
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
