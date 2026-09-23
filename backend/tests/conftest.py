import pytest
from sqlalchemy.orm import Session
from app.core.db import engine
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


# TODO: add fixture to act as user
# TODO: start tests from cli
