from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from sqlalchemy.orm import Session

_current_session: ContextVar[Session | None] = ContextVar(
    "seeding_session", default=None
)


class NoBoundSessionError(RuntimeError):
    """Raised when a seeding factory/fixture runs outside `bound_session(...)`."""


def get_current_session() -> Session:
    session = _current_session.get()
    if session is None:
        raise NoBoundSessionError(
            "No SQLAlchemy session bound for seeding. "
            "Wrap factory calls in `with bound_session(db): ...`."
        )
    return session


@contextmanager
def bound_session(session: Session) -> Generator[Session]:
    """
    Bind `session` as the active session for all seeding factories for the
    lifetime of the `with` block. Reentrant via ContextVar tokens, so a
    caller can nest another `bound_session` inside DatabaseSeeder.seed().
    """
    token: Token[Session | None] = _current_session.set(session)
    try:
        yield session
    finally:
        _current_session.reset(token)
