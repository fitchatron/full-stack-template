# python -c "import secrets; print(secrets.token_urlsafe(32))"
from email import message
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


@app.command("generate_secret_key")
def generate_secret_key(
    save_to_env: Annotated[
        bool,
        typer.Option(
            "--save-to-env/--log-only",
            help="Whether to save the generated secret key to the .env file or print it to the console.",
        ),
    ] = True,
):
    """
    Generate a new secret key for the application.

    By default, the generated secret key will be saved to the .env file.
    Use the --log-only option to print the secret key to the console instead of saving it.

    usage: uv run -m cli.main setup generate_secret_key
           uv run -m cli.main setup generate_secret_key --log-only
    """

    import secrets

    secret_key = secrets.token_urlsafe(32)
    if save_to_env:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        with open(env_file, "a") as f:
            f.write(f"\nSECRET_KEY={secret_key}\n")
        typer.secho("Generated secret key", fg=typer.colors.GREEN)
        typer.secho(f"Secret key saved to {env_file}", fg=typer.colors.YELLOW)
    else:
        print(secret_key)
        typer.secho("Generated secret key", fg=typer.colors.GREEN)
        typer.secho(f"Secret key is {secret_key}", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
