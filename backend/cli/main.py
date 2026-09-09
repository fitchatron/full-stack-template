import typer

from cli import db, test

app = typer.Typer()

# cli to manage backend dev scripts
app.add_typer(db.app, name="db", help="Subcommands to manage database")
app.add_typer(test.app, name="test", help="Subcommands to run tests")


if __name__ == "__main__":
    app()
