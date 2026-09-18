import random

from sqlalchemy.orm import Session

from app.models import Role, User, UserRole
from seeding.factories import UserFactory
from seeding.fixtures import admin_user_fixture, permissions_fixture, roles_fixture
from app.core.security import hash_password
from seeding.plan import SeedPlan, SeedResult
from seeding.session import bound_session


class DatabaseSeeder:
    """
    Populates fixed roles/permissions, a known-credentials admin user, and
    random fake users. Local dev only.

    Orchestration only: never commits -- the caller owns the transaction.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def seed(self, plan: SeedPlan | None = None) -> SeedResult:
        plan = plan or SeedPlan()

        with bound_session(self.db):
            permissions = permissions_fixture(self.db)
            roles = roles_fixture(self.db, permissions)
            admin_user = admin_user_fixture(
                self.db, roles, email=plan.admin_email, password=plan.admin_password
            )
            users = self._seed_bulk_users(plan)
            self._assign_random_roles(users, roles, plan.rng)

        return SeedResult(
            roles=roles, permissions=permissions, admin_user=admin_user, users=users
        )

    def _seed_bulk_users(self, plan: SeedPlan) -> list[User]:
        if plan.user_count <= 0:
            return []

        # One shared, real Argon2 hash for all random users -- nobody logs
        # in as a specific one, and per-user hashing doesn't scale (Argon2
        # is deliberately slow).
        salt, hashed_password = hash_password(plan.bulk_user_password)
        return UserFactory.create_batch(
            plan.user_count, salt=salt, hashed_password=hashed_password
        )

    def _assign_random_roles(
        self, users: list[User], roles: dict[str, Role], rng: random.Random
    ) -> None:
        role_list = list(roles.values())
        for user in users:
            k = rng.randint(1, len(role_list))
            for role in rng.sample(role_list, k=k):
                self.db.add(UserRole(user_id=user.user_id, role_id=role.role_id))
        self.db.flush()
