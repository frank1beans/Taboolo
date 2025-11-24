from pathlib import Path
import sys

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_storage_root() -> Path:
    """Return the storage folder depending on the runtime (source vs PyInstaller)."""
    if getattr(sys, "frozen", False):
        # When bundled with PyInstaller, keep data next to the executable.
        return Path(sys.executable).resolve().parent / "storage"
    return Path(__file__).resolve().parent.parent.parent / "storage"


class Settings(BaseSettings):
    """Configurazione centrale dell'applicazione."""

    app_name: str = "Taboo Measure Maker Backend"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False  # SECURITY: Disabilitato debug mode in produzione

    # Storage paths / database
    storage_root: Path = _default_storage_root()
    database_path: Path = Path("database.sqlite")
    database_url: str | None = Field(
        default=None,
        description=(
            "SQLAlchemy URL (PostgreSQL raccomandato in produzione per concorrenza/ISO)."
        ),
    )
    db_pool_size: int = Field(default=10, description="Pool di connessioni DB (Postgres)")
    db_max_overflow: int = Field(
        default=20, description="Connessioni addizionali consentite oltre il pool"
    )

    # Upload - limite dimensione file
    # Limite alzato per gestire file SIX/XML fino a 100MB.
    max_upload_size_mb: int = 100
    allowed_file_extensions: set[str] = {".xlsx", ".xlsm", ".xls", ".six", ".xml"}

    # SECURITY: CORS limitato agli origin specifici, mai "*"
    cors_origins: list[str] | tuple[str, ...] | str | None = Field(
        default_factory=lambda: [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    cors_allow_credentials: bool = True

    # JWT / auth
    jwt_secret_key: str = Field(
        default="change-me",
        description=("Chiave segreta per la firma dei JWT - sovrascrivere in produzione"),
    )
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    access_token_expire_minutes: int = Field(
        default=15,
        description="Durata (minuti) del token di accesso - breve per ridurre l'esposizione",
    )
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 14,
        description="Durata (minuti) del refresh token a rotazione",
    )
    access_token_cookie_name: str = Field(
        default="mm_access_token",
        description="Nome cookie HttpOnly per l'access token (opzionale)",
    )
    refresh_token_cookie_name: str = Field(
        default="mm_refresh_token",
        description="Nome cookie HttpOnly per il refresh token",
    )
    auth_cookie_secure: bool = Field(
        default=True, description="Imposta cookie Secure per ambienti HTTPS"
    )
    auth_cookie_samesite: str = Field(
        default="strict", description="SameSite per cookie di autenticazione"
    )
    require_https: bool = Field(
        default=True,
        description="Richiede HTTPS per tutte le chiamate esterne (controllo a livello middleware)",
    )
    hsts_enabled: bool = Field(
        default=True, description="Abilita Strict-Transport-Security via proxy"
    )
    seed_admin_email: str | None = Field(
        default="admin@taboolo.com",
        description="Email dell'utente amministratore generato automaticamente nei deploy di test",
    )
    seed_admin_password: str | None = Field(
        default="!1235813AbCdEf$",
        description="Password iniziale per l'utente amministratore seed (solo ambienti demo/sviluppo)",
    )
    seed_admin_full_name: str = Field(
        default="Amministratore Taboolo",
        description="Nome completo associato all'utente amministratore seed",
    )

    # Rate limiting e sicurezza API
    login_rate_limit_attempts: int = Field(
        default=5, description="Numero massimo tentativi di login per finestra"
    )
    login_rate_limit_window_seconds: int = Field(
        default=300, description="Finestra in secondi per rate limit login"
    )
    import_rate_limit_per_minute: int = Field(
        default=12, description="Limite chiamate import/minuto per IP"
    )
    max_request_body_mb: int = Field(
        default=160,
        description="Limite dimensione corpo richiesta in MB (ISO A.14.2.5)",
    )

    # NLP / embedding defaults
    nlp_model_id: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    nlp_model_revision: str = "main"
    nlp_model_subfolder: str | None = None
    nlp_execution_providers: list[str] = Field(
        default_factory=lambda: ["CPUExecutionProvider"]
    )
    nlp_max_length: int = 256
    nlp_auto_export_onnx: bool = True
    nlp_onnx_opset: int = 17
    enable_price_embeddings: bool = Field(
        default=False,
        description="Calcola embedding per elenco prezzi/import (consigliato False su SQLite/CPU).",
    )
    enable_property_extraction: bool = Field(
        default=False,
        description="Esegue estrazione proprietà da descrizione listino/import.",
    )

    # WBS predictors (roBERTino)
    wbs6_model_path: Path | None = Field(
        default=None,
        description="Percorso modello roBERTino per classificazione WBS6 (label embed).",
    )
    wbs7_model_path: Path | None = Field(
        default=None,
        description="Percorso modello roBERTino per classificazione WBS7 (label embed).",
    )
    wbs_label_map_path: Path | None = Field(
        default=None,
        description="File JSON id->label per predictor WBS se non incluso nel modello HF.",
    )

    # Logging e observability
    structured_logging: bool = Field(
        default=True,
        description="Emette log JSON per integrazione con SIEM/ELK",
    )
    log_level: str = Field(default="INFO", description="Livello di log applicativo")

    model_config = SettingsConfigDict(
        env_prefix="TABOO_", env_file=".env", extra="ignore"
    )

    @property
    def effective_database_url(self) -> str:
        """Preferisce un URL Postgres fornito via env, con fallback SQLite per sviluppo."""

        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.storage_root / self.database_path}"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(
        cls,
        value: str | list[str] | tuple[str, ...] | None,
    ) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            if not value.strip():
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    @field_validator("nlp_execution_providers", mode="before")
    @classmethod
    def _split_execution_providers(
        cls, value: str | list[str] | tuple[str, ...] | None
    ) -> list[str]:
        if value is None:
            return ["CPUExecutionProvider"]
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items or ["CPUExecutionProvider"]
        sequence = list(value)
        return sequence or ["CPUExecutionProvider"]


settings = Settings()

# Assicura che la cartella storage esista (per database + file caricati)
settings.storage_root.mkdir(parents=True, exist_ok=True)
