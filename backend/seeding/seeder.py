import random
from dataclasses import dataclass

import factory.random
from sqlalchemy.orm import Session

from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    AuthorizationAction,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from seeding.factories import PermissionFactory, UserFactory
from seeding.plan import SeedPlan, SeedResult

# Fixed, concrete reference data -- see authZ-seed.sql for the original
# authorization design this was derived from ("accounts" there maps to our
# "users" resource). admin is granted every permission in the catalog,
# rather than just the wildcard, to mirror that reference directly.
FIXED_ROLES: dict[str, tuple[str, str]] = {
    "admin": ("Admin", "admin role for the application"),
    "user_admin": ("User Admin", "Role that can assign users to roles."),
    "public": (
        "Public",
        "Public role for the application. Users are assigned this role by default.",
    ),
}

FIXED_ROLE_GRANTS: dict[str, list[AppPermissions]] = {
    "public": [
        AppPermissions.READ__USERS,
        AppPermissions.READ__USER_ROLES,
        AppPermissions.UPDATE__USERS,
    ],
    "user_admin": [
        AppPermissions.CREATE__USERS,
        AppPermissions.READ__USERS,
        AppPermissions.UPDATE__USERS,
        AppPermissions.DELETE__USERS,
        AppPermissions.CREATE__USER_ROLES,
        AppPermissions.READ__USER_ROLES,
        AppPermissions.UPDATE__USER_ROLES,
        AppPermissions.DELETE__USER_ROLES,
    ],
    "admin": list(AppPermissions),
}


@dataclass
class CoreSeedResult:
    roles: dict[str, Role]
    permissions: dict[tuple[str, str], Permission]
    admin_user: User


class DatabaseSeeder:
    """
    Seeds a freshly reset database. Always assumes an empty schema: every
    insert is unconditional, there is no get-or-create/idempotency here.

    `seed_core_data()` creates everything the app requires to function --
    roles, the full permission catalog, role grants, and the first
    superuser -- so it's the place for any future critical data too.
    `seed_mock_data()` adds random local-dev-only filler on top. `seed()`
    runs the former always, the latter only if requested, and commits once
    at the end.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def seed(self, plan: SeedPlan | None = None) -> SeedResult:
        plan = plan or SeedPlan()

        core = self.seed_core_data()
        users = self.seed_mock_data(core.roles, plan) if plan.include_mock_data else []

        self.session.commit()
        return SeedResult(
            roles=core.roles,
            permissions=core.permissions,
            admin_user=core.admin_user,
            users=users,
        )

    def seed_core_data(self) -> CoreSeedResult:
        permissions = self._seed_permissions()
        roles = self._seed_roles(permissions)
        admin_user = self._seed_admin_user(roles)
        return CoreSeedResult(roles=roles, permissions=permissions, admin_user=admin_user)

    def seed_mock_data(self, roles: dict[str, Role], plan: SeedPlan) -> list[User]:
        factory.random.reseed_random(plan.faker_seed)

        salt, hashed_password = hash_password(plan.bulk_user_password)
        users = UserFactory.build_batch(
            plan.user_count, salt=salt, hashed_password=hashed_password
        )
        self.session.add_all(users)
        self._assign_random_roles(users, roles, plan.rng)
        return users

    def _seed_permissions(self) -> dict[tuple[str, str], Permission]:
        permissions: dict[tuple[str, str], Permission] = {}
        for member in AppPermissions:
            action, resource = member.get_action_resource()
            permission = PermissionFactory.build(
                action=AuthorizationAction(action), resource=resource
            )
            self.session.add(permission)
            permissions[(action, resource)] = permission
        return permissions

    def _seed_roles(self, permissions: dict[tuple[str, str], Permission]) -> dict[str, Role]:
        roles: dict[str, Role] = {}
        for role_id, (name, description) in FIXED_ROLES.items():
            role = Role(role_id=role_id, name=name, description=description)
            self.session.add(role)
            roles[role_id] = role

        for role_name, granted in FIXED_ROLE_GRANTS.items():
            role = roles[role_name]
            for member in granted:
                permission = permissions[member.get_action_resource()]
                self.session.add(RolePermission(role=role, permission=permission))

        return roles

    def _seed_admin_user(self, roles: dict[str, Role]) -> User:
        admin_user = UserFactory.build(
            email=settings.FIRST_SUPERUSER,
            username="admin",
            given_name="Admin",
            family_name="User",
            password=settings.FIRST_SUPERUSER_PASSWORD,
            email_verified=True,
        )
        self.session.add(admin_user)
        self.session.add(UserRole(user=admin_user, role=roles["admin"]))
        return admin_user

    def _assign_random_roles(
        self, users: list[User], roles: dict[str, Role], rng: random.Random
    ) -> None:
        role_list = list(roles.values())
        for user in users:
            for role in rng.sample(role_list, k=rng.randint(1, len(role_list))):
                self.session.add(UserRole(user=user, role=role))
