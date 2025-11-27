"""Global settings models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SettingsBase(SQLModel):
    """Base model per settings globali dell'applicazione."""
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
    """Settings globali salvati nel database."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SettingsRead(SettingsBase):
    """Schema di lettura per Settings."""
    id: int
    created_at: datetime
    updated_at: datetime
