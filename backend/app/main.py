import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Carica variabili .env per roBERT/Ollama
load_dotenv(Path(__file__).parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api import api_router
from app.api.middleware import audit_and_security_middleware
from app.core import settings
from app.core.logging import configure_logging
from app.db import init_db
from app.db.session import engine
from app.db.models import Settings as SettingsModel
from app.services.property_extraction import init_model as init_property_model, init_property_prototypes
from app.services.nlp import semantic_embedding_service

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    # Nota architetturale: l'entrypoint espone i router definiti in app.api.routes,
    # utilizza SQLModel (app.db.models) con engine condiviso in app.db.session
    # e carica le configurazioni da app.core.config/settings. I servizi applicativi
    # sono organizzati nel package app.services.
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,  # SECURITY: Swagger solo in debug
        redoc_url="/redoc" if settings.debug else None,
    )

    # SECURITY: CORS rigoroso - mai accettare "*"
    allowed_origins = settings.cors_origins or []
    if isinstance(allowed_origins, str):
        allowed_origins = [allowed_origins]

    # SECURITY: Rimuovi qualsiasi "*" dalla lista
    allowed_origins = [origin for origin in allowed_origins if origin != "*"]

    if not allowed_origins:
        # SECURITY: Se non configurato, usa solo localhost
        allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # SECURITY: Metodi espliciti, no "*"
        allow_headers=["Content-Type", "Authorization"],  # SECURITY: Headers espliciti
        expose_headers=["*"],  # Esponi tutti gli headers nelle risposte
        max_age=3600,  # Cache preflight per 1 ora
    )

    @application.on_event("startup")
    def _startup() -> None:
        init_db()
        try:
            with Session(engine) as session:
                settings_row = session.query(SettingsModel).first()
                if settings_row:
                    semantic_embedding_service.configure(
                        model_id=settings_row.nlp_model_id,
                        max_length=settings_row.nlp_max_length,
                        batch_size=settings_row.nlp_batch_size,
                    )
        except Exception as exc:  # pragma: no cover - avvio best-effort
            logger.warning("Impossibile applicare la configurazione NLP: %s", exc)
        try:
            init_property_model()
            init_property_prototypes()
        except Exception as exc:  # pragma: no cover - avvio best-effort
            logger.warning("Impossibile inizializzare il resolver proprietà: %s", exc)

    application.include_router(api_router)
    application.middleware("http")(audit_and_security_middleware)
    return application


app = create_app()
