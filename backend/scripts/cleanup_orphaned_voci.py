"""Script per pulire voci e computi orfani (con commessa_id non esistente)."""
from __future__ import annotations

import logging
from sqlmodel import Session, select
from sqlalchemy import text

from app.db.session import engine
from app.db.models import VoceComputo, Computo, Commessa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_orphaned_records() -> None:
    """Pulisce tutti i record orfani (voci e computi senza commessa valida)."""

    with Session(engine) as session:
        logger.info("=" * 80)
        logger.info("INIZIO PULIZIA RECORD ORFANI")
        logger.info("=" * 80)

        # Get all valid commessa IDs
        valid_commessa_ids = set(
            session.exec(select(Commessa.id)).all()
        )
        logger.info(f"Trovate {len(valid_commessa_ids)} commesse valide nel database")

        # ====================================================================
        # 1. PULIZIA VOCI ORFANE
        # ====================================================================
        logger.info("\n--- FASE 1: Analisi VoceComputo ---")

        # Count total voci
        total_voci = session.exec(
            select(VoceComputo).where(VoceComputo.commessa_id.is_not(None))
        ).all()
        logger.info(f"Totale voci con commessa_id: {len(total_voci)}")

        # Find orphaned voci
        orphaned_voci = [
            voce for voce in total_voci
            if voce.commessa_id not in valid_commessa_ids
        ]

        if orphaned_voci:
            logger.warning(f"⚠️  TROVATE {len(orphaned_voci)} VOCI ORFANE!")

            # Group by commessa_id for reporting
            by_commessa: dict[int, int] = {}
            for voce in orphaned_voci:
                by_commessa[voce.commessa_id] = by_commessa.get(voce.commessa_id, 0) + 1

            logger.info("Voci orfane per commessa_id eliminata:")
            for comm_id, count in sorted(by_commessa.items()):
                logger.info(f"  - Commessa ID {comm_id}: {count} voci")

            # Delete orphaned voci
            logger.info(f"\n🗑️  Eliminazione di {len(orphaned_voci)} voci orfane...")
            for voce in orphaned_voci:
                session.delete(voce)

            session.commit()
            logger.info("✅ Voci orfane eliminate con successo")
        else:
            logger.info("✓ Nessuna voce orfana trovata")

        # ====================================================================
        # 2. PULIZIA COMPUTI ORFANI
        # ====================================================================
        logger.info("\n--- FASE 2: Analisi Computo ---")

        # Count total computi
        total_computi = session.exec(select(Computo)).all()
        logger.info(f"Totale computi: {len(total_computi)}")

        # Find orphaned computi
        orphaned_computi = [
            computo for computo in total_computi
            if computo.commessa_id not in valid_commessa_ids
        ]

        if orphaned_computi:
            logger.warning(f"⚠️  TROVATI {len(orphaned_computi)} COMPUTI ORFANI!")

            # Group by commessa_id for reporting
            by_commessa: dict[int, int] = {}
            for computo in orphaned_computi:
                by_commessa[computo.commessa_id] = by_commessa.get(computo.commessa_id, 0) + 1

            logger.info("Computi orfani per commessa_id eliminata:")
            for comm_id, count in sorted(by_commessa.items()):
                logger.info(f"  - Commessa ID {comm_id}: {count} computi")

            # Delete orphaned computi
            logger.info(f"\n🗑️  Eliminazione di {len(orphaned_computi)} computi orfani...")
            for computo in orphaned_computi:
                session.delete(computo)

            session.commit()
            logger.info("✅ Computi orfani eliminati con successo")
        else:
            logger.info("✓ Nessun computo orfano trovato")

        # ====================================================================
        # 3. VERIFICA FINALE
        # ====================================================================
        logger.info("\n--- FASE 3: Verifica Finale ---")

        # Verify no orphans remain
        remaining_orphaned_voci = session.exec(
            text("""
                SELECT COUNT(*)
                FROM vocecomputo
                WHERE commessa_id IS NOT NULL
                AND commessa_id NOT IN (SELECT id FROM commessa)
            """)
        ).scalar()

        remaining_orphaned_computi = session.exec(
            text("""
                SELECT COUNT(*)
                FROM computo
                WHERE commessa_id NOT IN (SELECT id FROM commessa)
            """)
        ).scalar()

        if remaining_orphaned_voci == 0 and remaining_orphaned_computi == 0:
            logger.info("✅ VERIFICA OK: Nessun record orfano rimasto")
        else:
            logger.error(f"❌ ERRORE: Rimasti {remaining_orphaned_voci} voci e {remaining_orphaned_computi} computi orfani")

        logger.info("\n" + "=" * 80)
        logger.info("PULIZIA COMPLETATA")
        logger.info("=" * 80)

        # Final statistics
        final_voci_count = session.exec(select(VoceComputo)).all()
        final_computi_count = session.exec(select(Computo)).all()
        logger.info(f"\nStatistiche finali:")
        logger.info(f"  - Commesse: {len(valid_commessa_ids)}")
        logger.info(f"  - Computi: {len(final_computi_count)}")
        logger.info(f"  - Voci: {len(final_voci_count)}")


if __name__ == "__main__":
    cleanup_orphaned_records()
