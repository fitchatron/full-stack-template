from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import Base, SessionLocal, engine
from seeding import DatabaseSeeder, SeedPlan

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


@app.command("create-local-db")
def create_local_db(
    mode: Annotated[
        TestDataMode, typer.Option(case_sensitive=False)
    ] = TestDataMode.mock,
    mock_data: Annotated[
        bool,
        typer.Option(
            "--mock-data/--no-mock-data",
            help="Also seed random mock users on top of the required core data.",
        ),
    ] = False,
):
    """
    Drop and recreate all tables, then seed the required core app data
    (roles, permissions, first superuser) and optionally random mock data.
    Local dev only -- always resets the schema, no confirmation prompt.

    usage: uv run -m cli.main db create-local-db --mock-data/--no-mock-data
    """

    try:
        _assert_local_host()

        Base.metadata.drop_all(bind=engine)

        if mode == TestDataMode.alembic:
            alembic_main(argv=["--raiseerr", "upgrade", "head"])
        else:
            Base.metadata.create_all(bind=engine)

            alembic_cfg = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
            command.stamp(alembic_cfg, "head")

        typer.secho("SUCCESS ✅", fg=typer.colors.GREEN)

        with SessionLocal() as session:
            result = DatabaseSeeder(session).seed(
                SeedPlan(include_mock_data=mock_data)
            )

            message = f"Done: tables recreated via {mode.value!r} mode.\nSeeded the following with mock_data={mock_data}\nroles: {len(result.roles)}\npermissions: {len(result.permissions)}\nusers: {len(result.users)}"
            typer.secho(message, fg=typer.colors.YELLOW)
            typer.secho(
                f"Admin user email: {result.admin_user.email}", fg=typer.colors.CYAN
            )
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
