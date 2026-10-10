from typing import Annotated

import typer

from cli.types import TestDataMode
from seeding import DatabaseManager, DatabaseSeeder, NonLocalDatabaseError, SeedPlan

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
        manager = DatabaseManager.from_settings(mode)
    except NonLocalDatabaseError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        result = manager.reset(
            seed=lambda session: DatabaseSeeder(session).seed(
                SeedPlan(include_mock_data=mock_data)
            )
        )
        assert result is not None

        typer.secho("SUCCESS ✅", fg=typer.colors.GREEN)
        message = f"Done: tables recreated via {mode.value!r} mode.\nSeeded the following with mock_data={mock_data}\nroles: {len(result.roles)}\npermissions: {len(result.permissions)}\nusers: {len(result.users)}"
        typer.secho(message, fg=typer.colors.YELLOW)
        typer.secho(
            f"Admin user email: {result.admin_user.email}"
            if result.admin_user
            else "No admin user created",
            fg=typer.colors.CYAN,
        )
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    finally:
        manager.dispose()


if __name__ == "__main__":
    app()
