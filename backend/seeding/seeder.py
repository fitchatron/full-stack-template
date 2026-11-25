import random
from dataclasses import dataclass

import factory.random
from sqlalchemy import select
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
from app.models.model import EmailTemplate
from seeding.factories import EmailTemplateFactory, PermissionFactory, UserFactory
from seeding.plan import SeedPlan, SeedResult

# Fixed role <-> permission mapping
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
        AppPermissions.ASTERISK__USERS,
        AppPermissions.ASTERISK__USER_ROLES,
    ],
    "admin": list(AppPermissions),
}


@dataclass
class CoreSeedResult:
    roles: dict[str, Role]
    permissions: dict[tuple[str, str], Permission]


class DatabaseSeeder:
    """
    Inserts data into an existing schema. Schema lifecycle (create/drop) lives
    in DatabaseManager.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def seed(self, plan: SeedPlan | None = None) -> SeedResult:
        plan = plan or SeedPlan()

        core = (
            self._seed_core_data() if plan.include_core_data else self._load_core_data()
        )

        admin_user = self._seed_admin_user(core.roles) if plan.admin_user else None

        (users, email_templates) = (
            self.seed_mock_data(core.roles, plan)
            if plan.include_mock_data
            else ([], [])
        )

        # self.session.add_all(email_templates)
        self.session.commit()
        return SeedResult(
            roles=core.roles,
            permissions=core.permissions,
            admin_user=admin_user,
            users=users,
            email_templates=email_templates,
        )

    def _load_core_data(self) -> CoreSeedResult:
        roles = {r.role_id: r for r in self.session.scalars(select(Role))}
        permissions = {
            (p.action.__str__(), p.resource): p
            for p in self.session.scalars(select(Permission))
        }
        return CoreSeedResult(roles=roles, permissions=permissions)

    def _seed_core_data(self) -> CoreSeedResult:
        permissions = self._seed_permissions()
        roles = self._seed_roles(permissions)
        return CoreSeedResult(roles=roles, permissions=permissions)

    def seed_mock_data(
        self, roles: dict[str, Role], plan: SeedPlan
    ) -> tuple[list[User], list[EmailTemplate]]:
        factory.random.reseed_random(plan.faker_seed)

        users = self._seed_users(
            faker_seed=plan.faker_seed,
            bulk_user_password=plan.bulk_user_password,
            user_count=plan.user_count,
            roles=roles,
        )

        email_templates = self._create_email_templates()
        return (users, email_templates)

    def _seed_users(
        self,
        faker_seed: int,
        bulk_user_password: str,
        user_count: int,
        roles: dict[str, Role],
    ) -> list[User]:
        salt, hashed_password = hash_password(bulk_user_password)
        users = UserFactory.build_batch(
            user_count, salt=salt, hashed_password=hashed_password
        )
        self.session.add_all(users)
        self._assign_random_roles(users, roles, random.Random(faker_seed))

        return users

    def _create_email_templates(self):
        templates = [
            {
                "name": "test_email",
                "body_template": '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1.0"/><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"/><meta name="x-apple-disable-message-reformatting"/><title>{{ project_name }} - Test email</title></head><body style="background-color:#f4f7f6;margin:0;padding:0"><!--$--><!--html--><!--head--><div style="display:none;overflow:hidden;line-height:1px;opacity:0;max-height:0;max-width:0" data-skip-in-text="true">{{ project_name }} email delivery is working<div></div></div><!--body--><table border="0" width="100%" cellPadding="0" cellSpacing="0" role="presentation" align="center"><tbody><tr><td style="background-color:#f4f7f6;color:#1e293b;font-family:-apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, Helvetica, Arial, sans-serif;margin:0;padding:32px 12px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="max-width:560px;background-color:#ffffff;border:1px solid #dce7e5;border-radius:8px;box-sizing:border-box;margin:0 auto;width:100%"><tbody><tr style="width:100%"><td><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody style="width:100%"><tr style="width:100%"><td data-id="__react-email-column" style="padding:40px 36px 32px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><hr style="width:32px;border:0;border-top:3px solid #00897b;margin:0 0 16px"/><p style="font-size:13px;line-height:20px;color:#334155;font-weight:700;letter-spacing:1px;margin:0 0 32px;text-transform:uppercase;margin-top:0;margin-right:0;margin-bottom:32px;margin-left:0">{{ project_name }}</p></td></tr></tbody></table><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><h1 style="color:#17212b;font-size:26px;font-weight:700;letter-spacing:-0.3px;line-height:34px;margin:0 0 20px">Test email</h1><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">Hi,</p><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">This is a test email from <!-- -->{{ project_name }}<!-- -->. If you&#x27;re reading it, email delivery is configured correctly.</p><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="background-color:#f2f8f7;border-left:3px solid #00897b;margin:24px 0 28px;padding:6px 18px"><tbody><tr><td><p style="font-size:14px;line-height:24px;margin:12px 0;margin-top:12px;margin-right:0;margin-bottom:12px;margin-left:0"><span style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;line-height:16px;text-transform:uppercase">Sent to</span><br/><span style="color:#1e293b;font-family:Consolas, &quot;Courier New&quot;, monospace;font-size:14px;font-weight:700;line-height:22px;word-break:break-all">{{ email }}</span></p></td></tr></tbody></table><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">If you weren&#x27;t expecting this email, you can safely ignore it.</p></td></tr></tbody></table><hr style="width:100%;border:0;border-top:1px solid #dce7e5;margin:36px 0 18px"/><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><p style="font-size:12px;line-height:20px;color:#64748b;margin:0;margin-top:0;margin-bottom:0;margin-left:0;margin-right:0">© <!-- -->2026<!-- --> <!-- -->{{ project_name }}<!-- -->. All rights reserved.</p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><!--/$--></body></html>',
                "body_context_schema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["project_name", "email"],
                    "additionalProperties": False,
                },
                "subject_template": "This is a test for {{ project_name }}",
                "subject_context_schema": {
                    "type": "object",
                    "properties": {"project_name": {"type": "string"}},
                    "required": ["project_name"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "new_account",
                "body_template": '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1.0"/><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"/><meta name="x-apple-disable-message-reformatting"/><title>{{ project_name }} - New account</title></head><body style="background-color:#f4f7f6;margin:0;padding:0"><!--$--><!--html--><!--head--><div style="display:none;overflow:hidden;line-height:1px;opacity:0;max-height:0;max-width:0" data-skip-in-text="true">Your {{ project_name }} account is ready<div></div></div><!--body--><table border="0" width="100%" cellPadding="0" cellSpacing="0" role="presentation" align="center"><tbody><tr><td style="background-color:#f4f7f6;color:#1e293b;font-family:-apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, Helvetica, Arial, sans-serif;margin:0;padding:32px 12px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="max-width:560px;background-color:#ffffff;border:1px solid #dce7e5;border-radius:8px;box-sizing:border-box;margin:0 auto;width:100%"><tbody><tr style="width:100%"><td><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody style="width:100%"><tr style="width:100%"><td data-id="__react-email-column" style="padding:40px 36px 32px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><hr style="width:32px;border:0;border-top:3px solid #00897b;margin:0 0 16px"/><p style="font-size:13px;line-height:20px;color:#334155;font-weight:700;letter-spacing:1px;margin:0 0 32px;text-transform:uppercase;margin-top:0;margin-right:0;margin-bottom:32px;margin-left:0">{{ project_name }}</p></td></tr></tbody></table><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><h1 style="color:#17212b;font-size:26px;font-weight:700;letter-spacing:-0.3px;line-height:34px;margin:0 0 20px">Welcome to <!-- -->{{ project_name }}<!-- -->!</h1><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">Hi,</p><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">Your account has been successfully created and is ready to use. These are your credentials:</p><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="background-color:#f2f8f7;border-left:3px solid #00897b;margin:24px 0 28px;padding:6px 18px"><tbody><tr><td><p style="font-size:14px;line-height:24px;margin:12px 0;margin-top:12px;margin-right:0;margin-bottom:12px;margin-left:0"><span style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;line-height:16px;text-transform:uppercase">Username</span><br/><span style="color:#1e293b;font-family:Consolas, &quot;Courier New&quot;, monospace;font-size:14px;font-weight:700;line-height:22px;word-break:break-all">{{ username }}</span></p><p style="font-size:14px;line-height:24px;margin:12px 0;margin-top:12px;margin-right:0;margin-bottom:12px;margin-left:0"><span style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;line-height:16px;text-transform:uppercase">Password</span><br/><span style="color:#1e293b;font-family:Consolas, &quot;Courier New&quot;, monospace;font-size:14px;font-weight:700;line-height:22px;word-break:break-all">{{ email }}</span></p></td></tr></tbody></table><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">Get started by signing in to your dashboard:</p><a href="{{ link }}" style="line-height:20px;text-decoration:none;display:inline-block;max-width:100%;mso-padding-alt:0px;background-color:#00796b;border-radius:6px;color:#ffffff;font-size:14px;font-weight:700;margin:8px 0 28px;padding:13px 28px;text-align:center;padding-top:13px;padding-right:28px;padding-bottom:13px;padding-left:28px" target="_blank"><span><!--[if mso]><i style="mso-font-width:466.6666666666667%;mso-text-raise:19.5" hidden>&#8202;&#8202;&#8202;</i><![endif]--></span><span style="max-width:100%;display:inline-block;line-height:120%;mso-padding-alt:0px;mso-text-raise:9.75px">Go to Dashboard</span><span><!--[if mso]><i style="mso-font-width:466.6666666666667%" hidden>&#8202;&#8202;&#8202;&#8203;</i><![endif]--></span></a><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">Or copy and paste this link into your browser:<br/><a href="{{ link }}" style="color:#00695c;text-decoration-line:none;text-decoration:underline;word-break:break-all" target="_blank">{{ link }}</a></p><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">For security reasons, change your password after your first sign in.</p></td></tr></tbody></table><hr style="width:100%;border:0;border-top:1px solid #dce7e5;margin:36px 0 18px"/><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><p style="font-size:12px;line-height:20px;color:#64748b;margin:0;margin-top:0;margin-bottom:0;margin-left:0;margin-right:0">© <!-- -->2026<!-- --> <!-- -->{{ project_name }}<!-- -->. All rights reserved.</p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><!--/$--></body></html>',
                "body_context_schema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "link": {"type": "string"},
                    },
                    "required": ["project_name", "username", "email", "link"],
                    "additionalProperties": False,
                },
                "subject_template": "Welcome to {{ project_name }}",
                "subject_context_schema": {
                    "type": "object",
                    "properties": {"project_name": {"type": "string"}},
                    "required": ["project_name"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "reset_password",
                "body_template": '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1.0"/><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"/><meta name="x-apple-disable-message-reformatting"/><title>{{ project_name }} - Password recovery</title></head><body style="background-color:#f4f7f6;margin:0;padding:0"><!--$--><!--html--><!--head--><div style="display:none;overflow:hidden;line-height:1px;opacity:0;max-height:0;max-width:0" data-skip-in-text="true">Reset your {{ project_name }} password<div></div></div><!--body--><table border="0" width="100%" cellPadding="0" cellSpacing="0" role="presentation" align="center"><tbody><tr><td style="background-color:#f4f7f6;color:#1e293b;font-family:-apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, Helvetica, Arial, sans-serif;margin:0;padding:32px 12px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="max-width:560px;background-color:#ffffff;border:1px solid #dce7e5;border-radius:8px;box-sizing:border-box;margin:0 auto;width:100%"><tbody><tr style="width:100%"><td><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody style="width:100%"><tr style="width:100%"><td data-id="__react-email-column" style="padding:40px 36px 32px"><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><hr style="width:32px;border:0;border-top:3px solid #00897b;margin:0 0 16px"/><p style="font-size:13px;line-height:20px;color:#334155;font-weight:700;letter-spacing:1px;margin:0 0 32px;text-transform:uppercase;margin-top:0;margin-right:0;margin-bottom:32px;margin-left:0">{{ project_name }}</p></td></tr></tbody></table><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><h1 style="color:#17212b;font-size:26px;font-weight:700;letter-spacing:-0.3px;line-height:34px;margin:0 0 20px">Reset your password</h1><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">Hi <!-- -->{{ username }}<!-- -->,</p><p style="font-size:15px;line-height:26px;color:#334155;margin:0 0 18px;margin-top:0;margin-right:0;margin-bottom:18px;margin-left:0">We&#x27;ve received a request to reset the password for your <!-- -->{{ project_name }}<!-- --> <!-- -->account. Choose a new one by clicking the button below:</p><a href="{{ link }}" style="line-height:20px;text-decoration:none;display:inline-block;max-width:100%;mso-padding-alt:0px;background-color:#00796b;border-radius:6px;color:#ffffff;font-size:14px;font-weight:700;margin:8px 0 28px;padding:13px 28px;text-align:center;padding-top:13px;padding-right:28px;padding-bottom:13px;padding-left:28px" target="_blank"><span><!--[if mso]><i style="mso-font-width:466.6666666666667%;mso-text-raise:19.5" hidden>&#8202;&#8202;&#8202;</i><![endif]--></span><span style="max-width:100%;display:inline-block;line-height:120%;mso-padding-alt:0px;mso-text-raise:9.75px">Reset password</span><span><!--[if mso]><i style="mso-font-width:466.6666666666667%" hidden>&#8202;&#8202;&#8202;&#8203;</i><![endif]--></span></a><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">Or copy and paste this link into your browser:<br/><a href="{{ link }}" style="color:#00695c;text-decoration-line:none;text-decoration:underline;word-break:break-all" target="_blank">{{ link }}</a></p><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">This link will expire in <!-- -->{{ valid_hours }}<!-- --> hours.</p><p style="font-size:14px;line-height:23px;color:#64748b;margin:0 0 16px;margin-top:0;margin-right:0;margin-bottom:16px;margin-left:0">If you didn&#x27;t request a password recovery, you can safely ignore this email.</p></td></tr></tbody></table><hr style="width:100%;border:0;border-top:1px solid #dce7e5;margin:36px 0 18px"/><table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation"><tbody><tr><td><p style="font-size:12px;line-height:20px;color:#64748b;margin:0;margin-top:0;margin-bottom:0;margin-left:0;margin-right:0">© <!-- -->2026<!-- --> <!-- -->{{ project_name }}<!-- -->. All rights reserved.</p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><!--/$--></body></html>',
                "body_context_schema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "username": {"type": "string"},
                        "link": {"type": "string"},
                    },
                    "required": ["project_name", "username", "link"],
                    "additionalProperties": False,
                },
                "subject_template": "Reset your password for {{ project_name }}",
                "subject_context_schema": {
                    "type": "object",
                    "properties": {"project_name": {"type": "string"}},
                    "required": ["project_name"],
                    "additionalProperties": False,
                },
            },
        ]

        email_templates: list[EmailTemplate] = []
        for template in templates:
            email_templates.append(
                EmailTemplateFactory.build(
                    name=template["name"],
                    subject_template=template["subject_template"],
                    subject_context_schema=template["subject_context_schema"],
                    body_template=template["body_template"],
                    body_context_schema=template["body_context_schema"],
                )
            )

        self.session.add_all(email_templates)
        return email_templates

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

    def _seed_roles(
        self, permissions: dict[tuple[str, str], Permission]
    ) -> dict[str, Role]:
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
