from sqlalchemy.orm import Session

from app.core.app_permissions import AppPermissions
from app.models import (
    AuthorizationAction,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from seeding.factories import UserFactory
from app.core.security import hash_password
from seeding.utils import get_or_create

FIXED_ADMIN_EMAIL = "admin@example.com"
FIXED_ADMIN_PASSWORD = "Admin123!"  # local dev only, not a secret

FIXED_ROLE_PERMISSIONS: dict[str, list[AppPermissions]] = {
    "public": [],
    "user_admin": [
        AppPermissions.CREATE__USERS,
        AppPermissions.READ__USERS,
        AppPermissions.UPDATE__USERS,
        AppPermissions.DELETE__USERS,
    ],
    "admin": [AppPermissions.ASTERISK__ASTERISK],
}


def permissions_fixture(db: Session) -> dict[tuple[str, str], Permission]:
    """Get-or-create one Permission row per AppPermissions member."""
    result: dict[tuple[str, str], Permission] = {}
    for member in AppPermissions:
        action_str, resource = member.get_action_resource()
        permission, _ = get_or_create(
            db,
            Permission,
            action=AuthorizationAction(action_str),
            resource=resource,
            defaults={"description": f"{action_str} on {resource}"},
        )
        result[(action_str, resource)] = permission
    return result


def roles_fixture(
    db: Session, permissions: dict[tuple[str, str], Permission]
) -> dict[str, Role]:
    """Get-or-create the fixed roles and their permission grants."""
    roles: dict[str, Role] = {}
    for role_name, members in FIXED_ROLE_PERMISSIONS.items():
        role, _ = get_or_create(
            db,
            Role,
            name=role_name,
            defaults={"description": f"{role_name.title()} role"},
        )
        for member in members:
            action_str, resource = member.get_action_resource()
            permission = permissions[(action_str, resource)]
            get_or_create(
                db,
                RolePermission,
                role_id=role.role_id,
                permission_id=permission.permission_id,
            )
        roles[role_name] = role
    return roles


def admin_user_fixture(
    db: Session,
    roles: dict[str, Role],
    *,
    email: str = FIXED_ADMIN_EMAIL,
    password: str = FIXED_ADMIN_PASSWORD,
) -> User:
    """
    Get-or-create the one fixed-credentials admin user, assigned the 'admin'
    role. Re-asserts salt/hashed_password on every run so the known login
    always works even if seeding runs repeatedly.
    """
    user = db.query(User).filter_by(email=email).one_or_none()
    if user is None:
        user = UserFactory.build(
            email=email,
            username="admin",
            given_name="Admin",
            family_name="User",
            password=password,
            email_verified=True,
        )
        db.add(user)
    else:
        user.salt, user.hashed_password = hash_password(password)
    db.flush()

    get_or_create(db, UserRole, user_id=user.user_id, role_id=roles["admin"].role_id)
    return user
