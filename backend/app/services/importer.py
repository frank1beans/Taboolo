from __future__ import annotations

from pathlib import Path
from typing import Sequence

from sqlmodel import Session

from app.db.models import Computo, VoceComputo
from app.services.importers.lc_import_service import LcImportService
from app.services.importers.mc_import_service import McImportService


class ImportService:
    """
    Facade unificato per import LC e MC con routing automatico.

    Delega ai servizi dedicati basandosi sulla modalità:
    - LC (Lista Lavorazioni): solo prezzi → LcImportService
    - MC (Computo Metrico): progressivi + quantità + prezzi → McImportService
    """

    def __init__(self):
        self.lc_service = LcImportService()
        self.mc_service = McImportService()

    def import_computo_ritorno(
        self,
        *,
        session: Session,
        commessa_id: int,
        impresa: str,
        file: Path,
        originale_nome: str | None,
        round_number: int | None = None,
        round_mode: str = "auto",
        sheet_name: str | None = None,
        sheet_code_columns: Sequence[str] | None = None,
        sheet_description_columns: Sequence[str] | None = None,
        sheet_price_column: str | None = None,
        sheet_quantity_column: str | None = None,
        sheet_progressive_column: str | None = None,
        mode: str | None = None,
    ) -> Computo:
        """
        Importa un ritorno gara (auto-detect LC vs MC o modalità esplicita).

        Routing:
        - Se mode='lc' O sheet_price_column presente → usa LcImportService
        - Altrimenti → usa McImportService

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            impresa: Nome impresa
            file: Path file Excel
            originale_nome: Nome originale file
            round_number: Numero round (opzionale)
            round_mode: 'auto', 'new', o 'replace'
            sheet_name: Nome foglio Excel
            sheet_code_columns: Colonne codice (per LC)
            sheet_description_columns: Colonne descrizione (per LC)
            sheet_price_column: Colonna prezzo (trigger LC)
            sheet_quantity_column: Colonna quantità
            sheet_progressive_column: Colonna progressivo
            mode: 'lc' o 'mc' (opzionale, auto-detect se None)

        Returns:
            Computo di tipo 'ritorno'
        """
        # Auto-detect modalità
        resolved_mode = (mode or "").strip().lower() if mode else None

        # Determina se è LC o MC
        if resolved_mode == "lc" or (not resolved_mode and sheet_price_column):
            # Modalità LC: solo prezzi
            return self.lc_service.import_lc(
                session=session,
                commessa_id=commessa_id,
                impresa=impresa,
                file=file,
                originale_nome=originale_nome,
                round_number=round_number,
                round_mode=round_mode,
                sheet_name=sheet_name,
                sheet_code_columns=sheet_code_columns,
                sheet_description_columns=sheet_description_columns,
                sheet_price_column=sheet_price_column,
                sheet_quantity_column=sheet_quantity_column,
                sheet_progressive_column=sheet_progressive_column,
            )
        else:
            # Modalità MC: progressivi + quantità + prezzi
            return self.mc_service.import_mc(
                session=session,
                commessa_id=commessa_id,
                impresa=impresa,
                file=file,
                originale_nome=originale_nome,
                round_number=round_number,
                round_mode=round_mode,
                sheet_name=sheet_name,
                sheet_price_column=sheet_price_column,
                sheet_quantity_column=sheet_quantity_column,
            )

    def import_computo_progetto(
        self,
        *,
        session: Session,
        commessa_id: int,
        file: Path,
        originale_nome: str | None,
    ) -> Computo:
        """
        Importa un computo metrico (MC) completo da file Excel/SIX.

        Delega a McImportService.

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            file: Path file Excel/SIX
            originale_nome: Nome originale file

        Returns:
            Computo di tipo 'progetto'
        """
        return self.mc_service.import_computo_metrico(
            session=session,
            commessa_id=commessa_id,
            file=file,
            originale_nome=originale_nome,
        )

    def import_batch_single_file(
        self,
        *,
        session: Session,
        commessa_id: int,
        file: Path,
        originale_nome: str | None,
        imprese_config: Sequence[dict],
        sheet_name: str | None = None,
        sheet_code_columns: Sequence[str] | None = None,
        sheet_description_columns: Sequence[str] | None = None,
        sheet_progressive_column: str | None = None,
        mode: str | None = None,
    ) -> dict:
        """
        Import batch da singolo file Excel con colonne multiple per imprese diverse.

        Importa ritorni gara per più imprese partendo da un unico file che contiene:
        - Colonne comuni: codice, descrizione, progressivo
        - Colonne specifiche per impresa: prezzo unitario e quantità (opzionale)

        Ogni impresa viene processata indipendentemente con transazioni separate.
        Se un'impresa fallisce (es. colonne vuote), le altre vengono comunque processate.

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            file: Path file Excel
            originale_nome: Nome originale file
            imprese_config: Lista configurazioni imprese, ogni dict contiene:
                - nome_impresa: str - Nome impresa
                - colonna_prezzo: str - Colonna prezzo (es. "E")
                - colonna_quantita: str | None - Colonna quantità opzionale (es. "D")
                - round_number: int | None - Numero round
                - round_mode: str - Modalità round ("auto", "new", "replace")
            sheet_name: Nome foglio Excel
            sheet_code_columns: Colonne codice
            sheet_description_columns: Colonne descrizione
            sheet_progressive_column: Colonna progressivo
            mode: 'lc' o 'mc'

        Returns:
            Report con struttura:
            {
                "success": ["Impresa A", "Impresa B"],
                "failed": [{"impresa": "Impresa C", "error": "...", "details": "..."}],
                "computi": {"Impresa A": <Computo>, "Impresa B": <Computo>},
                "total": 3,
                "success_count": 2,
                "failed_count": 1
            }
        """
        from typing import Any
        from sqlmodel import select
        from app.db.models import Computo, ComputoTipo, VoceComputo
        import logging

        logger = logging.getLogger(__name__)

        if not imprese_config:
            raise ValueError("imprese_config non può essere vuota")

        resolved_mode = (mode or "").strip().lower()
        if resolved_mode and resolved_mode not in {"lc", "mc"}:
            raise ValueError("Modalità import non valida. Usa 'lc' oppure 'mc'.")

        results: dict[str, Any] = {
            "success": [],
            "failed": [],
            "computi": {},
            "total": len(imprese_config),
            "success_count": 0,
            "failed_count": 0,
        }

        # Recupera computo di progetto e relative voci una sola volta per riuso
        progetto = session.exec(
            select(Computo)
            .where(
                Computo.commessa_id == commessa_id,
                Computo.tipo == ComputoTipo.progetto,
            )
            .order_by(Computo.created_at.desc())
        ).first()
        if not progetto:
            raise ValueError("Carica prima un computo metrico (MC) per la commessa")

        progetto_voci = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == progetto.id)
            .order_by(VoceComputo.ordine)
        ).all()
        if not progetto_voci:
            raise ValueError("Il computo metrico (MC) non contiene voci importabili")

        for idx, config in enumerate(imprese_config):
            # Validazione configurazione
            nome_impresa = config.get("nome_impresa")
            if not nome_impresa:
                results["failed"].append({
                    "impresa": f"<config #{idx + 1}>",
                    "error": "Campo 'nome_impresa' mancante",
                    "details": str(config)
                })
                results["failed_count"] += 1
                continue

            colonna_prezzo = config.get("colonna_prezzo")
            colonna_quantita = config.get("colonna_quantita")
            round_number = config.get("round_number")
            round_mode = config.get("round_mode", "auto")

            # Log inizio import per questa impresa
            logger.info(
                f"Import batch - Inizio processing impresa '{nome_impresa}' "
                f"(#{idx + 1}/{len(imprese_config)})"
            )

            try:
                # Usa import_computo_ritorno che fa routing automatico LC/MC
                computo = self.import_computo_ritorno(
                    session=session,
                    commessa_id=commessa_id,
                    impresa=nome_impresa,
                    file=file,
                    originale_nome=originale_nome,
                    round_number=round_number,
                    round_mode=round_mode,
                    sheet_name=sheet_name,
                    sheet_code_columns=sheet_code_columns,
                    sheet_description_columns=sheet_description_columns,
                    sheet_progressive_column=sheet_progressive_column,
                    mode=resolved_mode or None,
                    sheet_price_column=colonna_prezzo,
                    sheet_quantity_column=colonna_quantita,
                )

                # Commit separato per ogni impresa (importazione robusta)
                session.commit()
                session.refresh(computo)

                # Successo
                results["success"].append(nome_impresa)
                results["computi"][nome_impresa] = computo
                results["success_count"] += 1

                logger.info(
                    f"Import batch - Completato con successo impresa '{nome_impresa}' "
                    f"(Computo ID: {computo.id})"
                )

            except Exception as e:
                # Rollback per questa impresa, ma continua con le altre
                session.rollback()

                error_msg = str(e)
                error_type = type(e).__name__

                results["failed"].append({
                    "impresa": nome_impresa,
                    "error": error_msg,
                    "error_type": error_type,
                    "config": config
                })
                results["failed_count"] += 1

                logger.warning(
                    f"Import batch - Fallito impresa '{nome_impresa}': "
                    f"{error_type}: {error_msg}"
                )

        # Log finale
        logger.info(
            f"Import batch completato: {results['success_count']} successi, "
            f"{results['failed_count']} fallimenti su {results['total']} totali"
        )

        return results


import_service = ImportService()

__all__ = [
    "ImportService",
    "import_service",
]
