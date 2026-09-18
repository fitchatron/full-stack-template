from factory.alchemy import SQLAlchemyModelFactory

from seeding.session import get_current_session


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_factory = staticmethod(get_current_session)
        sqlalchemy_session_persistence = "flush"
