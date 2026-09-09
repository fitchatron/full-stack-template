from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import Base, SessionLocal, engine
from cli.seed import DatabaseSeeder

app = typer.Typer()

LOCAL_HOSTS = {"localhost", "127.0.0.1"}


class TestDataMode(StrEnum):
    alembic = "alembic"
    mock = "mock"


def _assert_local_host() -> None:
    host = engine.url.host
    if host not in LOCAL_HOSTS:
        typer.secho(
            f"Refusing to run against host {host!r} -- "
            f"this command only runs against {sorted(LOCAL_HOSTS)}.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


@app.command("seed")
def seed(
    user_count: Annotated[
        int, typer.Option(help="Number of random users to create")
    ] = 20,
):
    """
    Populate the fixed roles/permissions and create random fake users. Local dev only.

    Roles and permissions are fixed (not randomly generated) since app
    authorization logic is written against their names.
    """
    _assert_local_host()

    with SessionLocal() as db:
        roles, users = DatabaseSeeder(db).seed(user_count)
        db.commit()

    typer.secho(
        f"Seeded {len(roles)} roles/permissions and {len(users)} users.",
        fg=typer.colors.GREEN,
    )


@app.command("create-local-db")
def create_local_db(
    mode: Annotated[
        TestDataMode, typer.Option(case_sensitive=False)
    ] = TestDataMode.mock,
    seed_users_count: Annotated[
        int,
        typer.Option(
            "--seed-users",
            help="Number of random users to seed after recreating tables. Pass 0 to skip seeding.",
        ),
    ] = 20,
):
    """
    Drop and recreate all tables from the current models. Local dev only.

    After creating tables directly (bypassing Alembic), we stamp the DB as
    being at Alembic's "head" revision -- otherwise `alembic upgrade head`
    will later try to (re)create tables that already exist and fail.
    """
    _assert_local_host()

    typer.confirm(f"Drop and recreate all tables on {engine.url!r}?", abort=True)

    # drop all tables
    Base.metadata.drop_all(bind=engine)

    if mode == TestDataMode.alembic:
        # run migration scripts
        alembic_main(argv=["--raiseerr", "upgrade", "head"])
    else:
        # create all tables then stamp head
        Base.metadata.create_all(bind=engine)

        alembic_cfg = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
        command.stamp(alembic_cfg, "head")

    typer.secho(
        f"Done: tables recreated via {mode.value!r} mode.", fg=typer.colors.GREEN
    )

    if seed_users_count > 0:
        with SessionLocal() as db:
            roles, users = DatabaseSeeder(db).seed(seed_users_count)
            db.commit()

        typer.secho(
            f"Seeded {len(roles)} roles/permissions and {len(users)} users.",
            fg=typer.colors.GREEN,
        )


if __name__ == "__main__":
    app()
