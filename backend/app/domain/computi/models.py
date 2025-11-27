"""Computi domain models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ComputoTipo(str, Enum):
    """Tipo di computo metrico."""
    progetto = "progetto"
    ritorno = "ritorno"


class ComputoBase(SQLModel):
    """Base model per Computo con campi comuni."""
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
    """Computo metrico - elenco prezzi e quantità per una commessa."""
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ComputoRead(ComputoBase):
    """Schema di lettura per Computo."""
    id: int
    commessa_id: int
    created_at: datetime
    updated_at: datetime


class VoceBase(SQLModel):
    """Base model per singola voce di computo."""
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
    """Singola voce (riga) di un computo metrico."""
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(default=None, foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    computo_id: int = Field(foreign_key="computo.id")
    global_code: Optional[str] = Field(default=None, index=True)
    extra_metadata: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class VoceRead(VoceBase):
    """Schema di lettura per VoceComputo."""
    id: int
    computo_id: int


class ImportConfigBase(SQLModel):
    """Configurazione salvata per import ritorni di gara."""
    nome: str = Field(description="Nome descrittivo della configurazione (es: 'Formato Impresa XYZ')")
    impresa: Optional[str] = Field(default=None, description="Impresa associata (opzionale)")
    sheet_name: Optional[str] = Field(default=None, description="Nome del foglio Excel")
    code_columns: Optional[str] = Field(default=None, description="Colonne codice (es: 'A,B')")
    description_columns: Optional[str] = Field(default=None, description="Colonne descrizione")
    price_column: Optional[str] = Field(default=None, description="Colonna prezzo unitario")
    quantity_column: Optional[str] = Field(default=None, description="Colonna quantità dichiarata dall'impresa")
    wbs_columns: Optional[str] = Field(default=None, description="Colonne WBS per import (es: 'F,G,H')")
    note: Optional[str] = Field(default=None, description="Note sulla configurazione")


class ImportConfig(ImportConfigBase, table=True):
    """Configurazione import salvata nel database."""
    __tablename__ = "import_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(default=None, foreign_key="commessa.id", description="Commessa associata (null = globale)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ImportConfigRead(ImportConfigBase):
    """Schema di lettura per ImportConfig."""
    id: int
    commessa_id: Optional[int]
    created_at: datetime
    updated_at: datetime
