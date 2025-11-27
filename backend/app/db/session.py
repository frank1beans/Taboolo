from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

from app.core import settings


_url = make_url(settings.effective_database_url)
connect_args: dict = {}
engine_kwargs = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

if _url.get_backend_name().startswith("sqlite"):
    # Aumenta il timeout per ridurre i lock "database is locked" durante batch pesanti
    connect_args = {"check_same_thread": False, "timeout": 60, "isolation_level": None}
else:
    engine_kwargs.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        }
    )

engine = create_engine(settings.effective_database_url, connect_args=connect_args, **engine_kwargs)

# Abilita WAL per SQLite in dev per ridurre i lock durante scritture concorrenti
if _url.get_backend_name().startswith("sqlite"):
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager esplicito per operazioni di servizio."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
