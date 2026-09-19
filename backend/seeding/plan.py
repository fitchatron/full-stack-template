import random
from dataclasses import dataclass, field

from app.models import Permission, Role, User

# Fixed so a seed run produces the same Faker-driven field values and the
# same random role assignments every time, against a freshly reset schema.
DEFAULT_SEED = 1234


@dataclass
class SeedPlan:
    include_mock_data: bool = False
    user_count: int = 20
    faker_seed: int = DEFAULT_SEED
    rng: random.Random = field(default_factory=lambda: random.Random(DEFAULT_SEED))
    bulk_user_password: str = "Password123!"


@dataclass
class SeedResult:
    roles: dict[str, Role]
    permissions: dict[tuple[str, str], Permission]
    admin_user: User
    users: list[User]
