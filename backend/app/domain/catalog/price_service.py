from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any, Iterable, Sequence

from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.db.models import Commessa, PriceListItem


logger = logging.getLogger(__name__)


class PriceCatalogService:
    """Gestisce la persistenza delle voci di elenco prezzi multi-commessa."""

    def __init__(
        self,
        embedding_service=None,
        property_extractor=None,
    ) -> None:
        self.embedding_service = embedding_service
        self.property_extractor = property_extractor

    def replace_catalog(
        self,
        session: Session,
        commessa: Commessa,
        entries: Iterable[dict[str, Any]],
        source_file: str | None,
        preventivo_id: str | None,
        price_list_labels: dict[str, str],
        preferred_lists: Sequence[str],
        *,
        compute_embeddings: bool | None = None,
        extract_properties: bool | None = None,
        base_list_keywords: Sequence[str] = ("base",),
    ) -> None:
        session.exec(
            PriceListItem.__table__.delete().where(PriceListItem.commessa_id == commessa.id)
        )

        commessa_code = commessa.codice or f"commessa-{commessa.id}"
        commessa_tag = self._build_commessa_tag(commessa.id, commessa_code)
        preferred_lists_payload = list(preferred_lists)
        models: list[PriceListItem] = []
        normalized_base_lists = {
            list_id
            for list_id, label in price_list_labels.items()
            if any(keyword in (label or "").lower() for keyword in base_list_keywords)
            or any(keyword in (list_id or "").lower() for keyword in base_list_keywords)
        }

        seen_global_codes: set[str] = set()

        for entry in entries:
            product_id = entry.get("product_id")
            if not product_id:
                continue
            item_code = (entry.get("code") or product_id).strip()
            if not item_code:
                item_code = product_id
            global_code = self._build_global_code(commessa_tag, item_code, product_id)
            if global_code in seen_global_codes:
                logger.warning(
                    "Duplicate price item skipped for commessa=%s code=%s product=%s",
                    commessa_code,
                    item_code,
                    product_id,
                )
                continue
            seen_global_codes.add(global_code)
            price_lists = entry.get("price_lists")
            if price_lists:
                base_price_lists = {
                    list_id: value
                    for list_id, value in price_lists.items()
                    if list_id in normalized_base_lists
                }
                effective_price_lists = base_price_lists or price_lists
            else:
                effective_price_lists = {}
            metadata = {
                "source": "six",
                # RIMOSSO: "price_lists" per evitare duplicazione con il campo diretto
                "price_list_labels": {
                    list_id: price_list_labels.get(list_id)
                    for list_id in effective_price_lists.keys()
                    if list_id in price_list_labels
                },
                "preferred_price_lists": preferred_lists_payload,
            }

            do_extract = extract_properties if extract_properties is not None else settings.enable_property_extraction
            if do_extract and self.property_extractor:
                try:
                    if callable(getattr(self.property_extractor, "extract_properties", None)):
                        extracted = self.property_extractor.extract_properties(entry, session=session)
                    elif callable(self.property_extractor):
                        extracted = self._call_property_extractor(entry, session)
                    else:
                        extracted = None
                    if extracted:
                        metadata["extracted_properties"] = extracted
                except Exception as exc:  # pragma: no cover - robustezza
                    logger.exception("Errore nell'estrazione proprietà da descrizione: %s", exc)

            do_embeddings = compute_embeddings if compute_embeddings is not None else settings.enable_price_embeddings
            service = self.embedding_service if do_embeddings else None
            if service is not None:
                # Usa effective_price_lists per generare embedding consistenti
                embedding_input = {
                    **entry,
                    "price_lists": effective_price_lists,  # Sostituisci con listini filtrati
                    "price_list_labels": metadata["price_list_labels"],
                    "preferred_price_lists": preferred_lists_payload,
                }
                embedding_metadata = self._prepare_embedding_metadata(embedding_input)
                if embedding_metadata:
                    metadata.setdefault("nlp", {})[service.metadata_slot] = embedding_metadata
            models.append(
                PriceListItem(
                    commessa_id=commessa.id,
                    commessa_code=commessa_code,
                    product_id=product_id,
                    global_code=global_code,
                    item_code=item_code,
                    item_description=entry.get("description"),
                    unit_id=entry.get("unit_id"),
                    unit_label=entry.get("unit_label"),
                    wbs6_code=entry.get("wbs6_code"),
                    wbs6_description=entry.get("wbs6_description"),
                    wbs7_code=entry.get("wbs7_code"),
                    wbs7_description=entry.get("wbs7_description"),
                    price_lists=effective_price_lists,
                    extra_metadata=metadata,
                    source_file=source_file,
                    preventivo_id=preventivo_id,
                )
            )

        if models:
            session.add_all(models)

    def _call_property_extractor(self, entry: dict[str, Any], session: Session) -> Any:
        """
        Esegue l'estrazione proprietà con retry in caso di lock su SQLite.

        Se dopo alcuni tentativi il DB è ancora locked, salta l'estrazione per non interrompere l'import.
        """
        delays = (0.1, 0.3, 0.5)
        for attempt, delay in enumerate(delays, start=1):
            try:
                return self.property_extractor(entry, session)  # preferisce sessione se supportata
            except TypeError:
                # Fallback a chiamata senza sessione
                return self.property_extractor(entry)
            except OperationalError as exc:
                if isinstance(exc.orig, sqlite3.OperationalError) and "database is locked" in str(exc.orig):
                    logger.warning(
                        "Property extractor retry %s/%s per lock SQLite", attempt, len(delays)
                    )
                    time.sleep(delay)
                    continue
                raise
        logger.warning("Property extractor disabilitato per lock persistente: salto estrazione")
        return None

    def _prepare_embedding_metadata(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        if not self.embedding_service:
            return None
        try:
            return self.embedding_service.prepare_price_list_metadata(entry)
        except RuntimeError as exc:
            logger.warning("Ricerca semantica disabilitata: %s", exc)
            self.embedding_service = None
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("Errore nel calcolo embedding semantici: %s", exc)
        return None

    @staticmethod
    def _build_commessa_tag(commessa_id: int | None, commessa_code: str | None) -> str:
        code = (commessa_code or "commessa").strip() or "commessa"
        identifier = commessa_id or 0
        return f"{identifier}::{code}"

    @staticmethod
    def _build_global_code(commessa_tag: str, item_code: str, product_id: str) -> str:
        normalized_item = item_code.strip() or "item"
        normalized_product = product_id.strip() or normalized_item
        return f"{commessa_tag}::{normalized_item}::prd::{normalized_product}"


from app.core.config import settings
from app.services.nlp.embedding_service import semantic_embedding_service
from app.services.nlp.property_extraction import extract_properties_auto


price_catalog_service = PriceCatalogService(
    embedding_service=semantic_embedding_service if settings.enable_price_embeddings else None,
    property_extractor=extract_properties_auto if settings.enable_property_extraction else None,
)
