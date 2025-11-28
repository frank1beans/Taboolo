"""
McImportService - Servizio dedicato per l'importazione di file MC (Computo Metrico).

LOGICA MC:
- File contiene PROGRESSIVI + QUANTITÀ + PREZZI
- Match ESATTO su progressivo (ignorare codice se in conflitto)
- Ogni progressivo può avere prezzo diverso anche con stesso codice
- L'impresa quota il SINGOLO PROGRESSIVO, non il prodotto
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Sequence

from sqlmodel import Session, select

from app.db.models import Computo, ComputoTipo, PriceListItem, PriceListOffer, VoceComputo
from app.db.models_wbs import Impresa
from app.excel import ParsedVoce, parse_computo_excel
from app.services.commesse import CommesseService
from app.services.importers.common import (
    BaseImportService,
    _WbsNormalizeContext,
    _ceil_amount,
    sanitize_impresa_label,
)
from app.services.importers.import_common import (
    _build_parsed_from_progetto,
    calculate_total_import,
    validate_progetto_voci,
)
from app.services.importers.matching import (
    _align_return_rows,
    _build_description_price_map,
    _build_matching_report,
    _build_price_list_lookup,
    _build_project_snapshot_from_price_offers,
    _detect_duplicate_progressivi,
    _detect_forced_zero_violations,
    _format_quantity_value,
    _has_progressivi,
    _log_price_conflicts,
    _match_price_list_item_entry,
    _shorten_label,
    _sum_project_quantities,
    _voce_label,
)

logger = logging.getLogger(__name__)


class McImportService(BaseImportService):
    """
    Servizio per l'importazione di file MC (Computo Metrico).

    Il file MC contiene progressivi + quantità + prezzi.
    Match ESATTO su progressivo, ogni progressivo può avere prezzo diverso
    anche con stesso codice prodotto.
    """

    @staticmethod
    def _get_or_create_impresa(session: Session, label: str | None) -> Impresa | None:
        """Recupera o crea un'impresa normalizzando il nome."""
        if not label:
            return None
        import re
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

    def _validate_mc_return_file(
        self,
        progetto_voci: Sequence[VoceComputo],
        ritorno_voci: Sequence[ParsedVoce],
    ) -> list[str]:
        """
        Valida un file MC ritorno prima dell'import.

        Verifica:
        - Progressivi duplicati nel ritorno
        - Progressivi nel ritorno ma non nel progetto
        - Codici con prezzi multipli per stesso progressivo (warning)

        Returns:
            Lista di warning/errori trovati
        """
        warnings = []

        # 1. Check progressivi duplicati nel ritorno
        progressivi_ritorno = [v.progressivo for v in ritorno_voci if v.progressivo]
        if progressivi_ritorno:
            seen = set()
            duplicates = []
            for p in progressivi_ritorno:
                if p in seen:
                    duplicates.append(p)
                seen.add(p)

            if duplicates:
                dup_unique = list(set(duplicates))[:10]
                warnings.append(
                    f"Progressivi duplicati nel file ritorno: {dup_unique}"
                )

        # 2. Check progressivi nel ritorno ma non nel progetto
        progressivi_progetto = {v.progressivo for v in progetto_voci if v.progressivo}
        progressivi_extra = set(progressivi_ritorno) - progressivi_progetto
        if progressivi_extra:
            extra_list = list(progressivi_extra)[:10]
            warnings.append(
                f"Progressivi nel ritorno ma non nel progetto: {extra_list}"
            )

        # 3. Check codici con prezzi multipli nello stesso progressivo (warning informativo)
        prog_prezzo_map = defaultdict(list)
        for voce in ritorno_voci:
            if voce.progressivo and voce.prezzo_unitario is not None:
                prog_prezzo_map[voce.progressivo].append(voce.prezzo_unitario)

        multi_price_progs = {
            prog: prezzi for prog, prezzi in prog_prezzo_map.items()
            if len(set(prezzi)) > 1
        }
        if multi_price_progs:
            examples = list(multi_price_progs.items())[:5]
            warnings.append(
                f"Progressivi con prezzi multipli nel file: {examples}"
            )

        return warnings

    def import_mc(
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
        sheet_price_column: str | None = None,
        sheet_quantity_column: str | None = None,
    ) -> Computo:
        """
        Importa un file MC (Computo Metrico) di ritorno.

        Il file MC contiene progressivi + quantità + prezzi.
        Match ESATTO su progressivo (ignora codice se in conflitto).

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            impresa: Nome impresa
            file: Path file Excel
            originale_nome: Nome originale file
            round_number: Numero round (opzionale)
            round_mode: 'auto', 'new', o 'replace'
            sheet_name: Nome foglio Excel
            sheet_price_column: Colonna prezzo
            sheet_quantity_column: Colonna quantità

        Returns:
            Computo di tipo 'ritorno'

        Raises:
            ValueError: Se manca il computo metrico base o parametri invalidi
        """
        # Validazione input
        commessa = CommesseService.get_commessa(session, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

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
            raise ValueError("Carica prima un computo metrico (MC) per la commessa")

        # Recupera voci del computo metrico base
        mc_base_voci = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == computo_metrico_base.id)
            .order_by(VoceComputo.ordine)
        ).all()

        validate_progetto_voci(mc_base_voci)

        # Normalizza impresa
        impresa = sanitize_impresa_label(impresa)
        impresa_entry = self._get_or_create_impresa(session, impresa)

        # Gestione round
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

            if any(item.round_number == resolved_round for item in existing_ritorni):
                raise ValueError(
                    f"Esiste già un computo dell'impresa {impresa} per il round {resolved_round}. "
                    "Scegli la modalità di aggiornamento oppure seleziona un round diverso."
                )

        # Parse file MC
        parser_result = parse_computo_excel(
            file,
            sheet_name=sheet_name,
            price_column=sheet_price_column,
            quantity_column=sheet_quantity_column,
        )

        # Validazione file MC
        validation_warnings = self._validate_mc_return_file(
            mc_base_voci,
            parser_result.voci,
        )

        # Statistiche
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

        # Alignment: match progressivi del ritorno con voci progetto
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

        # Matching report
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

        # Costruzione messaggi warning
        warning_message: str | None = None

        # Aggiungi validation warnings
        if validation_warnings:
            warning_message = "; ".join(validation_warnings)

        # Voci mancanti
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
                missing_note = (
                    f"{len(remaining_missing)} voci del computo metrico non sono state aggiornate dal ritorno "
                    f"(allineate {matched_count} su {total_voci}, prime: {elenco})"
                )
                if coverage < 0.5:
                    missing_note += ". Il file sembra fornire solo una parte delle voci."
                if warning_message:
                    warning_message += " " + missing_note
                else:
                    warning_message = missing_note

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

        # Calcolo importo totale
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

        # Crea o aggiorna computo
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

        # Salva voci nel DB
        self._bulk_insert_voci(session, computo, voci_allineate)

        # Sync voci normalizzate
        self._sync_normalized_offerte(
            session,
            commessa_id,
            computo,
            impresa,
            resolved_round,
            legacy_pairs,
        )

        # Sync price list offers (opzionale per MC)
        self._sync_price_list_offers(
            session=session,
            commessa_id=commessa_id,
            computo=computo,
            impresa_label=impresa,
            parsed_voci=voci_allineate,
            progetto_voci=mc_base_voci,
        )

        session.commit()
        session.refresh(computo)

        logger.info(
            f"MC Import completato: {len(voci_allineate)} voci, "
            f"importo totale: €{total_import:,.2f}"
        )

        return computo

    def _sync_normalized_offerte(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
        impresa_label: str,
        round_number: int | None,
        legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]],
    ) -> None:
        """Sincronizza le offerte normalizzate nella tabella voce_offerta."""
        from app.db.models_wbs import VoceOfferta, Voce as VoceNorm

        context = _WbsNormalizeContext(session, commessa_id)
        impresa_entry = context.get_or_create_impresa(impresa_label)
        if not impresa_entry:
            return

        # Cancella offerte esistenti
        session.exec(
            VoceOfferta.__table__.delete().where(VoceOfferta.computo_id == computo.id)
        )

        # Crea nuove offerte
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
        progetto_voci: Sequence[VoceComputo] | None = None,
    ) -> None:
        """
        Crea/aggiorna price_list_offers per MC (opzionale).

        Per MC, le offerte sono derivate dai prezzi dei progressivi, non da file LC.
        Questo è utile per tracking e confronti, ma non è la fonte primaria.
        """
        # Cancella offerte esistenti
        session.exec(
            PriceListOffer.__table__.delete().where(
                PriceListOffer.computo_id == computo.id
            )
        )

        if not parsed_voci or not progetto_voci:
            return

        price_items = session.exec(
            select(PriceListItem).where(PriceListItem.commessa_id == commessa_id)
        ).all()
        if not price_items:
            return

        # Costruisci mappa progressivo → PriceListItem
        progressivo_map: dict[int, PriceListItem] = {}
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

        # Costruisci indici per matching
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
            context.get_or_create_impresa(impresa_label) if impresa_label else None
        )

        offer_models_map: dict[int, PriceListOffer] = {}

        # Match voci MC con price_list_items
        for voce in parsed_voci:
            prezzo = voce.prezzo_unitario
            # MC Fix: Skippa voci senza prezzo valido (None o 0)
            if prezzo in (None, 0, 0.0):
                continue

            # Prova prima con progressivo
            target_item = None
            if voce.progressivo is not None:
                try:
                    target_item = progressivo_map.get(int(voce.progressivo))
                except (TypeError, ValueError):
                    pass

            # Fallback: match su codice/descrizione
            if not target_item:
                target_item = _match_price_list_item_entry(
                    voce,
                    code_map,
                    signature_map,
                    description_map,
                    head_signature_map,
                    tail_signature_map,
                    embedding_map,
                )

            if not target_item:
                continue

            price_value = round(float(prezzo), 4)

            # Crea o aggiorna offerta
            existing_offer = offer_models_map.get(target_item.id)
            if existing_offer:
                # Stesso product_id con prezzi diversi (caso MC valido!)
                # MC Fix: Mantieni il PRIMO prezzo invece dell'ultimo
                logger.debug(
                    f"MC: Product_id {target_item.product_id} ha prezzi multipli "
                    f"({existing_offer.prezzo_unitario} vs {price_value}). Mantengo primo."
                )
                # Non sovrascrivere - mantieni il primo prezzo trovato
            else:
                offer_models_map[target_item.id] = PriceListOffer(
                    price_list_item_id=target_item.id,
                    commessa_id=commessa_id,
                    computo_id=computo.id,
                    impresa_id=impresa_entry.id if impresa_entry else None,
                    impresa_label=impresa_label,
                    round_number=computo.round_number,
                    prezzo_unitario=price_value,
                    quantita=voce.quantita,
                )

        if offer_models_map:
            session.add_all(offer_models_map.values())
            logger.info(f"MC: Create {len(offer_models_map)} price_list_offers")

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

        logger.info(
            f"MC Progetto importato: {len(parser_result.voci)} voci, "
            f"importo totale: €{total_import:,.2f}"
        )

        return computo

    def _persist_computo_metrico_voci(
        self,
        *,
        session: Session,
        commessa_id: int,
        computo: Computo,
        parsed_voci: Sequence[ParsedVoce],
    ) -> list[VoceComputo]:
        """Salva le voci del computo metrico (MC) nel DB."""
        # Riusa la logica di bulk_insert_voci
        self._bulk_insert_voci(session, computo, parsed_voci)

        # Sync voci normalizzate
        context = _WbsNormalizeContext(session, commessa_id)
        for parsed in parsed_voci:
            context.ensure_voce(parsed, None)

        return session.exec(
            select(VoceComputo).where(VoceComputo.computo_id == computo.id)
        ).all()
