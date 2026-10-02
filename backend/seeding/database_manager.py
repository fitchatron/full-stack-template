from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Self

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, Connection, NullPool, create_engine, make_url, text
from sqlalchemy.orm import Session

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.config import settings
from app.core.db import Base
from cli.types import TestDataMode

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


class NonLocalDatabaseError(RuntimeError):
    pass


class DatabaseManager:
    """
    Owns the lifecycle of one local database: creating/dropping the database
    itself and its tables. Knows nothing about the data that goes in -- pass a
    `seed` callable to `reset` for that.
    """

    LOCAL_HOSTS = {"localhost", "127.0.0.1"}
    MAINTENANCE_DATABASE = "postgres"

    def __init__(self, url: str | URL, mode: TestDataMode = TestDataMode.mock) -> None:
        self.url = make_url(url)
        self.mode = mode

        if not self.is_local_host():
            raise NonLocalDatabaseError(
                f"Refusing to run against host {self.url.host!r} -- "
                f"this command only runs against a local host."
            )

        self.engine = create_engine(self.url, pool_pre_ping=True)

    @classmethod
    def from_settings(cls, mode: TestDataMode = TestDataMode.mock) -> Self:
        return cls(settings.DATABASE_URL, mode)

    @classmethod
    def for_tests(cls, mode: TestDataMode = TestDataMode.mock) -> Self:
        url = make_url(settings.DATABASE_URL)
        return cls(url.set(database=f"test_{url.database}"), mode)

    @property
    def database_name(self) -> str:
        assert self.url.database is not None
        return self.url.database

    def is_local_host(self) -> bool:
        return self.url.host in self.LOCAL_HOSTS

    # MARK: database
    @contextmanager
    def _maintenance_connection(self) -> Generator[Connection]:
        # CREATE/DROP DATABASE can't run inside a transaction or while connected
        # to the target database, so go through the maintenance db in autocommit
        engine = create_engine(
            self.url.set(database=self.MAINTENANCE_DATABASE),
            isolation_level="AUTOCOMMIT",
            poolclass=NullPool,
        )
        try:
            with engine.connect() as connection:
                yield connection
        finally:
            engine.dispose()

    def _quoted_database_name(self, connection: Connection) -> str:
        return connection.dialect.identifier_preparer.quote(self.database_name)

    def database_exists(self) -> bool:
        with self._maintenance_connection() as connection:
            return (
                connection.scalar(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"),
                    {"name": self.database_name},
                )
                is not None
            )

    def create_database(self) -> None:
        with self._maintenance_connection() as connection:
            connection.execute(
                text(f"CREATE DATABASE {self._quoted_database_name(connection)}")
            )

    def drop_database(self) -> None:
        # release our own pooled connections; FORCE terminates everyone else's
        self.engine.dispose()
        with self._maintenance_connection() as connection:
            connection.execute(
                text(
                    f"DROP DATABASE IF EXISTS "
                    f"{self._quoted_database_name(connection)} WITH (FORCE)"
                )
            )

    def recreate_database(self) -> None:
        self.drop_database()
        self.create_database()

    # MARK: tables
    def _alembic_config(self, connection: Connection) -> Config:
        alembic_cfg = Config(ALEMBIC_INI)
        # env.py runs against this connection instead of settings.DATABASE_URL
        alembic_cfg.attributes["connection"] = connection
        return alembic_cfg

    def drop_tables(self) -> None:
        with self.engine.begin() as connection:
            Base.metadata.drop_all(bind=connection)
            # otherwise `upgrade head` sees the old revision and does nothing
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))

    def create_tables(self) -> None:
        with self.engine.begin() as connection:
            alembic_cfg = self._alembic_config(connection)
            if self.mode == TestDataMode.alembic:
                command.upgrade(alembic_cfg, "head")
            else:
                Base.metadata.create_all(bind=connection)
                command.stamp(alembic_cfg, "head")

    def recreate_tables(self) -> None:
        self.drop_tables()
        self.create_tables()

    # MARK: composition
    def session(self) -> Session:
        return Session(self.engine)

    def reset[T](
        self,
        seed: Callable[[Session], T] | None = None,
        *,
        recreate_db: bool = False,
    ) -> T | None:
        """
        Bring the database to an empty, current schema, then run `seed` (if
        given) in a fresh session and return its result.
        """
        if recreate_db:
            self.recreate_database()
        elif not self.database_exists():
            self.create_database()

        self.recreate_tables()

        if seed is None:
            return None

        # keep seeded objects readable after the seeder commits and we close
        with Session(self.engine, expire_on_commit=False) as session:
            return seed(session)

    def dispose(self) -> None:
        self.engine.dispose()
