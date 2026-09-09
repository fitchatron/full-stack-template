import random

from faker import Faker
from sqlalchemy.orm import Session

from app.models import (
    AuthorizationAction,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)


class DatabaseSeeder:
    """
    Populates fixed roles/permissions and random fake users. Local dev only.

    Roles and permissions are fixed (not randomly generated) since app
    authorization logic is written against their names.
    """

    FIXED_ROLE_PERMISSIONS: dict[str, list[tuple[AuthorizationAction, str]]] = {
        "admin": [],
        "editor": [
            (AuthorizationAction.read, "items"),
            (AuthorizationAction.create, "items"),
            (AuthorizationAction.update, "items"),
        ],
        "viewer": [
            (AuthorizationAction.read, "items"),
            (AuthorizationAction.read, "users"),
        ],
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.faker = Faker()

    def seed(self, user_count: int) -> tuple[dict[str, Role], list[User]]:
        roles = self.seed_roles_and_permissions()
        users = self.seed_users(user_count)
        self.assign_random_roles(users, roles)
        return roles, users

    def seed_roles_and_permissions(self) -> dict[str, Role]:
        roles = {}
        for role_name, permissions in self.FIXED_ROLE_PERMISSIONS.items():
            role = self.db.query(Role).filter_by(name=role_name).one_or_none()
            if role is None:
                role = Role(name=role_name, description=f"{role_name.title()} role")
                self.db.add(role)
                self.db.flush()

            granted = {
                rp.permission_id
                for rp in self.db.query(RolePermission).filter_by(role_id=role.role_id)
            }
            for action, resource in permissions:
                permission = (
                    self.db.query(Permission)
                    .filter_by(action=action, resource=resource)
                    .one_or_none()
                )
                if permission is None:
                    permission = Permission(
                        action=action,
                        resource=resource,
                        description=f"{action.value} on {resource}",
                    )
                    self.db.add(permission)
                    self.db.flush()

                if permission.permission_id not in granted:
                    self.db.add(
                        RolePermission(
                            role_id=role.role_id,
                            permission_id=permission.permission_id,
                        )
                    )

            roles[role_name] = role

        return roles

    def seed_users(self, count: int) -> list[User]:
        users = [
            User(
                email=self.faker.unique.email(),
                username=self.faker.unique.user_name(),
                given_name=self.faker.first_name(),
                family_name=self.faker.last_name(),
            )
            for _ in range(count)
        ]
        self.db.add_all(users)
        self.db.flush()
        return users

    def assign_random_roles(self, users: list[User], roles: dict[str, Role]) -> None:
        role_list = list(roles.values())
        for user in users:
            for role in random.sample(role_list, k=random.randint(1, len(role_list))):
                self.db.add(UserRole(user_id=user.user_id, role_id=role.role_id))
