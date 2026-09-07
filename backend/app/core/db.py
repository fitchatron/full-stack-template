from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# create engine object
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.SQLALCHEMY_DATABASE_POOL_SIZE,
    pool_pre_ping=settings.SQLALCHEMY_POOL_PRE_PING,
)

# factory function to create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# setup naming convention
convention = {
    "ix": "ix__%(table_name)s__%(column_0_N_name)s",
    "uq": "uq__%(table_name)s__%(column_0_N_name)s",
    "ck": "ck__%(table_name)s__%(column_0_N_name)s",
    "fk": "fk__%(table_name)s__%(column_0_N_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}


# model base class
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
