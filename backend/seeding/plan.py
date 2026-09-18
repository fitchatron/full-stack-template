import random
from dataclasses import dataclass, field

from app.models import Permission, Role, User


@dataclass
class SeedPlan:
    user_count: int = 20
    rng: random.Random = field(default_factory=random.Random)
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin123!"
    bulk_user_password: str = "Password123!"


@dataclass
class SeedResult:
    roles: dict[str, Role]
    permissions: dict[tuple[str, str], Permission]
    admin_user: User
    users: list[User]
