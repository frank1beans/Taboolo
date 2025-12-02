"""Script per analizzare i PriceListItem e identificare eventuali duplicati o item orfani."""
from __future__ import annotations

import logging
from collections import defaultdict
from sqlmodel import Session, select

from app.db.session import engine
from app.db.models import PriceListItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_price_list_items() -> None:
    """Analizza i PriceListItem per identificare duplicati e statistiche."""

    with Session(engine) as session:
        logger.info("=" * 80)
        logger.info("ANALISI PRICE LIST ITEMS")
        logger.info("=" * 80)

        # Get all items
        items = session.exec(select(PriceListItem)).all()
        total = len(items)
        logger.info(f"\nTotale PriceListItem: {total}")

        if total == 0:
            logger.info("Nessun item trovato nel catalogo prezzi")
            return

        # Group by product_id
        by_product_id: dict[str, list[PriceListItem]] = defaultdict(list)
        for item in items:
            if item.product_id:
                by_product_id[item.product_id].append(item)

        # Group by item_code
        by_item_code: dict[str, list[PriceListItem]] = defaultdict(list)
        for item in items:
            if item.item_code:
                by_item_code[item.item_code].append(item)

        # Statistics
        unique_product_ids = len(by_product_id)
        unique_item_codes = len(by_item_code)
        items_without_product_id = sum(1 for item in items if not item.product_id)
        items_without_item_code = sum(1 for item in items if not item.item_code)

        logger.info(f"\n--- Statistiche ---")
        logger.info(f"  Product ID unici: {unique_product_ids}")
        logger.info(f"  Item codes unici: {unique_item_codes}")
        logger.info(f"  Item senza product_id: {items_without_product_id}")
        logger.info(f"  Item senza item_code: {items_without_item_code}")

        # Find duplicates by product_id
        duplicates_by_product = {
            pid: items_list
            for pid, items_list in by_product_id.items()
            if len(items_list) > 1
        }

        if duplicates_by_product:
            logger.warning(f"\n⚠️  Trovati {len(duplicates_by_product)} product_id duplicati:")
            for pid, items_list in sorted(duplicates_by_product.items())[:10]:
                logger.info(f"  - Product ID '{pid}': {len(items_list)} occorrenze")
                logger.info(f"    Item IDs: {[item.id for item in items_list]}")
            if len(duplicates_by_product) > 10:
                logger.info(f"    ... e altri {len(duplicates_by_product) - 10} duplicati")
        else:
            logger.info("✓ Nessun product_id duplicato")

        # Find duplicates by item_code
        duplicates_by_code = {
            code: items_list
            for code, items_list in by_item_code.items()
            if len(items_list) > 1
        }

        if duplicates_by_code:
            logger.warning(f"\n⚠️  Trovati {len(duplicates_by_code)} item_code duplicati:")
            for code, items_list in sorted(duplicates_by_code.items())[:10]:
                logger.info(f"  - Item code '{code}': {len(items_list)} occorrenze")
                logger.info(f"    Product IDs: {[item.product_id for item in items_list]}")
            if len(duplicates_by_code) > 10:
                logger.info(f"    ... e altri {len(duplicates_by_code) - 10} duplicati")
        else:
            logger.info("✓ Nessun item_code duplicato")

        # Check for items with embeddings
        items_with_embeddings = 0
        for item in items:
            metadata = item.extra_metadata or {}
            if isinstance(metadata, dict):
                nlp = metadata.get("nlp")
                if nlp:
                    items_with_embeddings += 1

        logger.info(f"\n--- Embeddings ---")
        logger.info(f"  Item con embeddings: {items_with_embeddings}")
        logger.info(f"  Item senza embeddings: {total - items_with_embeddings}")

        # Check price_lists field distribution
        items_with_price_lists = sum(1 for item in items if item.price_lists)
        logger.info(f"\n--- Price Lists ---")
        logger.info(f"  Item con price_lists: {items_with_price_lists}")
        logger.info(f"  Item senza price_lists: {total - items_with_price_lists}")

        logger.info("\n" + "=" * 80)
        logger.info("ANALISI COMPLETATA")
        logger.info("=" * 80)


if __name__ == "__main__":
    analyze_price_list_items()
