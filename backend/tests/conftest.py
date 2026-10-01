import re
from datetime import timedelta

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, or_, select, text
from sqlalchemy.orm import Session
import urllib.parse
from app.main import app
from app.core.app_permissions import AppPermissions
from app.core.config import settings

# from app.core.db import engine
from app.core.security import create_access_token
from app.models.model import Permission, Role, User, UserRole
from seeding.factories import (
    RoleFactory,
    RolePermissionFactory,
    UserFactory,
    UserRoleFactory,
)
from seeding.plan import SeedPlan
from seeding.seeder import DatabaseSeeder

test_database_engine = create_engine(
    f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/test_{settings.POSTGRES_DB}",
    connect_args={"autocommit": True},
    pool_size=settings.SQLALCHEMY_DATABASE_POOL_SIZE,
    pool_pre_ping=settings.SQLALCHEMY_POOL_PRE_PING,
)


@pytest.fixture(scope="session", autouse=True)
def _core_data():
    """Reset the schema and seed required reference data once for the whole run."""
    with Session(test_database_engine) as session:
        DatabaseSeeder(
            session=session,
        ).seed(plan=SeedPlan(include_mock_data=False))


@pytest.fixture
def db_session():
    """
    Fixture to create SQLAlchemy session for talking to the database directly
    """
    connection = test_database_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def create_database():
    """
    Fixture to create database
    """

    # ensure that the connection string is pointing to local database

    host = test_database_engine.url.host
    if host not in ["localhost", "127.0.0.1"]:
        raise ValueError("Database host is not local")

    database_name = f"test_{settings.POSTGRES_DB}"

    master_database_engine = create_engine(
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/postgres",
        connect_args={"autocommit": True},
        pool_size=settings.SQLALCHEMY_DATABASE_POOL_SIZE,
        pool_pre_ping=settings.SQLALCHEMY_POOL_PRE_PING,
    )

    # create test database
    with master_database_engine.connect() as connection:

        # if database already exists then drop the database
        if (
            connection.scalars(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
            ).first()
            is not None
        ):
            connection.execute(
                text(f"ALTER DATABASE {database_name} WITH ALLOW_CONNECTIONS = false;")
            )
            connection.execute(text(f"DROP DATABASE IF EXISTS {database_name}"))

        # create database
        connection.execute(text(f"CREATE DATABASE {database_name}"))
    yield


@pytest.fixture(scope="session")
def client(create_database):
    """
    Fixture to setup client
    """
    # create test client
    client = TestClient(app)
    yield client


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
