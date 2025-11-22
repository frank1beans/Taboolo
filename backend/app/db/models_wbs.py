from __future__ import annotations

"""
Modelli relazionali per la gestione WBS.

La WBS è spezzata in tre livelli:
* WbsSpaziale: nodi dal livello 1 al 5 (gerarchia spaziale per commessa)
* Wbs6: nodo analitico principale (codice A### obbligatorio)
* Wbs7: nodo opzionale per ulteriori sottocodici (A###.###)

Le voci analitiche e i prezzi (progetto e offerte) fanno sempre riferimento
alla WBS6 (chiave analitica di aggregazione) e, se presente, alla WBS7.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class WbsSpaziale(SQLModel, table=True):
    """Nodo spaziale della WBS (livelli 1-5) normalizzato per commessa."""

    __tablename__ = "wbs_spaziale"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id",
            "level",
            "code",
            name="uq_wbs_spaziale_commessa_level_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="wbs_spaziale.id")
    level: int = Field(description="Livello WBS (1-5)")
    code: str = Field(description="Codice del nodo (es. P00)")
    description: Optional[str] = Field(default=None, description="Descrizione nodo")
    importo_totale: Optional[float] = Field(
        default=None,
        description="Importo aggregato opzionale per il nodo",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Wbs6(SQLModel, table=True):
    """Nodo analitico WBS6 (codice A### obbligatorio)."""

    __tablename__ = "wbs6"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id",
            "code",
            name="uq_wbs6_commessa_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    wbs_spaziale_id: Optional[int] = Field(
        default=None,
        foreign_key="wbs_spaziale.id",
        description="Nodo spaziale foglia associato (livello 5)",
    )
    code: str = Field(description="Codice WBS6 (formato A###)")
    description: str = Field(description="Descrizione sintetica della WBS6")
    label: str = Field(description="Etichetta normalizzata (CODE - DESCRIPTION)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Wbs7(SQLModel, table=True):
    """Nodo opzionale WBS7 (sotto-articolazione della WBS6)."""

    __tablename__ = "wbs7"
    __table_args__ = (
        UniqueConstraint(
            "wbs6_id",
            "code",
            name="uq_wbs7_wbs6_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(
        foreign_key="commessa.id",
        description="Commessa di riferimento (per filtri diretti)",
    )
    wbs6_id: int = Field(foreign_key="wbs6.id")
    code: Optional[str] = Field(
        default=None,
        description="Codice WBS7 (A###.###) opzionale",
    )
    description: Optional[str] = Field(
        default=None,
        description="Descrizione aggiuntiva della voce",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WbsVisibilityKind(str, Enum):
    spaziale = "spaziale"
    wbs6 = "wbs6"
    wbs7 = "wbs7"


class WbsVisibility(SQLModel, table=True):
    """Preferenze di visibilità per i raggruppatori WBS (livelli 1-7)."""

    __tablename__ = "wbs_visibility"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id",
            "kind",
            "node_id",
            name="uq_wbs_visibility_commessa_node",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    kind: WbsVisibilityKind = Field(description="Tipo di nodo (spaziale/wbs6/wbs7)")
    node_id: int = Field(description="Identificativo del nodo di riferimento")
    hidden: bool = Field(
        default=False,
        description="True se il nodo va nascosto nelle viste",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Impresa(SQLModel, table=True):
    """Anagrafica imprese normalizzata per offerte e round."""

    __tablename__ = "impresa"
    __table_args__ = (
        UniqueConstraint(
            "normalized_label",
            name="uq_impresa_normalized_label",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(description="Nome visualizzato")
    normalized_label: str = Field(description="Nome normalizzato per confronti")
    note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Voce(SQLModel, table=True):
    """
    Voce analitica normalizzata.

    Ogni voce appartiene ad una commessa e deve avere sempre una WBS6
    di riferimento. La WBS7 è opzionale (se esiste nel computo originale).
    """

    __tablename__ = "voce"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id",
            "wbs6_id",
            "codice",
            "ordine",
            name="uq_voce_commessa_wbs6_codice_ordine",
        ),
        UniqueConstraint(
            "legacy_vocecomputo_id",
            name="uq_voce_legacy",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    wbs6_id: int = Field(foreign_key="wbs6.id")
    wbs7_id: Optional[int] = Field(default=None, foreign_key="wbs7.id")
    legacy_vocecomputo_id: Optional[int] = Field(
        default=None,
        foreign_key="vocecomputo.id",
        description="Riferimento alla voce legacy per compatibilità",
    )
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    note: Optional[str] = None
    ordine: int = Field(default=0)
    price_list_item_id: Optional[int] = Field(
        default=None,
        foreign_key="price_list_item.id",
        description="Voce di elenco prezzi di riferimento",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoceProgetto(SQLModel, table=True):
    """Quantità e prezzi di progetto associati ad una voce normalizzata."""

    __tablename__ = "voce_progetto"
    __table_args__ = (
        UniqueConstraint(
            "voce_id",
            name="uq_voce_progetto_voce",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    voce_id: int = Field(foreign_key="voce.id")
    computo_id: int = Field(foreign_key="computo.id")
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoceOfferta(SQLModel, table=True):
    """
    Importi offerta delle imprese per singola voce.

    Ogni riga identifica una voce, un computo (ritorno), un round e un'impresa.
    """

    __tablename__ = "voce_offerta"
    __table_args__ = (
        UniqueConstraint(
            "voce_id",
            "computo_id",
            "impresa_id",
            name="uq_voce_offerta_voce_computo_impresa",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    voce_id: int = Field(foreign_key="voce.id")
    computo_id: int = Field(foreign_key="computo.id")
    impresa_id: int = Field(foreign_key="impresa.id")
    round_number: Optional[int] = Field(default=None)
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
