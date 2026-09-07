from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import Base, engine

app = typer.Typer()

LOCAL_HOSTS = {"localhost", "127.0.0.1"}


class TestDataMode(StrEnum):
    alembic = "alembic"
    mock = "mock"


@app.command("create-local-db")
def create_local_db(
    mode: Annotated[
        TestDataMode, typer.Option(case_sensitive=False)
    ] = TestDataMode.mock,
):
    """
    Drop and recreate all tables from the current models. Local dev only.

    After creating tables directly (bypassing Alembic), we stamp the DB as
    being at Alembic's "head" revision -- otherwise `alembic upgrade head`
    will later try to (re)create tables that already exist and fail.
    """
    host = engine.url.host
    if host not in LOCAL_HOSTS:
        typer.secho(
            f"Refusing to reset database at host {host!r} -- "
            f"this command only runs against {sorted(LOCAL_HOSTS)}.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    typer.confirm(
        f"Drop and recreate all tables on {engine.url!r}?", abort=True
    )

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


if __name__ == "__main__":
    app()
