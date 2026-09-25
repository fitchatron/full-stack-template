from enum import StrEnum, auto
from sqlalchemy import and_
from app.models.model import Permission


class AppPermissions(StrEnum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list
    ) -> str:
        verb, _, resource = name.lower().partition("__")
        return f"{verb.replace('asterisk', '*')}:{resource.replace('asterisk', '*')}"

    def get_action_resource(self) -> tuple[str, str]:
        verb, _, resource = self.name.lower().partition("__")
        return verb.replace("asterisk", "*"), resource.replace("asterisk", "*")

    def to_filter_clause(self):
        action, resource = self.get_action_resource()
        return and_(Permission.action == action, Permission.resource == resource)

    ASTERISK__ASTERISK = auto()

    CREATE__ASTERISK = auto()

    ASTERISK__USERS = auto()

    CREATE__USERS = auto()
    READ__USERS = auto()
    UPDATE__USERS = auto()
    DELETE__USERS = auto()

    CREATE__PERMISSIONS = auto()
    READ__PERMISSIONS = auto()
    UPDATE__PERMISSIONS = auto()
    DELETE__PERMISSIONS = auto()

    CREATE__ROLES = auto()
    READ__ROLES = auto()
    UPDATE__ROLES = auto()
    DELETE__ROLES = auto()

    CREATE__ROLE_PERMISSIONS = auto()
    READ__ROLE_PERMISSIONS = auto()
    UPDATE__ROLE_PERMISSIONS = auto()
    DELETE__ROLE_PERMISSIONS = auto()

    CREATE__USER_ROLES = auto()
    READ__USER_ROLES = auto()
    UPDATE__USER_ROLES = auto()
    DELETE__USER_ROLES = auto()
