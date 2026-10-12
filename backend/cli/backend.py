from subprocess import STDOUT, call
from typing import Annotated, Literal

import typer

app = typer.Typer()


@app.command("run")
def run(
    mode: Annotated[
        Literal["dev", "prod"],
        typer.Argument(
            help="The mode in which to run the application (dev or prod).",
        ),
    ] = "dev",
):
    """
    Run the FastAPI application in the specified mode (dev or prod).

    usage: uv run -m cli.main backend run
           uv run -m cli.main backend run dev | prod
    """

    args = [
        "fastapi",
        "dev" if mode == "dev" else "run",
    ]
    output = call(
        args,
        stderr=STDOUT,
    )

    if output != 0:
        raise typer.Exit(code=output)


if __name__ == "__main__":
    app()
