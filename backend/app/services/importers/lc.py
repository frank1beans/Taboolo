from __future__ import annotations

import logging
import unicodedata
from collections import defaultdict, deque
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import copy
import re
from pathlib import Path
from typing import Any, Iterable, Sequence, Dict, Optional, Tuple

from sqlmodel import Session, select

from app.db.models import Computo, ComputoTipo, PriceListItem, PriceListOffer, VoceComputo
from app.db.models_wbs import Impresa, Voce as VoceNorm, VoceOfferta
from app.excel import ParsedComputo, ParsedVoce, ParsedWbsLevel, parse_computo_excel
from app.excel.parser import MAX_WBS_LEVELS
from app.services.commesse import CommesseService
from app.services.nlp import semantic_embedding_service
from app.services.importers.common import (
    BaseImportService,
    _WbsNormalizeContext,
    _build_global_voce_code,
    _map_wbs_levels,
    _normalize_commessa_tag,
    _normalize_wbs6_code,
    _normalize_wbs7_code,
    _looks_like_wbs7_code,
    _calculate_line_amount,
    _ceil_amount,
    _ceil_quantity,
    sanitize_impresa_label,
)
from app.services.importers.lc_parser import parse_lc_return_excel
from app.services.importers.matching import (
    _align_return_rows,
    _build_description_price_map,
    _build_lc_matching_report,
    _build_matching_report,
    _build_price_list_lookup,
    _build_project_snapshot_from_price_offers,
    _detect_duplicate_progressivi,
    _detect_forced_zero_violations,
    _format_quantity_value,
    _has_progressivi,
    _log_price_conflicts,
    _log_unmatched_price_entries,
    _match_price_list_item_entry,
    _prices_match,
    _shorten_label,
    _sum_project_quantities,
    _voce_label,
)

logger = logging.getLogger(__name__)


class LcImportService(BaseImportService):
    """Gestisce il caricamento di file Excel e la creazione delle voci di computo."""

    @staticmethod
    def _get_or_create_impresa(session: Session, label: str | None) -> Optional[Impresa]:
        """Recupera o crea un'impresa normalizzando il nome."""
        if not label:
            return None
        text = sanitize_impresa_label(label)
        if not text:
            return None
        normalized = re.sub(r"\s+", " ", text).lower()
        if not normalized:
            return None
        existing = session.exec(
            select(Impresa).where(Impresa.normalized_label == normalized)
        ).first()
        if existing:
            return existing
        impresa = Impresa(label=text, normalized_label=normalized)
        session.add(impresa)
        session.flush()
        return impresa

    def _import_lc_return(
        self,
        *,
        session: Session,
        commessa,
        parser_result: ParsedComputo,
        column_warnings: Sequence[str] | None = None,
        progetto_voci: Sequence[VoceComputo],
        impresa: str,
        impresa_id: int | None,
        file: Path,
        originale_nome: str | None,
        resolved_round: int,
        target_computo: Computo | None,
    ) -> Computo:
        raw_entries = parser_result.voci
        if not raw_entries:
            raise ValueError("Il file LC non contiene voci utilizzabili.")

        if target_computo is not None:
            computo = target_computo
            computo.file_nome = originale_nome
            computo.file_percorso = str(file)
            computo.impresa = impresa
            computo.impresa_id = impresa_id
        else:
            computo = CommesseService.add_computo(
                session,
                commessa,
                nome=f"{commessa.nome} - {impresa}",
                tipo=ComputoTipo.ritorno,
                impresa=impresa,
                impresa_id=impresa_id,
                round_number=resolved_round,
                file_nome=originale_nome,
                file_percorso=str(file),
            )

        computo.round_number = resolved_round
        computo.file_nome = originale_nome
        computo.file_percorso = str(file)
        computo.updated_at = datetime.utcnow()
        session.add(computo)

        summary = self._sync_price_list_offers(
            session=session,
            commessa_id=commessa.id,
            computo=computo,
            impresa_label=impresa,
            parsed_voci=raw_entries,
            progetto_voci=progetto_voci,
            collect_summary=True,
        )
        if not summary or summary["price_items_total"] == 0:
            raise ValueError(
                "Nessun elenco prezzi associato alla commessa: impossibile importare il file LC."
            )

        matching_report = _build_lc_matching_report(summary)
        computo.matching_report = matching_report

        missing_count = max(
            0,
            summary["price_items_total"] - len(summary["matched_item_ids"]),
        )
        note_messages: list[str] = []
        if missing_count:
            note_messages.append(
                f"{missing_count} voci del listino non hanno trovato un prezzo nel file LC."
            )
        if column_warnings:
            note_messages.extend(column_warnings)
        computo.note = " ".join(note_messages) if note_messages else None

        price_items = summary.get("price_items") or []
        price_map: dict[int, float] = summary.get("price_map") or {}
        voci_allineate, legacy_pairs = _build_project_snapshot_from_price_offers(
            progetto_voci,
            price_items,
            price_map,
        )

        total_import = _ceil_amount(
            sum(voce.importo or 0 for voce in voci_allineate)
        )
        computo.importo_totale = total_import or 0.0

        self._bulk_insert_voci(session, computo, voci_allineate)
        if legacy_pairs:
            self._sync_normalized_offerte(
                session,
                commessa.id,
                computo,
                impresa,
                resolved_round,
                legacy_pairs,
            )

        session.commit()
        session.refresh(computo)
        return computo

    def import_ritorno_gara(
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
        progetto_voci_override: Sequence[VoceComputo] | None = None,
    ) -> Computo:
        """
        Importa un ritorno di gara (autodetect LC o MC mode).

        Modalità rilevate automaticamente:
        - **LC (Lista Lavorazioni)**: se sheet_price_column specificato
          → File con solo prezzi unitari, matching su elenco prezzi
        - **MC mode**: altrimenti
          → File con quantità, matching su progressivi/descrizioni

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            impresa: Nome impresa
            file: Path file Excel
            originale_nome: Nome originale file
            round_number: Numero round (opzionale)
            round_mode: 'auto', 'new', o 'replace'
            sheet_name: Nome foglio Excel (opzionale)
            sheet_code_columns: Colonne codice per parsing LC
            sheet_description_columns: Colonne descrizione per parsing LC
            sheet_price_column: Colonna prezzo (trigger modalità LC)
            sheet_quantity_column: Colonna quantità (opzionale)
            sheet_progressive_column: Colonna progressivo (opzionale)

        Returns:
            Computo di tipo 'ritorno'

        Raises:
            ValueError: Se manca il computo metrico base o parametri invalidi
        """
        commessa = CommesseService.get_commessa(session, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

        resolved_mode = (mode or "").strip().lower()
        if resolved_mode and resolved_mode not in {"lc", "mc"}:
            raise ValueError("Modalità import non valida. Usa 'lc' oppure 'mc'.")

        # Recupera computo metrico base (MC) della commessa
        computo_metrico_base = session.exec(
            select(Computo)
            .where(
                Computo.commessa_id == commessa_id,
                Computo.tipo == ComputoTipo.progetto,
            )
            .order_by(Computo.created_at.desc())
        ).first()
        if not computo_metrico_base:
            raise ValueError(
                "Carica prima un computo metrico (MC) per la commessa"
            )

        impresa = sanitize_impresa_label(impresa)
        impresa_entry = self._get_or_create_impresa(session, impresa)

        # Recupera voci del computo metrico base per confronto (riusabili fra imprese)
        if progetto_voci_override is not None:
            mc_base_voci = list(progetto_voci_override)
        else:
            mc_base_voci = session.exec(
                select(VoceComputo)
                .where(VoceComputo.computo_id == computo_metrico_base.id)
                .order_by(VoceComputo.ordine)
            ).all()
            if not mc_base_voci:
                raise ValueError(
                    "Il computo metrico (MC) non contiene voci importabili"
                )

        existing_ritorni = session.exec(
            select(Computo)
            .where(
                Computo.commessa_id == commessa_id,
                Computo.tipo == ComputoTipo.ritorno,
                Computo.impresa == impresa,
            )
            .order_by(Computo.created_at.asc())
        ).all()

        normalized_mode = (round_mode or "auto").strip().lower()
        if normalized_mode not in {"auto", "new", "replace"}:
            raise ValueError("Modalità round non valida. Usa 'new' oppure 'replace'.")

        target_computo: Computo | None = None
        resolved_round: int

        if normalized_mode == "replace":
            if round_number is None:
                raise ValueError("Seleziona il round da aggiornare.")
            target_computo = next(
                (item for item in existing_ritorni if item.round_number == round_number),
                None,
            )
            if target_computo is None:
                raise ValueError(
                    f"Nessun computo dell'impresa {impresa} trovato per il round {round_number}."
                )
            resolved_round = round_number
        else:
            if round_number is not None:
                resolved_round = round_number
            else:
                existing_numbers = [
                    item.round_number
                    for item in existing_ritorni
                    if item.round_number is not None
                ]
                if existing_numbers:
                    resolved_round = max(existing_numbers) + 1
                else:
                    resolved_round = 1

            if any(
                item.round_number == resolved_round for item in existing_ritorni
            ):
                raise ValueError(
                    f"Esiste già un computo dell'impresa {impresa} per il round {resolved_round}. "
                    "Scegli la modalità di aggiornamento oppure seleziona un round diverso."
                )

        if resolved_mode:
            lc_mode = resolved_mode == "lc"
        else:
            lc_mode = bool(sheet_price_column)
        if lc_mode:
            parse_result = parse_lc_return_excel(
                file,
                sheet_name,
                sheet_code_columns or [],
                sheet_description_columns or [],
                sheet_price_column or "",
                sheet_quantity_column,
                sheet_progressive_column,
            )
            parser_result = parse_result.computo
            return self._import_lc_return(
                session=session,
                commessa=commessa,
                parser_result=parser_result,
                column_warnings=parse_result.column_warnings,
                progetto_voci=None,  # in LC il progressivo non è previsto
                impresa=impresa,
                impresa_id=impresa_entry.id if impresa_entry else None,
                file=file,
                originale_nome=originale_nome,
                resolved_round=resolved_round,
                target_computo=target_computo,
            )

        parser_result = parse_computo_excel(
            file,
            sheet_name=sheet_name,
            price_column=sheet_price_column,
            quantity_column=sheet_quantity_column,
        )
        description_price_map = _build_description_price_map(parser_result.voci)
        ritorno_con_progressivi = _has_progressivi(parser_result.voci)
        mc_quantita_totale = _sum_project_quantities(mc_base_voci)
        excel_quantita_totale = (
            Decimal(str(parser_result.totale_quantita))
            if parser_result.totale_quantita is not None
            else None
        )
        ritorno_quantita_totale = (
            excel_quantita_totale
            if excel_quantita_totale is not None
            else sum(Decimal(str(voce.quantita or 0)) for voce in parser_result.voci)
        )
        mc_quantita_float = float(mc_quantita_totale or 0)
        ritorno_quantita_float = float(ritorno_quantita_totale or 0)
        delta_quantita_totale = ritorno_quantita_float - mc_quantita_float

        total_voci = len(mc_base_voci)
        alignment = _align_return_rows(
            mc_base_voci,
            parser_result.voci,
            prefer_progressivi=ritorno_con_progressivi,
            description_price_map=description_price_map,
        )

        voci_allineate = alignment.voci_allineate
        legacy_pairs = alignment.legacy_pairs
        matched_count = alignment.matched_count
        price_adjustments = alignment.price_adjustments
        zero_guard_inputs = alignment.zero_guard_inputs
        return_only_labels = alignment.return_only_labels
        progress_quantity_mismatches = alignment.progress_quantity_mismatches
        progress_price_conflicts = alignment.progress_price_conflicts
        excel_only_groups = alignment.excel_only_groups
        matching_report = _build_matching_report(
            legacy_pairs=legacy_pairs,
            excel_only_labels=return_only_labels,
            excel_only_groups=excel_only_groups,
            quantity_mismatches=progress_quantity_mismatches if ritorno_con_progressivi else None,
            quantity_totals={
                "progetto": mc_quantita_float,
                "ritorno": ritorno_quantita_float,
                "delta": delta_quantita_totale,
            },
        )

        warning_message: str | None = None
        remaining_missing = [
            _voce_label(voce_progetto)
            for voce_progetto, parsed in legacy_pairs
            if voce_progetto
            and (parsed.metadata or {}).get("missing_from_return")
        ]
        if ritorno_con_progressivi and progress_quantity_mismatches:
            summary = "; ".join(progress_quantity_mismatches[:5])
            quantity_note = (
                f"{len(progress_quantity_mismatches)} progressivi riportano quantità diverse "
                f"rispetto al computo: {summary}"
            )
            if warning_message:
                warning_message += " " + quantity_note
            else:
                warning_message = quantity_note
        if ritorno_con_progressivi and progress_price_conflicts:
            summary = "; ".join(progress_price_conflicts[:5])
            price_note = (
                f"{len(progress_price_conflicts)} progressivi hanno prezzi non coerenti: {summary}"
            )
            if warning_message:
                warning_message += " " + price_note
            else:
                warning_message = price_note
        if remaining_missing:
            elenco = ", ".join(
                _shorten_label(item) for item in remaining_missing[:5]
            )
            if len(remaining_missing) > 5:
                elenco += ", ..."
            if matched_count == 0:
                raise ValueError(
                    "Nessuna voce del file caricato corrisponde al computo metrico estimativo. "
                    "Verifica di avere esportato il ritorno con la stessa struttura del computo di progetto: "
                    f"{elenco}"
                )
            if total_voci:
                coverage = matched_count / total_voci
                warning_message = (
                    f"{len(remaining_missing)} voci del computo metrico non sono state aggiornate dal ritorno "
                    f"(allineate {matched_count} su {total_voci}, prime: {elenco})"
                )
                if coverage < 0.5:
                    warning_message += ". Il file sembra fornire solo una parte delle voci."
            else:
                warning_message = (
                    f"{len(remaining_missing)} voci del computo metrico non sono state aggiornate dal ritorno: {elenco}"
                )

        if excel_only_groups:
            elenco_excel = ", ".join(
                _shorten_label(item) for item in excel_only_groups[:5]
            )
            if len(excel_only_groups) > 5:
                elenco_excel += ", ..."
            extra_warning = (
                f"{len(excel_only_groups)} voci del ritorno non sono state abbinate al computo: {elenco_excel}"
            )
            if warning_message:
                warning_message += " " + extra_warning
            else:
                warning_message = extra_warning
        if price_adjustments:
            adjustments_summary = "; ".join(price_adjustments[:5])
            if len(price_adjustments) > 5:
                adjustments_summary += ", ..."
            adjustments_text = (
                "Corrette automaticamente alcune offerte con prezzi fuori scala: "
                f"{adjustments_summary}"
            )
            if warning_message:
                warning_message += " " + adjustments_text
            else:
                warning_message = adjustments_text

        if return_only_labels:
            extras_summary = ", ".join(return_only_labels[:5])
            if len(return_only_labels) > 5:
                extras_summary += ", ..."
            extra_warning = (
                f"Importate {len(return_only_labels)} voci presenti solo nel ritorno di gara: {extras_summary}"
            )
            if warning_message:
                warning_message += " " + extra_warning
            else:
                warning_message = extra_warning

        if ritorno_con_progressivi:
            duplicate_progressivi = _detect_duplicate_progressivi(parser_result.voci)
            if duplicate_progressivi:
                dup_summary = ", ".join(duplicate_progressivi[:5])
                if len(duplicate_progressivi) > 5:
                    dup_summary += ", ..."
                dup_warning = (
                    f"Trovati progressivi duplicati nel file importato: {dup_summary}. "
                    "Ogni progressivo deve comparire una sola volta."
                )
                if warning_message:
                    warning_message += " " + dup_warning
                else:
                    warning_message = dup_warning

        zero_guard_violations = _detect_forced_zero_violations(zero_guard_inputs)
        if zero_guard_violations:
            summary = ", ".join(zero_guard_violations[:5])
            if len(zero_guard_violations) > 5:
                summary += ", ..."
            zero_guard_warning = (
                "Alcune voci di coordinamento (Assistenze murarie / Mark up fee) risultano valorizzate "
                f"ma devono restare a zero: {summary}. Correggi il file del ritorno."
            )
            if warning_message:
                warning_message += " " + zero_guard_warning
            else:
                warning_message = zero_guard_warning

        total_import: float | None = None
        computed_total: Decimal | None = None
        if voci_allineate:
            computed_total = sum(
                Decimal(str(voce.importo))
                for voce in voci_allineate
                if voce.importo is not None
            )
            computed_total = computed_total.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total_import = float(computed_total)

        if parser_result.totale_importo is not None:
            excel_total = Decimal(str(parser_result.totale_importo)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if computed_total is None or abs(excel_total - computed_total) <= Decimal("0.01"):
                total_import = float(excel_total)
            else:
                extra_warning = (
                    "Il totale del ritorno "
                    f"({format(excel_total, '.2f')}) non coincide con la somma delle voci importate "
                    f"({format(computed_total, '.2f')})."
                )
                if warning_message:
                    warning_message += " " + extra_warning
                else:
                    warning_message = extra_warning

        if excel_quantita_totale is not None and mc_quantita_totale is not None:
            excel_quantity = excel_quantita_totale.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            mc_quantity = mc_quantita_totale.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            if abs(excel_quantity - mc_quantity) > Decimal("0.0001"):
                quantity_warning = (
                    "Il totale delle quantità importate "
                    f"({_format_quantity_value(excel_quantity)}) non coincide con il computo metrico "
                    f"({_format_quantity_value(mc_quantity)})."
                )
                if warning_message:
                    warning_message += " " + quantity_warning
                else:
                    warning_message = quantity_warning

        if target_computo is not None:
            computo = target_computo
            computo.file_nome = originale_nome
            computo.file_percorso = str(file)
            computo.impresa = impresa
        else:
            computo = CommesseService.add_computo(
                session,
                commessa,
                nome=f"{commessa.nome} - {impresa}",
                tipo=ComputoTipo.ritorno,
                impresa=impresa,
                round_number=resolved_round,
                file_nome=originale_nome,
                file_percorso=str(file),
            )

        computo.round_number = resolved_round
        computo.importo_totale = total_import
        computo.file_nome = originale_nome
        computo.file_percorso = str(file)
        if warning_message:
            computo.note = warning_message
        else:
            computo.note = None
        computo.updated_at = datetime.utcnow()
        computo.matching_report = matching_report
        session.add(computo)
        self._bulk_insert_voci(session, computo, voci_allineate)
        self._sync_normalized_offerte(
            session,
            commessa.id,
            computo,
            impresa,
            resolved_round,
            legacy_pairs,
        )
        self._sync_price_list_offers(
            session=session,
            commessa_id=commessa.id,
            computo=computo,
            impresa_label=impresa,
            parsed_voci=voci_allineate,
            progetto_voci=mc_base_voci,
        )
        session.commit()
        session.refresh(computo)
        return computo

    # Alias per retrocompatibilità
    def import_computo_ritorno(self, **kwargs) -> Computo:
        """DEPRECATED: Usa import_ritorno_gara(). Mantenuto per retrocompatibilità."""
        return self.import_ritorno_gara(**kwargs)

    def import_batch_single_file(
        self,
        *,
        session: Session,
        commessa_id: int,
        file: Path,
        originale_nome: str | None,
        imprese_config: Sequence[dict[str, Any]],
        sheet_name: str | None = None,
        sheet_code_columns: Sequence[str] | None = None,
        sheet_description_columns: Sequence[str] | None = None,
        sheet_progressive_column: str | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
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
            imprese_config: Lista di configurazioni imprese, ogni dict contiene:
                - nome_impresa: str - Nome impresa
                - colonna_prezzo: str - Colonna prezzo (es. "E")
                - colonna_quantita: str | None - Colonna quantità opzionale (es. "D")
                - round_number: int | None - Numero round
                - round_mode: str - Modalità round ("auto", "new", "replace")
            sheet_name: Nome foglio Excel (opzionale)
            sheet_code_columns: Colonne codice (opzionale)
            sheet_description_columns: Colonne descrizione (opzionale)
            sheet_progressive_column: Colonna progressivo (opzionale)

        Returns:
            Report con struttura:
            {
                "success": ["Impresa A", "Impresa B"],
                "failed": [
                    {"impresa": "Impresa C", "error": "...", "details": "..."}
                ],
                "computi": {
                    "Impresa A": <Computo>,
                    "Impresa B": <Computo>
                },
                "total": 3,
                "success_count": 2,
                "failed_count": 1
            }

        Example:
            >>> result = service.import_batch_single_file(
            ...     session=session,
            ...     commessa_id=123,
            ...     file=Path("ritorni_multi.xlsx"),
            ...     originale_nome="ritorni_multi.xlsx",
            ...     imprese_config=[
            ...         {
            ...             "nome_impresa": "Impresa A",
            ...             "colonna_prezzo": "E",
            ...             "colonna_quantita": "D",
            ...             "round_number": 1,
            ...             "round_mode": "new"
            ...         },
            ...         {
            ...             "nome_impresa": "Impresa B",
            ...             "colonna_prezzo": "G",
            ...             "colonna_quantita": "F",
            ...             "round_number": 1,
            ...             "round_mode": "new"
            ...         }
            ...     ]
            ... )
        """
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
                # Chiama import_ritorno_gara con colonne specifiche per questa impresa
                computo = self.import_ritorno_gara(
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
                    # riusa voci progetto per prestazioni/consistenza
                    progetto_voci_override=progetto_voci,
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

    def update_manual_offer_price(
        self,
        *,
        session: Session,
        commessa_id: int,
        computo_id: int,
        price_list_item_id: int,
        prezzo_unitario: float,
        quantita: float | None = None,
    ) -> tuple[PriceListOffer, Computo]:
        computo = session.get(Computo, computo_id)
        if not computo or computo.commessa_id != commessa_id:
            raise ValueError("Computo non valido per la commessa selezionata.")
        if computo.tipo != ComputoTipo.ritorno:
            raise ValueError("L'aggiornamento manuale dei prezzi è consentito solo sui ritorni gara.")

        item = session.get(PriceListItem, price_list_item_id)
        if not item or item.commessa_id != commessa_id:
            raise ValueError("Voce di elenco prezzi non trovata per la commessa indicata.")

        context = _WbsNormalizeContext(session, commessa_id)
        impresa_entry = (
            context.get_or_create_impresa(computo.impresa) if computo.impresa else None
        )
        offer = session.exec(
            select(PriceListOffer).where(
                PriceListOffer.computo_id == computo.id,
                PriceListOffer.price_list_item_id == price_list_item_id,
            )
        ).first()
        if not offer:
            offer = PriceListOffer(
                price_list_item_id=price_list_item_id,
                commessa_id=commessa_id,
                computo_id=computo.id,
                impresa_id=impresa_entry.id if impresa_entry else None,
                impresa_label=computo.impresa,
                round_number=computo.round_number,
            )
        offer.prezzo_unitario = round(float(prezzo_unitario), 4)
        if quantita is not None:
            offer.quantita = quantita
        offer.updated_at = datetime.utcnow()
        session.add(offer)

        self._rebuild_computo_from_offers(session, commessa_id, computo)
        self._acknowledge_manual_price(computo, price_list_item_id)

        session.commit()
        session.refresh(offer)
        session.refresh(computo)
        return offer, computo

    def _sync_normalized_offerte(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
        impresa_label: str,
        round_number: int | None,
        legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]],
    ) -> None:
        context = _WbsNormalizeContext(session, commessa_id)
        impresa_entry = context.get_or_create_impresa(impresa_label)
        if not impresa_entry:
            return
        session.exec(
            VoceOfferta.__table__.delete().where(VoceOfferta.computo_id == computo.id)
        )
        for legacy, parsed in legacy_pairs:
            voce_norm = context.get_voce_from_legacy(legacy.id) if legacy else None
            if voce_norm is None:
                voce_norm = context.ensure_voce(parsed, legacy)
            if voce_norm is None:
                continue
            session.add(
                VoceOfferta(
                    voce_id=voce_norm.id,
                    computo_id=computo.id,
                    impresa_id=impresa_entry.id,
                    round_number=round_number,
                    quantita=parsed.quantita,
                    prezzo_unitario=parsed.prezzo_unitario,
                    importo=parsed.importo,
                    note=parsed.note,
                )
            )

    def _sync_price_list_offers(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
        impresa_label: str | None,
        parsed_voci: Sequence[ParsedVoce],
        *,
        persist_impresa: bool = True,
        collect_summary: bool = False,
        progetto_voci: Sequence[VoceComputo] | None = None,
    ) -> dict[str, Any] | None:
        session.exec(
            PriceListOffer.__table__.delete().where(
                PriceListOffer.computo_id == computo.id
            )
        )
        if not parsed_voci:
            return {
                "price_items_total": 0,
                "matched_item_ids": set(),
                "unmatched_entries": [],
                "price_items": [],
            } if collect_summary else None

        price_items = session.exec(
            select(PriceListItem).where(PriceListItem.commessa_id == commessa_id)
        ).all()
        if not price_items:
            return {
                "price_items_total": 0,
                "matched_item_ids": set(),
                "unmatched_entries": list(parsed_voci),
                "price_items": [],
            } if collect_summary else None

        # Mappa progressivo -> PriceListItem usando il computo di progetto.
        progressivo_map: dict[int, PriceListItem] = {}
        if progetto_voci:
            product_index = {
                str(item.product_id): item
                for item in price_items
                if item.product_id
            }
            for voce in progetto_voci:
                if voce.progressivo in (None,):
                    continue
                metadata = voce.extra_metadata or {}
                product_id = metadata.get("product_id")
                if not product_id:
                    continue
                target_item = product_index.get(str(product_id))
                if target_item:
                    try:
                        progressivo_map[int(voce.progressivo)] = target_item
                    except (TypeError, ValueError):
                        continue

        (
            code_map,
            signature_map,
            description_map,
            head_signature_map,
            tail_signature_map,
            embedding_map,
        ) = _build_price_list_lookup(price_items)
        context = _WbsNormalizeContext(session, commessa_id)
        impresa_entry = (
            context.get_or_create_impresa(impresa_label)
            if persist_impresa and impresa_label
            else None
        )

        matched_item_ids: set[int] = set()
        unmatched_entries: list[ParsedVoce] = []
        offer_models_map: dict[int, PriceListOffer] = {}
        price_map: dict[int, float] = {}
        price_records: dict[int, list[dict[str, Any]]] = defaultdict(list)

        for voce in parsed_voci:
            prezzo = voce.prezzo_unitario
            if prezzo in (None,):
                continue
            target_item = _match_price_list_item_entry(
                voce,
                code_map,
                signature_map,
                description_map,
                head_signature_map,
                tail_signature_map,
                embedding_map,
            )
            if not target_item and progressivo_map and voce.progressivo not in (None,):
                try:
                    target_item = progressivo_map.get(int(voce.progressivo))
                except (TypeError, ValueError):
                    target_item = None
            if not target_item:
                unmatched_entries.append(voce)
                continue

            price_value = round(float(prezzo), 4)
            source_label = voce.codice or voce.descrizione or "Voce senza descrizione"
            samples = price_records[target_item.id]
            samples.append({"source": source_label, "price": price_value})

            matched_item_ids.add(target_item.id)
            price_map[target_item.id] = price_value
            existing_offer = offer_models_map.get(target_item.id)
            if existing_offer:
                existing_offer.prezzo_unitario = round(float(prezzo), 4)
                existing_offer.quantita = voce.quantita
            else:
                offer_models_map[target_item.id] = PriceListOffer(
                    price_list_item_id=target_item.id,
                    commessa_id=commessa_id,
                    computo_id=computo.id,
                    impresa_id=impresa_entry.id if impresa_entry else None,
                    impresa_label=impresa_label,
                    round_number=computo.round_number,
                    prezzo_unitario=round(float(prezzo), 4),
                    quantita=voce.quantita,
                )

        if unmatched_entries:
            _log_unmatched_price_entries(unmatched_entries)

        if offer_models_map:
            session.add_all(offer_models_map.values())
        if collect_summary:
            conflict_payload = [
                {
                    "price_list_item_id": entry["price_list_item_id"],
                    "item_code": entry["item_code"],
                    "item_description": entry["item_description"],
                    "prices": sorted({round(float(p), 4) for p in entry["prices"]}),
                    "samples": entry["samples"],
                }
                for entry in conflicting_price_items.values()
            ]
            return {
                "price_items_total": len(price_items),
                "matched_item_ids": matched_item_ids,
                "unmatched_entries": unmatched_entries,
                "price_items": price_items,
                "price_map": price_map,
                "conflicting_price_items": conflict_payload,
            }
        return None

    def _rebuild_computo_from_offers(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
    ) -> None:
        progetto = session.exec(
            select(Computo)
            .where(
                Computo.commessa_id == commessa_id,
                Computo.tipo == ComputoTipo.progetto,
            )
            .order_by(Computo.created_at.desc())
        ).first()
        if not progetto:
            raise ValueError("Impossibile aggiornare il ritorno: manca il computo di progetto.")

        progetto_voci = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == progetto.id)
            .order_by(VoceComputo.ordine)
        ).all()
        if not progetto_voci:
            raise ValueError("Il computo di progetto non contiene voci da utilizzare.")

        price_items = session.exec(
            select(PriceListItem).where(PriceListItem.commessa_id == commessa_id)
        ).all()
        offer_entries = session.exec(
            select(PriceListOffer).where(PriceListOffer.computo_id == computo.id)
        ).all()
        price_map = {
            entry.price_list_item_id: entry.prezzo_unitario
            for entry in offer_entries
            if entry.prezzo_unitario is not None
        }
        voci_allineate, legacy_pairs = _build_project_snapshot_from_price_offers(
            progetto_voci,
            price_items,
            price_map,
        )
        total_import = _ceil_amount(sum(voce.importo or 0 for voce in voci_allineate))
        computo.importo_totale = total_import or 0.0
        computo.updated_at = datetime.utcnow()
        self._bulk_insert_voci(session, computo, voci_allineate)
        if legacy_pairs:
            self._sync_normalized_offerte(
                session,
                commessa_id,
                computo,
                computo.impresa or "",
                computo.round_number,
                legacy_pairs,
            )

    @staticmethod
    def _acknowledge_manual_price(computo: Computo, price_list_item_id: int) -> None:
        report = computo.matching_report
        if not isinstance(report, dict):
            return
        if report.get("mode") != "lc":
            return
        missing_items = report.get("missing_price_items")
        if not isinstance(missing_items, list):
            return
        updated_missing = [
            item
            for item in missing_items
            if item.get("price_list_item_id") != price_list_item_id
        ]
        if len(updated_missing) == len(missing_items):
            return
        report["missing_price_items"] = updated_missing
        total = report.get("total_price_items")
        if isinstance(total, int) and total >= 0:
            report["matched_price_items"] = total - len(updated_missing)
        else:
            current_matched = report.get("matched_price_items") or 0
            report["matched_price_items"] = current_matched + 1
        computo.matching_report = report



