from subprocess import STDOUT, call
from typing import Annotated

import typer

from app import models  # noqa: F401 -- registers all models on Base.metadata

app = typer.Typer()


@app.command("run")
def run_tests(
    path: Annotated[
        str | None,
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
