"""Commesse domain models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class CommessaStato(str, Enum):
    """Stati possibili per una commessa."""
    setup = "setup"
    in_corso = "in_corso"
    chiusa = "chiusa"


class CommessaBase(SQLModel):
    """Base model per Commessa con campi comuni."""
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
    """Commessa (progetto) - entità principale del dominio."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommessaRead(CommessaBase):
    """Schema di lettura per Commessa."""
    id: int
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
    """Schema di lettura per CommessaPreferences."""
    id: int
    commessa_id: int
    created_at: datetime
    updated_at: datetime
