from factory.alchemy import SQLAlchemyModelFactory
from factory.declarations import (
    LazyAttribute,
    LazyAttributeSequence,
    LazyFunction,
    Sequence,
    Trait,
)
from factory.faker import Faker

from app.core.security import create_salt, hash_with_salt
from app.models import AuthorizationAction, Permission, User

DEFAULT_USER_PASSWORD = "Password123!"  # local dev only, not a secret


class UserFactory(SQLAlchemyModelFactory):
    """
    Build-only: `.build()`/`.build_batch()` never touch a session, so
    callers add the resulting instances themselves.
    """

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


class PermissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Permission

    action = AuthorizationAction.read
    resource = Sequence(lambda n: f"resource-{n}")
    description = LazyAttribute(
        lambda o: "Full access to all actions and resources."
        if o.action == AuthorizationAction.all and o.resource == "*"
        else f"Permission to {o.action.value} {o.resource}."
    )
