"""
LcImportService - Servizio dedicato per l'importazione di file LC (Lista Lavorazioni).

LOGICA LC:
- File contiene solo PREZZI UNITARI per ciascun prodotto (codice/descrizione)
- NON contiene progressivi (è un listino prezzi puro)
- L'impresa quota il PRODOTTO, non il singolo progressivo
- Un prezzo per product_id → applicato a TUTTI i progressivi con quel product_id
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from sqlmodel import Session, select

from app.db.models import Computo, ComputoTipo, PriceListItem, PriceListOffer, VoceComputo
from app.db.models_wbs import Impresa
from app.excel import ParsedVoce
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
from app.services.importers.lc_parser import parse_lc_return_excel
from app.services.importers.matching import (
    _build_lc_matching_report,
    _build_price_list_lookup,
    _log_unmatched_price_entries,
    _match_price_list_item_entry,
)

logger = logging.getLogger(__name__)


class LcImportService(BaseImportService):
    """
    Servizio per l'importazione di file LC (Lista Lavorazioni).

    Il file LC contiene solo prezzi unitari per prodotto, senza progressivi.
    Ogni prezzo viene applicato a TUTTI i progressivi che usano quel product_id.
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

    def _build_computo_from_lc_offers(
        self,
        progetto_voci: Sequence[VoceComputo],
        price_items: Sequence[PriceListItem],
        offer_price_map: dict[int, float],
    ) -> tuple[list[ParsedVoce], list[tuple[VoceComputo, ParsedVoce]]]:
        """
        Ricostruisce il computo da offerte LC.

        LOGICA LC SPECIFICA:
        - Un prezzo per product_id → applicato a TUTTI i progressivi con quel product_id
        - L'impresa quota il prodotto, non il singolo progressivo
        - Se product_id ha multipli progressivi, TUTTI ricevono lo stesso prezzo

        Args:
            progetto_voci: Voci del computo progetto (MC)
            price_items: Items del listino prezzi
            offer_price_map: Mappa price_list_item_id → prezzo offerta

        Returns:
            Tuple (voci_parsed, legacy_pairs) per creare il computo ritorno
        """
        if not progetto_voci:
            return [], []

        # 1. Costruisci indice: product_id → price_list_item
        product_index: dict[str, PriceListItem] = {}
        for item in price_items:
            product_id = (item.product_id or "").strip()
            if product_id:
                product_index[product_id] = item

        # 2. Statistiche per logging
        product_ids_with_offers = set()
        progressivi_with_offers = 0
        progressivi_without_offers = 0

        # 3. Per ogni voce del progetto, applica il prezzo dell'offerta se esiste
        parsed_voci: list[ParsedVoce] = []
        legacy_pairs: list[tuple[VoceComputo, ParsedVoce]] = []

        for voce in progetto_voci:
            metadata = voce.extra_metadata or {}
            product_id = metadata.get("product_id") if isinstance(metadata, dict) else None

            # Cerca il price_list_item per questo product_id
            target_item = product_index.get(product_id) if product_id else None

            # Cerca il prezzo dell'offerta
            prezzo_offerta = offer_price_map.get(target_item.id) if target_item else None

            # LOGICA LC: usa prezzo offerta se esiste, altrimenti mantieni prezzo progetto
            quantita = voce.quantita
            prezzo_value = prezzo_offerta if prezzo_offerta is not None else voce.prezzo_unitario

            # Tracking per statistiche
            if prezzo_offerta is not None:
                progressivi_with_offers += 1
                if product_id:
                    product_ids_with_offers.add(product_id)
            else:
                progressivi_without_offers += 1

            # Ricalcola importo con nuovo prezzo
            importo_value = voce.importo
            if prezzo_offerta is not None and quantita not in (None, 0):
                importo_value = _ceil_amount(
                    Decimal(str(prezzo_offerta)) * Decimal(str(quantita))
                )

            parsed = _build_parsed_from_progetto(
                voce,
                quantita,
                prezzo_value,
                importo_value,
            )
            parsed_voci.append(parsed)
            legacy_pairs.append((voce, parsed))

        # Log statistiche
        logger.info(
            f"LC Import - Ricostruzione computo: "
            f"{progressivi_with_offers} progressivi con offerta, "
            f"{progressivi_without_offers} senza offerta "
            f"({len(product_ids_with_offers)} product_id unici prezzati)"
        )

        return parsed_voci, legacy_pairs

    def _sync_price_list_offers(
        self,
        session: Session,
        commessa_id: int,
        computo: Computo,
        impresa_label: str | None,
        parsed_voci: Sequence[ParsedVoce],
        price_items: Sequence[PriceListItem],
    ) -> dict[str, Any]:
        """
        Crea/aggiorna le offerte nella tabella price_list_offer.

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            computo: Computo ritorno
            impresa_label: Nome impresa
            parsed_voci: Voci parsed dal file LC
            price_items: Items del listino prezzi

        Returns:
            Summary con statistiche matching
        """
        # Cancella offerte esistenti per questo computo
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
                "price_map": {},
            }

        if not price_items:
            return {
                "price_items_total": 0,
                "matched_item_ids": set(),
                "unmatched_entries": list(parsed_voci),
                "price_items": [],
                "price_map": {},
            }

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
        impresa_entry = context.get_or_create_impresa(impresa_label) if impresa_label else None

        matched_item_ids: set[int] = set()
        unmatched_entries: list[ParsedVoce] = []
        offer_models_map: dict[int, PriceListOffer] = {}
        price_map: dict[int, float] = {}

        # Match ogni voce LC con price_list_item
        for voce in parsed_voci:
            prezzo = voce.prezzo_unitario
            if prezzo in (None,):
                continue

            # Cerca il price_list_item corrispondente
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
                unmatched_entries.append(voce)
                continue

            price_value = round(float(prezzo), 4)
            matched_item_ids.add(target_item.id)
            price_map[target_item.id] = price_value

            # Crea o aggiorna l'offerta
            existing_offer = offer_models_map.get(target_item.id)
            if existing_offer:
                # Stesso product_id trovato più volte nel file LC
                # (dovrebbe essere raro, ma gestiamo il caso)
                logger.warning(
                    f"Product_id {target_item.product_id} ({target_item.item_code}) "
                    f"trovato più volte nel file LC. "
                    f"Prezzo precedente: {existing_offer.prezzo_unitario}, "
                    f"nuovo: {price_value}"
                )
                existing_offer.prezzo_unitario = price_value
                if voce.quantita is not None:
                    existing_offer.quantita = voce.quantita
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

        if unmatched_entries:
            _log_unmatched_price_entries(unmatched_entries)

        if offer_models_map:
            session.add_all(offer_models_map.values())

        logger.info(
            f"LC Import - Offerte create: {len(offer_models_map)}/{len(price_items)} "
            f"({len(offer_models_map)/len(price_items)*100:.1f}% coverage)"
        )

        return {
            "price_items_total": len(price_items),
            "matched_item_ids": matched_item_ids,
            "unmatched_entries": unmatched_entries,
            "price_items": price_items,
            "price_map": price_map,
        }

    def import_lc(
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
    ) -> Computo:
        """
        Importa un file LC (Lista Lavorazioni).

        Il file LC contiene solo prezzi unitari per prodotto, senza progressivi.
        Ogni prezzo viene applicato a TUTTI i progressivi che usano quel product_id.

        Args:
            session: Sessione DB
            commessa_id: ID commessa
            impresa: Nome impresa
            file: Path file Excel
            originale_nome: Nome originale file
            round_number: Numero round (opzionale)
            round_mode: 'auto', 'new', o 'replace'
            sheet_name: Nome foglio Excel
            sheet_code_columns: Colonne codice
            sheet_description_columns: Colonne descrizione
            sheet_price_column: Colonna prezzo
            sheet_quantity_column: Colonna quantità (opzionale)
            sheet_progressive_column: Colonna progressivo (opzionale, ignorato per LC)

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

        # Parse file LC
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
        column_warnings = parse_result.column_warnings

        raw_entries = parser_result.voci
        if not raw_entries:
            raise ValueError("Il file LC non contiene voci utilizzabili.")

        # Crea o aggiorna computo
        if target_computo is not None:
            computo = target_computo
            computo.file_nome = originale_nome
            computo.file_percorso = str(file)
            computo.impresa = impresa
            computo.impresa_id = impresa_entry.id if impresa_entry else None
        else:
            computo = CommesseService.add_computo(
                session,
                commessa,
                nome=f"{commessa.nome} - {impresa}",
                tipo=ComputoTipo.ritorno,
                impresa=impresa,
                impresa_id=impresa_entry.id if impresa_entry else None,
                round_number=resolved_round,
                file_nome=originale_nome,
                file_percorso=str(file),
            )

        computo.round_number = resolved_round
        computo.file_nome = originale_nome
        computo.file_percorso = str(file)
        computo.updated_at = datetime.utcnow()
        session.add(computo)

        # Recupera price_list_items
        price_items = session.exec(
            select(PriceListItem).where(PriceListItem.commessa_id == commessa_id)
        ).all()
        if not price_items:
            raise ValueError(
                "Nessun elenco prezzi associato alla commessa: impossibile importare il file LC."
            )

        # Sync offerte: voci LC → price_list_offer
        summary = self._sync_price_list_offers(
            session=session,
            commessa_id=commessa_id,
            computo=computo,
            impresa_label=impresa,
            parsed_voci=raw_entries,
            price_items=price_items,
        )

        if not summary or summary["price_items_total"] == 0:
            raise ValueError(
                "Nessun elenco prezzi associato alla commessa: impossibile importare il file LC."
            )

        # Report matching
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

        # Ricostruisci computo: price_list_offer → voci computo ritorno
        price_map: dict[int, float] = summary.get("price_map") or {}
        voci_allineate, legacy_pairs = self._build_computo_from_lc_offers(
            mc_base_voci,  # Voci progetto
            price_items,
            price_map,
        )

        total_import = calculate_total_import(voci_allineate)
        computo.importo_totale = total_import

        # Salva voci nel DB
        self._bulk_insert_voci(session, computo, voci_allineate)

        # Sync voci normalizzate
        if legacy_pairs:
            self._sync_normalized_offerte(
                session,
                commessa_id,
                computo,
                impresa,
                resolved_round,
                legacy_pairs,
            )

        session.commit()
        session.refresh(computo)

        logger.info(
            f"LC Import completato: {len(voci_allineate)} voci, "
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
