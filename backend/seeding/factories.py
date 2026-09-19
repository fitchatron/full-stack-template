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
        password = DEFAULT_USER_PASSWORD
        inactive = Trait(is_active=False)
        verified = Trait(email_verified=True)

    given_name = Faker("first_name")
    family_name = Faker("last_name")
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

    role_id = Sequence(lambda n: f"role_{n}")
    name = Sequence(lambda n: f"Role {n}")
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
