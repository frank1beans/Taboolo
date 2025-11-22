import logging

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, select

from app.core import settings
from app.core.security import hash_password
from app.db.models import User, UserProfile, UserRole
from app.db.session import engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Crea tutte le tabelle e applica gli aggiornamenti necessari."""
    SQLModel.metadata.create_all(engine)
    _healthcheck()
    _ensure_settings_columns()
    _ensure_price_list_item_columns()
    _ensure_seed_admin()


def _ensure_settings_columns() -> None:
    """Aggiunge le nuove colonne NLP alla tabella settings se mancanti."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "settings" not in tables:
        return

    existing = {column["name"] for column in inspector.get_columns("settings")}
    required_columns = [
        (
            "nlp_model_id",
            "TEXT",
            "'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'",
        ),
        ("nlp_batch_size", "INTEGER", "32"),
        ("nlp_max_length", "INTEGER", "256"),
        ("nlp_embeddings_model_id", "TEXT", "NULL"),
    ]

    with engine.begin() as connection:
        for name, column_type, default in required_columns:
            if name in existing:
                continue
            ddl = f"ALTER TABLE settings ADD COLUMN {name} {column_type}"
            if default is not None:
                ddl += f" DEFAULT {default}"
            try:
                connection.execute(text(ddl))
                if name == "nlp_embeddings_model_id":
                    connection.execute(
                        text(
                            "UPDATE settings "
                            "SET nlp_embeddings_model_id = nlp_model_id "
                            "WHERE nlp_embeddings_model_id IS NULL"
                        )
                    )
                logger.info("Added missing column '%s' to settings table.", name)
            except SQLAlchemyError as exc:  # pragma: no cover - best effort
                logger.warning(
                    "Unable to add column '%s' to settings table: %s", name, exc
                )


def _ensure_price_list_item_columns() -> None:
    """Aggiunge colonne mancanti su price_list_item (preventivo_id, created_at, updated_at)."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "price_list_item" not in tables:
        return

    existing = {column["name"] for column in inspector.get_columns("price_list_item")}
    columns = [
        ("preventivo_id", "TEXT", None),
        ("created_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
    ]
    with engine.begin() as connection:
        for name, column_type, default in columns:
            if name in existing:
                continue
            ddl = f"ALTER TABLE price_list_item ADD COLUMN {name} {column_type}"
            if default is not None:
                ddl += f" DEFAULT {default}"
            try:
                connection.execute(text(ddl))
                logger.info("Added missing column '%s' to price_list_item table.", name)
            except SQLAlchemyError as exc:  # pragma: no cover - best effort
                logger.warning("Unable to add column '%s' to price_list_item: %s", name, exc)


def _healthcheck() -> None:
    """Verifica la raggiungibilità del DB (ISO A.17)."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover - best effort
        logger.error("Database healthcheck failed: %s", exc)


def _ensure_seed_admin() -> None:
    """Crea un utente amministratore predefinito per ambienti demo/sviluppo."""
    email = settings.seed_admin_email
    password = settings.seed_admin_password
    if not email or not password:
        return

    try:
        with Session(engine) as session:
            existing = session.exec(select(User).where(User.email == email)).first()
            if existing:
                return

            admin = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=settings.seed_admin_full_name,
                role=UserRole.admin,
                is_active=True,
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)

            profile = UserProfile(user_id=admin.id, company="Taboolo", language="it-IT")
            session.add(profile)
            session.commit()

            logger.info("Created seed admin user '%s'", email)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Unable to seed default admin user: %s", exc)
