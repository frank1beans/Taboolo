"""Script per pulire PriceListItem orfani (con commessa_id non esistente)."""
from __future__ import annotations

import logging
from sqlmodel import Session, select
from sqlalchemy import text

from app.db.session import engine
from app.db.models import PriceListItem, Commessa, PriceListOffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_orphaned_pricelist_items() -> None:
    """Pulisce tutti i PriceListItem orfani (con commessa_id non valido)."""

    with Session(engine) as session:
        logger.info("=" * 80)
        logger.info("INIZIO PULIZIA PRICELIST ITEMS ORFANI")
        logger.info("=" * 80)

        # Get all valid commessa IDs
        valid_commessa_ids = set(
            session.exec(select(Commessa.id)).all()
        )
        logger.info(f"Trovate {len(valid_commessa_ids)} commesse valide nel database")

        # ====================================================================
        # 1. ANALISI PRICELIST ITEMS
        # ====================================================================
        logger.info("\n--- FASE 1: Analisi PriceListItem ---")

        # Count total items
        total_items = session.exec(select(PriceListItem)).all()
        logger.info(f"Totale PriceListItem: {len(total_items)}")

        # Find orphaned items
        orphaned_items = [
            item for item in total_items
            if item.commessa_id not in valid_commessa_ids
        ]

        if orphaned_items:
            logger.warning(f"⚠️  TROVATI {len(orphaned_items)} PRICELIST ITEMS ORFANI!")

            # Group by commessa_id for reporting
            by_commessa: dict[int, int] = {}
            for item in orphaned_items:
                by_commessa[item.commessa_id] = by_commessa.get(item.commessa_id, 0) + 1

            logger.info("PriceListItem orfani per commessa_id eliminata:")
            for comm_id, count in sorted(by_commessa.items()):
                logger.info(f"  - Commessa ID {comm_id}: {count} items")

            # Before deleting items, we need to delete related offers
            logger.info(f"\n🔍 Controllo PriceListOffer collegati...")
            orphaned_item_ids = {item.id for item in orphaned_items}

            orphaned_offers = session.exec(
                select(PriceListOffer).where(
                    PriceListOffer.price_list_item_id.in_(orphaned_item_ids)
                )
            ).all()

            if orphaned_offers:
                logger.warning(f"⚠️  Trovati {len(orphaned_offers)} PriceListOffer orfani da eliminare")
                for offer in orphaned_offers:
                    session.delete(offer)
                session.commit()
                logger.info("✅ PriceListOffer orfani eliminati")

            # Delete orphaned items
            logger.info(f"\n🗑️  Eliminazione di {len(orphaned_items)} PriceListItem orfani...")
            for item in orphaned_items:
                session.delete(item)

            session.commit()
            logger.info("✅ PriceListItem orfani eliminati con successo")
        else:
            logger.info("✓ Nessun PriceListItem orfano trovato")

        # ====================================================================
        # 2. VERIFICA FINALE
        # ====================================================================
        logger.info("\n--- FASE 2: Verifica Finale ---")

        # Verify no orphans remain
        remaining_orphaned_items = session.exec(
            text("""
                SELECT COUNT(*)
                FROM pricelistitem
                WHERE commessa_id NOT IN (SELECT id FROM commessa)
            """)
        ).scalar()

        if remaining_orphaned_items == 0:
            logger.info("✅ VERIFICA OK: Nessun PriceListItem orfano rimasto")
        else:
            logger.error(f"❌ ERRORE: Rimasti {remaining_orphaned_items} PriceListItem orfani")

        logger.info("\n" + "=" * 80)
        logger.info("PULIZIA COMPLETATA")
        logger.info("=" * 80)

        # Final statistics
        final_items_count = session.exec(select(PriceListItem)).all()
        logger.info(f"\nStatistiche finali:")
        logger.info(f"  - Commesse: {len(valid_commessa_ids)}")
        logger.info(f"  - PriceListItem: {len(final_items_count)}")
        logger.info(f"  - PriceListItem eliminati: {len(orphaned_items)}")


if __name__ == "__main__":
    cleanup_orphaned_pricelist_items()
