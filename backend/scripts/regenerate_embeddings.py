"""Script per rigenerare gli embedding semantici per tutte le voci del price catalog."""
from __future__ import annotations

import logging
from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import engine
from app.db.models import PriceListItem, Settings
from app.services.nlp import semantic_embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_embeddings() -> None:
    """Rigenera gli embedding per tutte le voci del price catalog."""
    if not semantic_embedding_service.is_available():
        logger.error("Servizio embedding semantici non disponibile. Installa le dipendenze NLP.")
        return

    with Session(engine) as session:
        settings = session.exec(select(Settings)).first()
        if settings:
            semantic_embedding_service.configure(
                model_id=settings.nlp_model_id,
                batch_size=settings.nlp_batch_size,
                max_length=settings.nlp_max_length,
            )
        # Fetch all price list items
        items = session.exec(select(PriceListItem)).all()
        total = len(items)
        logger.info(f"Trovate {total} voci nel catalogo prezzi.")

        updated = 0
        skipped = 0
        errors = 0

        for idx, item in enumerate(items, 1):
            if idx % 100 == 0:
                logger.info(f"Processate {idx}/{total} voci...")

            # Prepare entry dict for embedding
            metadata = item.extra_metadata or {}
            price_list_labels = {}
            preferred_lists = []
            if isinstance(metadata, dict):
                labels = metadata.get("price_list_labels")
                if isinstance(labels, dict):
                    price_list_labels = labels
                pref = metadata.get("preferred_price_lists")
                if isinstance(pref, list):
                    preferred_lists = pref

            entry = {
                "item_code": item.item_code,
                "code": item.item_code,
                "product_id": item.product_id,
                "item_description": item.item_description,
                "description": item.item_description,
                "wbs6_code": item.wbs6_code,
                "wbs6_description": item.wbs6_description,
                "wbs7_code": item.wbs7_code,
                "wbs7_description": item.wbs7_description,
                "price_lists": item.price_lists,
                "price_list_labels": price_list_labels,
                "preferred_price_lists": preferred_lists,
            }

            try:
                embedding_metadata = semantic_embedding_service.prepare_price_list_metadata(entry)
                if not embedding_metadata:
                    skipped += 1
                    continue

                # Update metadata
                metadata = item.extra_metadata or {}
                if not isinstance(metadata, dict):
                    metadata = {}

                metadata.setdefault("nlp", {})[semantic_embedding_service.metadata_slot] = (
                    embedding_metadata
                )
                item.extra_metadata = metadata
                # Mark the field as modified so SQLAlchemy tracks the change
                flag_modified(item, "extra_metadata")
                session.add(item)
                updated += 1

            except Exception as exc:
                logger.error(f"Errore per item {item.id} ({item.item_code}): {exc}")
                errors += 1

        # Commit changes
        session.commit()
        if settings:
            settings.nlp_embeddings_model_id = semantic_embedding_service.model_id
            session.add(settings)
            session.commit()
        logger.info(
            f"Completato! Aggiornate: {updated}, Saltate: {skipped}, Errori: {errors}"
        )


if __name__ == "__main__":
    regenerate_embeddings()
