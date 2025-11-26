import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api import api_router
from app.api.middleware import audit_and_security_middleware
from app.core import settings
from app.core.logging import configure_logging
from app.db import init_db
from app.db.session import engine
from app.db.models import Settings as SettingsModel
from app.services.property_extraction import (
    init_model as init_property_model,
    init_property_prototypes,
)
from app.services.nlp import semantic_embedding_service

logger = logging.getLogger(__name__)

# Carica variabili .env una sola volta all'import del modulo
load_dotenv(Path(__file__).parent.parent / ".env")


def _build_cors_origins() -> list[str]:
    """
    Normalizza e applica politiche di sicurezza CORS in modo centralizzato.
    """
    allowed_origins = settings.cors_origins or []

    if isinstance(allowed_origins, str):
        allowed_origins = [allowed_origins]

    # SECURITY: rimuovi qualsiasi "*"
    allowed_origins = [origin for origin in allowed_origins if origin != "*"]

    if not allowed_origins:
        # SECURITY: fallback sicuro solo su localhost
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    return allowed_origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan centralizza logica di startup/shutdown e viene eseguito una sola volta
    per process (non ad ogni import del modulo).
    """
    # Configura logging prima di tutto
    configure_logging()

    # Inizializza DB (creazione tabelle / migrazioni leggere)
    init_db()

    # Applica configurazione NLP se presente
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

    # Inizializza modello e prototipi proprietà
    try:
        init_property_model()
        init_property_prototypes()
    except Exception as exc:  # pragma: no cover - avvio best-effort
        logger.warning("Impossibile inizializzare il resolver proprietà: %s", exc)

    # Qui l'app è pronta a ricevere richieste
    yield

    # Eventuale logica di shutdown (chiusura connessioni, flush, ecc.)
    # al momento non necessario -> pass
    # es: semantic_embedding_service.close() se servisse in futuro
    # pass


def create_app() -> FastAPI:
    """
    Factory dell'app FastAPI.

    Nota architetturale: l'entrypoint espone i router definiti in app.api.routes,
    utilizza SQLModel (app.db.models) con engine condiviso in app.db.session
    e carica le configurazioni da app.core.settings. I servizi applicativi
    sono organizzati nel package app.services.
    """
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,   # SECURITY: Swagger solo in debug
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Router API
    application.include_router(api_router)

    # Audit e sicurezza: eseguito prima delle route, ma dopo il CORS
    application.middleware("http")(audit_and_security_middleware)

    # CORS rigoroso
    allowed_origins = _build_cors_origins()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # SECURITY: metodi espliciti
        allow_headers=["Content-Type", "Authorization"],            # SECURITY: header espliciti
        expose_headers=["*"],  # Esponi tutti gli header nelle risposte
        max_age=3600,          # Cache preflight per 1 ora
    )

    return application


app = create_app()
