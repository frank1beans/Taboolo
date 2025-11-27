"""Catalog domain models (price lists, products, properties)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, UniqueConstraint


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
    preventivo_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
