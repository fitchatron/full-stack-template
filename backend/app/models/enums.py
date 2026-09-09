from enum import StrEnum
from sqlalchemy import Enum


class AuthorizationAction(StrEnum):
    all = "*"
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


authorization_action_type = Enum(
    AuthorizationAction,
    name="authorization_action",
    values_callable=lambda enum: [e.value for e in enum],
)
