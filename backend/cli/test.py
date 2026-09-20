from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.config import main as alembic_main

from app import models  # noqa: F401 -- registers all models on Base.metadata
from app.core.db import Base, SessionLocal, engine
from app.core.config import settings
from app.core.app_permissions import AppPermissions

app = typer.Typer()


@app.command("permissions")
def print_permissions():
    """
    Print Permissions
    """

    typer.echo(AppPermissions.ASTERISK__ASTERISK.value)  # *:*
    typer.echo(AppPermissions.CREATE__ASTERISK.value)  # create:*
    typer.echo(AppPermissions.ASTERISK__USERS.value)  # *:users
    typer.echo(AppPermissions.CREATE__USERS.value)  # create:users
    typer.echo(AppPermissions.READ__USERS.value)  # read:users
    typer.echo(AppPermissions.UPDATE__USERS.value)  # update:users
    typer.echo(AppPermissions.DELETE__USERS.value)  # delete:users
    typer.echo(AppPermissions.CREATE__PERMISSIONS.value)  # create:permissions
    typer.echo(AppPermissions.READ__PERMISSIONS.value)  # read:permissions
    typer.echo(AppPermissions.UPDATE__PERMISSIONS.value)  # update:permissions
    typer.echo(AppPermissions.DELETE__PERMISSIONS.value)  # delete:permissions
    typer.echo(AppPermissions.CREATE__ROLES.value)  # create:roles
    typer.echo(AppPermissions.READ__ROLES.value)  # read:roles
    typer.echo(AppPermissions.UPDATE__ROLES.value)  # update:roles
    typer.echo(AppPermissions.DELETE__ROLES.value)  # delete:roles
    typer.echo(AppPermissions.CREATE__ROLE_PERMISSIONS.value)  # create:role_permissions
    typer.echo(AppPermissions.READ__ROLE_PERMISSIONS.value)  # read:role_permissions
    typer.echo(AppPermissions.UPDATE__ROLE_PERMISSIONS.value)  # update:role_permissions
    typer.echo(AppPermissions.DELETE__ROLE_PERMISSIONS.value)  # delete:role_permissions
    typer.echo(AppPermissions.CREATE__USER_ROLES.value)  # create:user_roles
    typer.echo(AppPermissions.READ__USER_ROLES.value)  # read:user_roles
    typer.echo(AppPermissions.UPDATE__USER_ROLES.value)  # update:user_roles
    typer.echo(AppPermissions.DELETE__USER_ROLES.value)  # delete:user_roles

    typer.echo(AppPermissions.ASTERISK__ASTERISK.get_action_resource())  # (*, *)
    typer.echo(AppPermissions.CREATE__ASTERISK.get_action_resource())  # (create, *)
    typer.echo(AppPermissions.ASTERISK__USERS.get_action_resource())  # (*, users)
    typer.echo(AppPermissions.CREATE__USERS.get_action_resource())  # (create, users)
    typer.echo(AppPermissions.READ__USERS.get_action_resource())  # (read, users)
    typer.echo(AppPermissions.UPDATE__USERS.get_action_resource())  # (update, users)
    typer.echo(AppPermissions.DELETE__USERS.get_action_resource())  # (delete, users)
    typer.echo(
        AppPermissions.CREATE__PERMISSIONS.get_action_resource()
    )  # (create, permissions)
    typer.echo(
        AppPermissions.READ__PERMISSIONS.get_action_resource()
    )  # (read, permissions)
    typer.echo(
        AppPermissions.UPDATE__PERMISSIONS.get_action_resource()
    )  # (update, permissions)
    typer.echo(
        AppPermissions.DELETE__PERMISSIONS.get_action_resource()
    )  # (delete, permissions)
    typer.echo(AppPermissions.CREATE__ROLES.get_action_resource())  # (create, roles)
    typer.echo(AppPermissions.READ__ROLES.get_action_resource())  # (read, roles)
    typer.echo(AppPermissions.UPDATE__ROLES.get_action_resource())  # (update, roles)
    typer.echo(AppPermissions.DELETE__ROLES.get_action_resource())  # (delete, roles)
    typer.echo(
        AppPermissions.CREATE__ROLE_PERMISSIONS.get_action_resource()
    )  # (create, role_permissions)
    typer.echo(
        AppPermissions.READ__ROLE_PERMISSIONS.get_action_resource()
    )  # (read, role_permissions)
    typer.echo(
        AppPermissions.UPDATE__ROLE_PERMISSIONS.get_action_resource()
    )  # (update, role_permissions)
    typer.echo(
        AppPermissions.DELETE__ROLE_PERMISSIONS.get_action_resource()
    )  # (delete, role_permissions)
    typer.echo(
        AppPermissions.CREATE__USER_ROLES.get_action_resource()
    )  # (create, user_roles)
    typer.echo(
        AppPermissions.READ__USER_ROLES.get_action_resource()
    )  # (read, user_roles)
    typer.echo(
        AppPermissions.UPDATE__USER_ROLES.get_action_resource()
    )  # (update, user_roles)
    typer.echo(
        AppPermissions.DELETE__USER_ROLES.get_action_resource()
    )  # (delete, user_roles)


if __name__ == "__main__":
    app()
