from __future__ import annotations

from pathlib import Path
from typing import Sequence

from sqlmodel import Session

from app.db.models import Computo, ComputoTipo, VoceComputo
from app.db.models_wbs import VoceProgetto
from app.excel import ParsedVoce, parse_computo_excel
from app.services.commesse import CommesseService
from app.services.importers.common import _WbsNormalizeContext, _ceil_amount
from app.services.importers.lc import LcImportService


class McImportService(LcImportService):
    """
    Import MC (Computo Metrico).

    Gestisce:
    - Import computo metrico completo (quantità + prezzi + WBS)
    - Ritorni gara basati su progressivi (riusa pipeline LC)

    Nomenclatura:
    - MC = Computo Metrico = File completo con quantità
    - LC = Lista Lavorazioni = File ritorno con solo prezzi
    """

    def import_computo_metrico(
        self,
        *,
        session: Session,
        commessa_id: int,
        file: Path,
        originale_nome: str | None,
    ) -> Computo:
        """
        Importa un computo metrico (MC) completo da file Excel/SIX.

        Il computo metrico contiene:
        - Struttura WBS completa
        - Quantità per ogni voce
        - Prezzi unitari
        - Importi calcolati

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            file: Path file Excel/SIX
            originale_nome: Nome originale file

        Returns:
            Computo di tipo 'progetto' (MC base per confronto ritorni)
        """
        commessa = CommesseService.get_commessa(session, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

        parser_result = parse_computo_excel(file)
        if parser_result.totale_importo is not None:
            total_import = _ceil_amount(parser_result.totale_importo)
        else:
            total_import = _ceil_amount(sum(voce.importo or 0 for voce in parser_result.voci))

        computo = CommesseService.add_computo(
            session,
            commessa,
            nome=f"{commessa.nome} - Computo Metrico",
            tipo=ComputoTipo.progetto,
            file_nome=originale_nome,
            file_percorso=str(file),
        )

        computo.importo_totale = total_import
        session.add(computo)
        self._persist_computo_metrico_voci(
            session=session,
            commessa_id=commessa.id,
            computo=computo,
            parsed_voci=parser_result.voci,
        )
        session.commit()
        session.refresh(computo)
        return computo

    # Alias per retrocompatibilità
    def import_computo_progetto(self, **kwargs) -> Computo:
        """DEPRECATED: Usa import_computo_metrico(). Mantenuto per retrocompatibilità."""
        return self.import_computo_metrico(**kwargs)

    def _persist_computo_metrico_voci(
        self,
        *,
        session: Session,
        commessa_id: int,
        computo: Computo,
        parsed_voci: Sequence[ParsedVoce],
    ) -> list[VoceComputo]:
        """
        Salva le voci del computo metrico (MC) nel DB.

        Crea:
        - VoceComputo (struttura legacy flat)
        - VoceProgetto (struttura normalizzata WBS)

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            computo: Computo container
            parsed_voci: Voci parsate da Excel/SIX

        Returns:
            Lista VoceComputo create
        """
        legacy_voci = self._bulk_insert_voci(session, computo, parsed_voci)
        self._sync_normalized_computo_metrico(
            session,
            commessa_id,
            computo,
            legacy_voci,
            parsed_voci,
        )
        return legacy_voci

    # Alias per retrocompatibilità
    def persist_project_from_parsed(self, **kwargs) -> list[VoceComputo]:
        """DEPRECATED: Usa _persist_computo_metrico_voci(). Mantenuto per retrocompatibilità."""
        return self._persist_computo_metrico_voci(**kwargs)

    def _sync_normalized_computo_metrico(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
        legacy_voci: Sequence[VoceComputo],
        parsed_voci: Sequence[ParsedVoce],
    ) -> None:
        """
        Sincronizza voci normalizzate WBS per il computo metrico (MC).

        Crea entries in VoceProgetto (tabella normalizzata) partendo
        dalle voci legacy flat.
        """
        context = _WbsNormalizeContext(session, commessa_id)
        session.exec(
            VoceProgetto.__table__.delete().where(VoceProgetto.computo_id == computo.id)
        )
        for legacy, parsed in zip(legacy_voci, parsed_voci):
            voce_norm = context.ensure_voce(parsed, legacy)
            if voce_norm is None:
                continue
            session.add(
                VoceProgetto(
                    voce_id=voce_norm.id,
                    computo_id=computo.id,
                    quantita=parsed.quantita,
                    prezzo_unitario=parsed.prezzo_unitario,
                    importo=parsed.importo,
                    note=parsed.note,
                )
            )

    # Alias per retrocompatibilità
    def _sync_normalized_progetto(self, *args, **kwargs) -> None:
        """DEPRECATED: Usa _sync_normalized_computo_metrico(). Mantenuto per retrocompatibilità."""
        return self._sync_normalized_computo_metrico(*args, **kwargs)
