import uuid

from factory.declarations import (
    LazyAttribute,
    LazyAttributeSequence,
    LazyFunction,
    Sequence,
    SubFactory,
    Trait,
)
from factory.faker import Faker

from app.models import (
    AuthorizationAction,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.core.security import create_salt, hash_with_salt
from seeding.base import BaseFactory

DEFAULT_USER_PASSWORD = "Password123!"  # local dev only, not a secret


class UserFactory(BaseFactory):
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
    # Sequence + a short random suffix (not Faker's `.unique`, which is
    # global, never resets within a process, and can eventually raise
    # UniquenessException) -- the suffix also guards against collisions
    # across separate `db seed` runs, since Sequence restarts at 0 per
    # process.
    email = LazyAttributeSequence(
        lambda o, n: f"{o.given_name}.{o.family_name}.{n}.{uuid.uuid4().hex[:6]}@example.com".lower()
    )
    username = LazyAttributeSequence(
        lambda o, n: f"{o.given_name}{o.family_name}{n}{uuid.uuid4().hex[:6]}".lower()
    )
    email_verified = False
    is_active = True

    salt = LazyFunction(create_salt)
    hashed_password = LazyAttribute(lambda o: hash_with_salt(o.password, o.salt))


class RoleFactory(BaseFactory):
    """
    Ad hoc/randomized roles, for potential future test use. Not used for the
    fixed named roles -- see seeding.fixtures.roles_fixture for those.
    """

    class Meta:
        model = Role

    name = Sequence(lambda n: f"role-{n}")
    description = LazyAttribute(lambda o: f"{o.name} role")


class PermissionFactory(BaseFactory):
    """
    Ad hoc/randomized permissions, for potential future test use. Not used
    for the AppPermissions-derived catalog -- see
    seeding.fixtures.permissions_fixture for those.
    """

    class Meta:
        model = Permission

    action = AuthorizationAction.read
    resource = Sequence(lambda n: f"resource-{n}")
    description = LazyAttribute(lambda o: f"{o.action.value} on {o.resource}")


class RolePermissionFactory(BaseFactory):
    class Meta:
        model = RolePermission

    role = SubFactory(RoleFactory)
    permission = SubFactory(PermissionFactory)


class UserRoleFactory(BaseFactory):
    class Meta:
        model = UserRole

    user = SubFactory(UserFactory)
    role = SubFactory(RoleFactory)
