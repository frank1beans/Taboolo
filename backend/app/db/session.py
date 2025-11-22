from contextlib import contextmanager
from typing import Generator

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
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        }
    )

engine = create_engine(settings.effective_database_url, connect_args=connect_args, **engine_kwargs)


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
