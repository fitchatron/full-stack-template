import typer
from cli import db, test, setup

app = typer.Typer()

# cli to manage backend dev scripts
app.add_typer(db.app, name="db", help="Subcommands to manage database")
app.add_typer(test.app, name="test", help="Subcommands to run tests")
app.add_typer(setup.app, name="setup", help="Subcommands to set-up the env")


if __name__ == "__main__":
    app()
