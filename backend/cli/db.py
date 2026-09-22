from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import SessionLocal, engine
from cli.types import TestDataMode
from seeding import DatabaseSeeder, SeedPlan

app = typer.Typer()


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
        with SessionLocal() as session:
            seeder = DatabaseSeeder(session=session, mode=mode)

            if not seeder.is_local_host():
                typer.secho(
                    f"Refusing to run against host {engine.url.host!r} -- "
                    f"this command only runs against a local host.",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(code=1)

            result = seeder.seed(SeedPlan(include_mock_data=mock_data))

            typer.secho("SUCCESS ✅", fg=typer.colors.GREEN)
            message = f"Done: tables recreated via {mode.value!r} mode.\nSeeded the following with mock_data={mock_data}\nroles: {len(result.roles)}\npermissions: {len(result.permissions)}\nusers: {len(result.users)}"
            typer.secho(message, fg=typer.colors.YELLOW)
            typer.secho(
                f"Admin user email: {result.admin_user.email}", fg=typer.colors.CYAN
            )
    except typer.Exit:
        raise
    except SystemExit:
        raise
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
