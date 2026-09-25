from enum import StrEnum
from pathlib import Path
from typing import Annotated, Optional

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import Base, SessionLocal, engine
from app.core.config import settings
from app.core.app_permissions import AppPermissions
from subprocess import call, STDOUT

app = typer.Typer()


@app.command("run")
def run_tests(
    path: Annotated[
        Optional[str],
        typer.Argument(
            help="Path to the tests to run.",
        ),
    ] = None,
):
    """
    Run test suite located at the specified path. If no path is provided, runs all tests.

    usage: uv run -m cli.main test run
           uv run -m cli.main test run
    """
    if path:
        output = call(["pytest", path], stderr=STDOUT)
    else:
        output = call(["pytest"], stderr=STDOUT)

    if output != 0:
        raise typer.Exit(code=output)


if __name__ == "__main__":
    app()
