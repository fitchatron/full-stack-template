from dataclasses import dataclass

from app.models import Permission, Role, User

# Fixed so a seed run produces the same Faker-driven field values and the
# same random role assignments every time, against a freshly reset schema.
DEFAULT_SEED = 1234


@dataclass
class SeedPlan:
    include_mock_data: bool = False
    admin_user: bool = True
    user_count: int = 200
    faker_seed: int = DEFAULT_SEED
    bulk_user_password: str = "Password123!"


@dataclass
class SeedResult:
    roles: dict[str, Role]
    permissions: dict[tuple[str, str], Permission]
    admin_user: User | None
    users: list[User]
