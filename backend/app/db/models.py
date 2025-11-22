from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, UniqueConstraint
from datetime import datetime


class ComputoTipo(str, Enum):
    progetto = "progetto"
    ritorno = "ritorno"


class CommessaStato(str, Enum):
    setup = "setup"
    in_corso = "in_corso"
    chiusa = "chiusa"


class UserRole(str, Enum):
    admin = "admin"
    project_manager = "project_manager"
    computista = "computista"
    viewer = "viewer"


class User(SQLModel, table=True):
    __tablename__ = "app_user"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.viewer)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", unique=True, index=True)
    company: Optional[str] = None
    language: str = Field(default="it-IT")
    settings: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="app_user.id")
    action: str
    method: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    payload_hash: Optional[str] = None
    outcome: Optional[str] = Field(
        default=None, description="success|failure in base alle risposte HTTP"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id")
    token_fingerprint: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked: bool = Field(default=False)
    replaced_by_id: Optional[int] = Field(default=None, foreign_key="refresh_token.id")


class CommessaBase(SQLModel):
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato = Field(
        default=CommessaStato.setup,
        description="Stato operativo della commessa (setup/in_corso/chiusa)",
    )


class Commessa(CommessaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommessaRead(CommessaBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ComputoBase(SQLModel):
    nome: str
    tipo: ComputoTipo
    impresa: Optional[str] = None
    file_nome: Optional[str] = None
    file_percorso: Optional[str] = None
    round_number: Optional[int] = Field(default=None)
    importo_totale: Optional[float] = None
    delta_vs_progetto: Optional[float] = None
    percentuale_delta: Optional[float] = None
    note: Optional[str] = None
    matching_report: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Dettaglio match import ritorni",
    )


class Computo(ComputoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ComputoRead(ComputoBase):
    id: int
    commessa_id: int
    created_at: datetime
    updated_at: datetime


class VoceBase(SQLModel):
    progressivo: Optional[int] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    ordine: int = Field(default=0)
    wbs_1_code: Optional[str] = None
    wbs_1_description: Optional[str] = None
    wbs_2_code: Optional[str] = None
    wbs_2_description: Optional[str] = None
    wbs_3_code: Optional[str] = None
    wbs_3_description: Optional[str] = None
    wbs_4_code: Optional[str] = None
    wbs_4_description: Optional[str] = None
    wbs_5_code: Optional[str] = None
    wbs_5_description: Optional[str] = None
    wbs_6_code: Optional[str] = None
    wbs_6_description: Optional[str] = None
    wbs_7_code: Optional[str] = None
    wbs_7_description: Optional[str] = None


class VoceComputo(VoceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(default=None, foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    computo_id: int = Field(foreign_key="computo.id")
    global_code: Optional[str] = Field(default=None, index=True)
    extra_metadata: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class VoceRead(VoceBase):
    id: int
    computo_id: int


class PriceListItem(SQLModel, table=True):
    """Voce dell'elenco prezzi importata da STR Vision, arricchita con metadati."""

    __tablename__ = "price_list_item"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id",
            "product_id",
            name="uq_price_list_item_commessa_product",
        ),
        UniqueConstraint(
            "global_code",
            name="uq_price_list_item_global_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    commessa_code: str = Field(index=True)
    product_id: str = Field(description="Identificativo originale del prodotto STR Vision")
    global_code: str = Field(
        description="Codice commessa+prodotto per vista multicommessa", index=True
    )
    item_code: str = Field(description="Codice visualizzato nel prezzario", index=True)
    item_description: Optional[str] = Field(default=None)
    unit_id: Optional[str] = Field(default=None)
    unit_label: Optional[str] = Field(default=None)
    wbs6_code: Optional[str] = Field(default=None)
    wbs6_description: Optional[str] = Field(default=None)
    wbs7_code: Optional[str] = Field(default=None)
    wbs7_description: Optional[str] = Field(default=None)
    price_lists: Optional[dict[str, float]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    extra_metadata: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    source_file: Optional[str] = Field(default=None)
    preventivo_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PropertyLexicon(SQLModel, table=True):
    """Dizionario gestibile via UI per brand/materiali/modelli/keyword/regex."""

    __tablename__ = "property_lexicon"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(description="brand|material|model|keyword|regex|custom")
    canonical: str = Field(description="Valore canonico normalizzato")
    synonyms: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    categories: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    details: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PropertyPattern(SQLModel, table=True):
    """Pattern o regex aggiuntivi per una proprietà specifica."""

    __tablename__ = "property_pattern"

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: Optional[str] = Field(default=None, index=True)
    property_id: Optional[str] = Field(default=None, index=True)
    pattern: str = Field(description="Regex o template da applicare")
    context_keywords: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    priority: int = Field(default=0, description="Priorità di applicazione (più alto = prima)")
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PropertyOverride(SQLModel, table=True):
    """Override manuali per le proprietà estratte di una voce di elenco prezzi."""

    __tablename__ = "property_override"

    id: Optional[int] = Field(default=None, primary_key=True)
    price_list_item_id: int = Field(foreign_key="price_list_item.id", index=True)
    category_id: Optional[str] = Field(default=None, index=True)
    properties: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    source: str = Field(default="manual")
    author: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PropertyFeedback(SQLModel, table=True):
    """Feedback puntuali per training futuro (span opzionale)."""

    __tablename__ = "property_feedback"

    id: Optional[int] = Field(default=None, primary_key=True)
    price_list_item_id: int = Field(foreign_key="price_list_item.id", index=True)
    category_id: Optional[str] = Field(default=None, index=True)
    property_id: Optional[str] = Field(default=None, index=True)
    value: Optional[str] = Field(default=None)
    span_start: Optional[int] = Field(default=None)
    span_end: Optional[int] = Field(default=None)
    note: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    preventivo_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PriceListOffer(SQLModel, table=True):
    """Prezzi offerti dalle imprese per singola voce di elenco prezzi."""

    __tablename__ = "price_list_offer"
    __table_args__ = (
        UniqueConstraint(
            "price_list_item_id",
            "computo_id",
            name="uq_price_list_offer_item_computo",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    price_list_item_id: int = Field(foreign_key="price_list_item.id")
    commessa_id: int = Field(foreign_key="commessa.id")
    computo_id: int = Field(foreign_key="computo.id")
    impresa_id: Optional[int] = Field(default=None, foreign_key="impresa.id")
    impresa_label: Optional[str] = None
    round_number: Optional[int] = None
    prezzo_unitario: float = Field(description="Prezzo dichiarato dall'impresa")
    quantita: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SettingsBase(SQLModel):
    delta_minimo_critico: float = -30000.0
    delta_massimo_critico: float = 1000.0
    percentuale_cme_alto: float = 25.0
    percentuale_cme_basso: float = 50.0
    criticita_media_percent: float = 25.0
    criticita_alta_percent: float = 50.0
    nlp_model_id: str = Field(
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        description="Modello SentenceTransformer selezionato per gli embedding",
    )
    nlp_batch_size: int = Field(
        default=32,
        description="Numero di elementi processati per batch durante il calcolo degli embedding",
    )
    nlp_max_length: int = Field(
        default=256,
        description="Lunghezza massima del testo passato al modello NLP",
    )
    nlp_embeddings_model_id: Optional[str] = Field(
        default=None,
        description="Ultimo modello utilizzato per rigenerare gli embedding salvati",
    )


class Settings(SettingsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SettingsRead(SettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ImportConfigBase(SQLModel):
    """Configurazione salvata per import ritorni di gara."""
    nome: str = Field(description="Nome descrittivo della configurazione (es: 'Formato Impresa XYZ')")
    impresa: Optional[str] = Field(default=None, description="Impresa associata (opzionale)")
    sheet_name: Optional[str] = Field(default=None, description="Nome del foglio Excel")
    code_columns: Optional[str] = Field(default=None, description="Colonne codice (es: 'A,B')")
    description_columns: Optional[str] = Field(default=None, description="Colonne descrizione")
    price_column: Optional[str] = Field(default=None, description="Colonna prezzo unitario")
    quantity_column: Optional[str] = Field(default=None, description="Colonna quantità dichiarata dall'impresa")
    note: Optional[str] = Field(default=None, description="Note sulla configurazione")


class ImportConfig(ImportConfigBase, table=True):
    """Configurazione import salvata nel database."""
    __tablename__ = "import_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(default=None, foreign_key="commessa.id", description="Commessa associata (null = globale)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ImportConfigRead(ImportConfigBase):
    id: int
    commessa_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class CommessaPreferencesBase(SQLModel):
    """Preferenze e impostazioni specifiche per la commessa."""
    selected_preventivo_id: Optional[str] = Field(
        default=None,
        description="ID del preventivo STR Vision selezionato come primario"
    )
    selected_price_list_id: Optional[str] = Field(
        default=None,
        description="ID del listino prezzi selezionato come primario"
    )
    default_wbs_view: Optional[str] = Field(
        default=None,
        description="Vista WBS predefinita (spaziale/wbs6/wbs7)"
    )
    custom_settings: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Altre impostazioni personalizzate in formato JSON"
    )


class CommessaPreferences(CommessaPreferencesBase, table=True):
    """Tabella preferenze commessa."""
    __tablename__ = "commessa_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id", unique=True, description="Commessa di riferimento")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommessaPreferencesRead(CommessaPreferencesBase):
    id: int
    commessa_id: int
    created_at: datetime
    updated_at: datetime
