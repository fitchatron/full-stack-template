# 6ed0d9a9-eb8b-46ce-bea1-03031a2f02de | 8169cdac-1ca9-40d1-8a00-9647706e38ab
from subprocess import STDOUT, call

import typer

app = typer.Typer()


@app.command("run")
def run():
    """
    Run the celery worker application.
    https://docs.celeryq.dev/en/stable/getting-started/next-steps.html#in-the-background
    usage: uv run -m cli.main celery run
    """

    args = [
        "celery",
        "-A",
        "app.core.celery:celery_app",
        "worker",
        "-l",
        "INFO",
    ]
    output = call(
        args,
        stderr=STDOUT,
    )

    if output != 0:
        raise typer.Exit(code=output)


if __name__ == "__main__":
    app()
