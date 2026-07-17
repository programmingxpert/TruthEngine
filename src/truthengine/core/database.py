"""Database engine, session, and declarative base configuration."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from truthengine.core.config import Settings

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


def create_database_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine from application settings."""
    engine_kwargs: dict[str, Any] = {}
    if settings.database_url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool

        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    return create_engine(settings.database_url, pool_pre_ping=True, **engine_kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory bound to an engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Yield a database session and handle commit, rollback, and close."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
