import typer

from cli import db

app = typer.Typer()

# cli to manage backend dev scripts
app.add_typer(db.app, name="db", help="Subcommands to manage database")


if __name__ == "__main__":
    app()
