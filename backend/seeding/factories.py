from datetime import UTC, datetime, timedelta
from typing import Generic, TypeVar

from factory.alchemy import SQLAlchemyModelFactory as _SQLAlchemyModelFactory
from factory.declarations import (
    LazyAttribute,
    LazyAttributeSequence,
    LazyFunction,
    Sequence,
    SubFactory,
    Trait,
)
from factory.faker import Faker

from app.core.security import create_salt, hash_with_salt
from app.models import (
    AuthorizationAction,
    Permission,
    User,
    UserRole,
    Role,
    RolePermission,
)

DEFAULT_USER_PASSWORD = "Password123!"  # local dev only, not a secret

ModelT = TypeVar("ModelT")


class SQLAlchemyModelFactory(_SQLAlchemyModelFactory, Generic[ModelT]):
    """Re-adds the Generic[T] param that factory_boy's own base drops.

    `factory.alchemy.SQLAlchemyModelFactory` subclasses `factory.Factory`
    without subscripting it, so `T` resolves to `Unknown` and every
    subclass's `.build()`/`.create()` return type is `Unknown` regardless
    of `Meta.model`. Subclass as `SQLAlchemyModelFactory[Model]` to restore
    typed returns.
    """

    class Meta:
        abstract = True

    @classmethod
    def build(cls, **kwargs) -> ModelT:
        return super().build(**kwargs)

    @classmethod
    def create(cls, **kwargs) -> ModelT:
        return super().create(**kwargs)


class UserFactory(SQLAlchemyModelFactory[User]):

    class Meta:
        model = User

    class Params:
        # Non-model pseudo-field: consumed by `hashed_password` below, never
        # passed to User(). Override it to get a real hash of a known
        # plaintext (e.g. for a user that needs to log in); override
        # `hashed_password`/`salt` directly instead to skip hashing entirely.
        password = DEFAULT_USER_PASSWORD
        inactive = Trait(is_active=False)
        verified = Trait(email_verified=True)

    given_name = Faker("first_name")
    family_name = Faker("last_name")
    # Sequence (not Faker's `.unique`, which is global mutable state that
    # never resets within a process) is enough for uniqueness: every seed
    # run starts against a freshly reset, empty table.
    email = LazyAttributeSequence(
        lambda o, n: f"{o.given_name}.{o.family_name}.{n}@example.com".lower()
    )
    username = LazyAttributeSequence(
        lambda o, n: f"{o.given_name}{o.family_name}{n}".lower()
    )
    email_verified = False
    is_active = True

    salt = LazyFunction(create_salt)
    hashed_password = LazyAttribute(lambda o: hash_with_salt(o.password, o.salt))


class RoleFactory(SQLAlchemyModelFactory[Role]):

    class Meta:
        model = Role

    role_id = Sequence(lambda n: f"role-{n}")
    name = LazyAttribute(lambda o: o.role_id.capitalize())
    description = LazyAttribute(lambda o: f"Description for role {o.name}")


class UserRoleFactory(SQLAlchemyModelFactory[UserRole]):

    class Meta:
        model = UserRole

    user = SubFactory(UserFactory)
    role = SubFactory(RoleFactory)

    # A minute in the past, not now: Postgres' now() is frozen at transaction
    # start, so a role created later in the same transaction (as in tests)
    # would otherwise not yet count as active.
    start_at = LazyFunction(lambda: datetime.now(UTC) - timedelta(minutes=1))
    end_at = LazyAttribute(lambda o: o.start_at + timedelta(days=365))


class PermissionFactory(SQLAlchemyModelFactory[Permission]):
    class Meta:
        model = Permission

    action = AuthorizationAction.read
    resource = Sequence(lambda n: f"resource-{n}")
    description = LazyAttribute(
        lambda o: (
            "Full access to all actions and resources."
            if o.action == AuthorizationAction.all and o.resource == "*"
            else f"Permission to {o.action.value} {o.resource}."
        )
    )


class RolePermissionFactory(SQLAlchemyModelFactory[RolePermission]):

    class Meta:
        model = RolePermission

    role = SubFactory(RoleFactory)
    permission = SubFactory(PermissionFactory)
