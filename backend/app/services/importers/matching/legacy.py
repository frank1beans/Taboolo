from __future__ import annotations

import logging
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import copy
import re
from typing import Any, Iterable, Sequence, Dict, Optional, Tuple

import pandas as pd

from app.db.models import PriceListItem, VoceComputo
from app.excel import ParsedVoce, ParsedWbsLevel
from app.excel.parser import MAX_WBS_LEVELS
from app.services.importers.common import (
    _normalize_commessa_tag,
    _build_global_voce_code,
    _map_wbs_levels,
    _normalize_wbs6_code,
    _normalize_wbs7_code,
    _looks_like_wbs7_code,
    _calculate_line_amount,
    _ceil_amount,
    _ceil_quantity,
)
from app.services.nlp import semantic_embedding_service

logger = logging.getLogger(__name__)

@dataclass
class _ReturnAlignmentResult:
    voci_allineate: list[ParsedVoce]
    legacy_pairs: list[tuple[VoceComputo | None, ParsedVoce]]
    matched_count: int
    price_adjustments: list[str]
    zero_guard_inputs: list[ParsedVoce]
    return_only_labels: list[str]
    progress_quantity_mismatches: list[str]
    progress_price_conflicts: list[str]
    excel_only_groups: list[str]

def _collect_return_only_labels(
    wrappers: Sequence[dict[str, Any]],
    satisfied_group_keys: set[str] | None = None,
) -> list[str]:
    matched_groups = satisfied_group_keys or set()
    labels: list[str] = []
    for wrapper in wrappers:
        if wrapper.get("matched"):
            continue
        voce_excel = wrapper.get("voce")
        if voce_excel is None:
            continue
        key = _wbs_key_from_parsed(voce_excel)
        if key and key in matched_groups:
            continue
        label = voce_excel.descrizione or voce_excel.codice or "voce senza descrizione"
        labels.append(_shorten_label(label))
    return labels


def _align_progressive_return(
    progetto_voci: Sequence[VoceComputo],
    indice_ritorno: dict[str, list[dict[str, Any]]],
    ritorno_wrappers: Sequence[dict[str, Any]],
) -> _ReturnAlignmentResult:
    voci_allineate: list[ParsedVoce] = []
    legacy_pairs: list[tuple[VoceComputo | None, ParsedVoce]] = []
    price_adjustments: list[str] = []
    zero_guard_inputs: list[ParsedVoce] = []
    return_only_labels: list[str] = []
    progress_quantity_mismatches: list[str] = []
    progress_price_conflicts: list[str] = []
    matched_count = 0
    progress_price_registry: dict[tuple[int, str], float] = {}

    for voce_progetto in progetto_voci:
        keys = _keys_from_voce_progetto(voce_progetto)
        match = _pick_match(indice_ritorno, keys, voce_progetto)

        quantita = voce_progetto.quantita
        prezzo_unitario = voce_progetto.prezzo_unitario
        importo = voce_progetto.importo
        lock_price_override = False
        enforce_zero = _requires_zero_guard(
            voce_progetto.codice,
            voce_progetto.descrizione,
        )
        zero_guard_price_input: float | None = None
        zero_guard_quant_input: float | None = None
        zero_guard_import_input: float | None = None
        progress_key = _progress_price_key(voce_progetto)
        price_from_match: float | None = None
        quant_from_match: float | None = None
        import_from_match: float | None = None

        if match:
            matched_count += 1
            (
                price_from_match,
                quant_from_match,
                import_from_match,
            ) = _price_bundle(match)
            zero_guard_price_input = price_from_match
            zero_guard_quant_input = quant_from_match
            zero_guard_import_input = import_from_match
            if price_from_match is not None:
                corrected_price, was_corrected = _stabilize_return_price(
                    price_from_match,
                    voce_progetto.prezzo_unitario,
                )
                if was_corrected:
                    price_adjustments.append(
                        f"{_voce_label(voce_progetto)}: {format(price_from_match, '.2f')} -> {format(corrected_price, '.2f')}"
                    )
                    price_from_match = corrected_price

            project_quantity = voce_progetto.quantita
            if quant_from_match not in (None,) and project_quantity not in (None, 0):
                if not _quantities_match(project_quantity, quant_from_match):
                    progress_quantity_mismatches.append(
                        f"{_shorten_label(_voce_label(voce_progetto))} (ritorno="
                        f"{_format_quantity_for_warning(quant_from_match)} vs computo="
                        f"{_format_quantity_for_warning(project_quantity)})"
                    )
            # preferisci la quantità del ritorno, se presente; altrimenti usa quella di progetto
            if quant_from_match not in (None,):
                quantita = quant_from_match
            elif project_quantity is not None:
                quantita = project_quantity
        # MC Fix: Se il ritorno ha prezzo 0 o None, usa il prezzo del progetto come fallback
        if price_from_match not in (None, 0, 0.0):
            prezzo_unitario = round(price_from_match, 4)
            if quantita not in (None, 0):
                _, importo = _calculate_line_amount(quantita, prezzo_unitario)
            if progress_key:
                existing_price = progress_price_registry.get(progress_key)
                if existing_price is None:
                    progress_price_registry[progress_key] = prezzo_unitario
                elif not _prices_match(existing_price, prezzo_unitario):
                    progress_price_conflicts.append(
                        f"{_shorten_label(_voce_label(voce_progetto))}"
                        f" ({format(existing_price, '.4f')} vs {format(prezzo_unitario, '.4f')})"
                    )
        elif import_from_match not in (None, 0, 0.0):
            # Fallback: calcola prezzo da importo/quantità
            importo = _ceil_amount(import_from_match)
            if importo is not None and quantita not in (None, 0):
                prezzo_unitario = round(importo / quantita, 4)
        # else: mantieni prezzo_unitario del progetto (linea 84)

        if quantita is None and voce_progetto.quantita is not None:
            quantita = voce_progetto.quantita
        if quantita in (0, 0.0):
            importo = 0.0

        parsed_voce = _build_parsed_from_progetto(
            voce_progetto,
            quantita,
            prezzo_unitario,
            importo,
        )
        if match is None:
            parsed_voce.quantita = 0.0
            parsed_voce.importo = 0.0
            meta = dict(parsed_voce.metadata or {})
            meta["missing_from_return"] = True
            parsed_voce.metadata = meta

        if enforce_zero and match:
            zero_guard_inputs.append(
                _build_zero_guard_entry(
                    voce_progetto.codice or parsed_voce.codice,
                    voce_progetto.descrizione or parsed_voce.descrizione,
                    zero_guard_quant_input,
                    zero_guard_price_input,
                    zero_guard_import_input,
                )
            )

        voci_allineate.append(parsed_voce)
        legacy_pairs.append((voce_progetto, parsed_voce))

    return_only_labels = _collect_return_only_labels(ritorno_wrappers)
    return _ReturnAlignmentResult(
        voci_allineate=voci_allineate,
        legacy_pairs=legacy_pairs,
        matched_count=matched_count,
        price_adjustments=price_adjustments,
        zero_guard_inputs=zero_guard_inputs,
        return_only_labels=return_only_labels,
        progress_quantity_mismatches=progress_quantity_mismatches,
        progress_price_conflicts=progress_price_conflicts,
        excel_only_groups=[],
    )


def _align_totals_return(
    progetto_voci: Sequence[VoceComputo],
    indice_ritorno: dict[str, list[dict[str, Any]]],
    ritorno_wrappers: Sequence[dict[str, Any]],
    wbs_wrapper_map: dict[str, list[dict[str, Any]]],
    description_price_map: dict[str, list[float]],
    excel_group_targets: dict[str, Decimal],
    excel_group_labels: dict[str, str],
    excel_group_details: dict[str, dict[str, Any]],
) -> _ReturnAlignmentResult:
    voci_allineate: list[ParsedVoce] = []
    legacy_pairs: list[tuple[VoceComputo | None, ParsedVoce]] = []
    price_adjustments: list[str] = []
    zero_guard_inputs: list[ParsedVoce] = []
    group_entries: dict[str, list[ParsedVoce]] = {}
    project_group_entries: dict[str, list[tuple[ParsedVoce, VoceComputo]]] = {}
    project_primary_entries: dict[str, list[tuple[ParsedVoce, VoceComputo]]] = {}
    project_code_entries: dict[str, list[tuple[ParsedVoce, VoceComputo]]] = {}
    project_description_entries: dict[str, list[tuple[ParsedVoce, VoceComputo]]] = {}
    matched_count = 0
    wbs_price_map = _build_wbs_price_map(wbs_wrapper_map)
    used_wbs_keys: set[str] = set()

    for voce_progetto in progetto_voci:
        project_wbs_key = _wbs_key_from_model(voce_progetto)
        project_base_key = _base_wbs_key_from_key(project_wbs_key)
        keys = _keys_from_voce_progetto(voce_progetto)
        match = None
        quant_from_match: float | None = None
        import_from_match: float | None = None
        price_from_match: float | None = None
        matched_from_wbs = False
        matched_from_description = False
        wbs_group_key: str | None = None
        description_signature = _description_signature_from_model(voce_progetto)
        has_description_price = (
            description_signature is not None
            and description_signature in description_price_map
        )

        if project_base_key and project_base_key in wbs_price_map and not has_description_price:
            info = wbs_price_map[project_base_key]
            price_from_match = info.get("price")
            wbs_group_key = info.get("group_key")
            matched_from_wbs = True
            matched_count += 1
            used_wbs_keys.add(project_base_key)
        else:
            match = _pick_match(indice_ritorno, keys, voce_progetto)
            if match:
                matched_count += 1

        quantita = voce_progetto.quantita
        prezzo_unitario = voce_progetto.prezzo_unitario
        importo = voce_progetto.importo
        lock_price_override = False
        enforce_zero = _requires_zero_guard(
            voce_progetto.codice,
            voce_progetto.descrizione,
        )
        zero_guard_price_input: float | None = None
        zero_guard_quant_input: float | None = None
        zero_guard_import_input: float | None = None

        if match:
            (
                price_from_match_match,
                quant_from_match,
                import_from_match,
            ) = _price_bundle(match)
            price_from_match = price_from_match_match
            zero_guard_price_input = price_from_match
            zero_guard_quant_input = quant_from_match
            zero_guard_import_input = import_from_match
            if price_from_match is not None:
                corrected_price, was_corrected = _stabilize_return_price(
                    price_from_match,
                    voce_progetto.prezzo_unitario,
                )
                if was_corrected:
                    price_adjustments.append(
                        f"{_voce_label(voce_progetto)}: {format(price_from_match, '.2f')} -> {format(corrected_price, '.2f')}"
                    )
                    price_from_match = corrected_price
        elif matched_from_wbs and price_from_match is not None:
            zero_guard_price_input = price_from_match
            if voce_progetto.quantita not in (None, 0):
                zero_guard_quant_input = voce_progetto.quantita
                zero_guard_import_input = price_from_match * voce_progetto.quantita

        if price_from_match is None and description_signature:
            price_candidate = description_price_map.get(description_signature)
            if price_candidate is not None:
                price_from_match = price_candidate
                matched_from_description = True
        if price_from_match is not None:
            prezzo_unitario = price_from_match
            if quantita not in (None, 0):
                _, importo = _calculate_line_amount(quantita, price_from_match)
            lock_price_override = True
        elif import_from_match is not None:
            importo = import_from_match
            if quantita not in (None, 0):
                prezzo_unitario = import_from_match / quantita
            else:
                prezzo_unitario = None
            lock_price_override = True

        if quantita is None and voce_progetto.quantita is not None:
            quantita = voce_progetto.quantita

        parsed_voce = _build_parsed_from_progetto(
            voce_progetto,
            quantita,
            prezzo_unitario,
            importo,
        )
        if lock_price_override:
            meta = dict(parsed_voce.metadata or {})
            meta["lock_return_price"] = True
            parsed_voce.metadata = meta
        if match is None and not (matched_from_wbs or matched_from_description):
            parsed_voce.quantita = 0.0
            parsed_voce.importo = 0.0
            meta = dict(parsed_voce.metadata or {})
            meta["missing_from_return"] = True
            parsed_voce.metadata = meta

        if enforce_zero and (match or matched_from_wbs or matched_from_description):
            zero_guard_inputs.append(
                _build_zero_guard_entry(
                    voce_progetto.codice or parsed_voce.codice,
                    voce_progetto.descrizione or parsed_voce.descrizione,
                    zero_guard_quant_input,
                    zero_guard_price_input,
                    zero_guard_import_input,
                )
            )

        group_key = _wbs_key_from_parsed(match) if match else None
        if not group_key and matched_from_wbs:
            group_key = wbs_group_key or project_wbs_key
        if not group_key and match:
            group_key = project_wbs_key
        if group_key and (match or matched_from_wbs):
            group_entries.setdefault(group_key, []).append(parsed_voce)

        project_key = project_wbs_key
        if project_key:
            project_group_entries.setdefault(project_key, []).append(
                (parsed_voce, voce_progetto)
            )
            primary, _ = _split_wbs_key(project_key)
            if primary:
                project_primary_entries.setdefault(primary, []).append(
                    (parsed_voce, voce_progetto)
                )
            for code_token in _collect_code_tokens(voce_progetto.codice):
                project_code_entries.setdefault(code_token, []).append(
                    (parsed_voce, voce_progetto)
                )
            for desc_token in _collect_description_tokens(voce_progetto.descrizione):
                project_description_entries.setdefault(desc_token, []).append(
                    (parsed_voce, voce_progetto)
                )

        voci_allineate.append(parsed_voce)
        legacy_pairs.append((voce_progetto, parsed_voce))

    resolved_from_groups, satisfied_group_keys = _distribute_group_targets(
        excel_group_targets,
        group_entries,
        project_group_entries,
        project_code_entries,
        project_primary_entries,
        project_description_entries,
        excel_group_details,
    )
    matched_count += resolved_from_groups

    return_only_labels = _collect_return_only_labels(
        ritorno_wrappers,
        satisfied_group_keys,
    )

    for key, entries in group_entries.items():
        target = excel_group_targets.get(key)
        if target is None:
            continue
        _apply_rounding_to_match(entries, target)

    excel_only_groups = [
        excel_group_labels[key]
        for key, total in excel_group_targets.items()
        if key not in group_entries and total != Decimal("0")
    ]

    for base_key in used_wbs_keys:
        for wrapper in wbs_wrapper_map.get(base_key, []):
            wrapper["matched"] = True

    return _ReturnAlignmentResult(
        voci_allineate=voci_allineate,
        legacy_pairs=legacy_pairs,
        matched_count=matched_count,
        price_adjustments=price_adjustments,
        zero_guard_inputs=zero_guard_inputs,
        return_only_labels=return_only_labels,
        progress_quantity_mismatches=[],
        progress_price_conflicts=[],
        excel_only_groups=excel_only_groups,
    )


def _align_return_rows(
    progetto_voci: Sequence[VoceComputo],
    ritorno_voci: Sequence[ParsedVoce],
    *,
    prefer_progressivi: bool,
    description_price_map: dict[str, list[float]],
) -> _ReturnAlignmentResult:
    indice_ritorno, ritorno_wrappers = _build_return_index(ritorno_voci)
    has_progressivi = prefer_progressivi and _has_progressivi(ritorno_voci)
    if has_progressivi:
        project_buckets = _build_project_description_buckets(progetto_voci)
        _assign_wrapper_preferences(ritorno_wrappers, project_buckets)
        progressive_result = _align_progressive_return(
            progetto_voci,
            indice_ritorno,
            ritorno_wrappers,
        )
        if progressive_result.matched_count == 0:
            # Fallback: progressivi non compatibili, prova match per descrizione/WBS
            return _align_description_only_return(
                progetto_voci,
                ritorno_voci,
                description_price_map,
            )
        return progressive_result
    return _align_description_only_return(
        progetto_voci,
        ritorno_voci,
        description_price_map,
    )


def _align_description_only_return(
    progetto_voci: Sequence[VoceComputo],
    ritorno_voci: Sequence[ParsedVoce],
    description_price_map: dict[str, list[float]],
) -> _ReturnAlignmentResult:
    excel_entries: list[dict[str, Any]] = []
    signature_queues: dict[str, deque[int]] = defaultdict(deque)
    signature_labels: dict[str, str] = {}

    for voce in ritorno_voci:
        signature = _description_signature_from_parsed(voce)
        if not signature:
            continue
        tokens = _descr_tokens(voce.descrizione)
        label = voce.descrizione or voce.codice or "voce senza descrizione"
        entry = {
            "signature": signature,
            "price": voce.prezzo_unitario or 0.0,
            "label": label,
            "tokens": tokens,
            "used": False,
            "voce": voce,
            "quantity": voce.quantita,
            "importo": voce.importo,
        }
        idx = len(excel_entries)
        excel_entries.append(entry)
        signature_queues[signature].append(idx)
        signature_labels.setdefault(signature, label)

    signature_projects: dict[str, list[VoceComputo]] = defaultdict(list)
    for voce in progetto_voci:
        signature = _description_signature_from_model(voce)
        if signature:
            signature_projects[signature].append(voce)

    price_overrides: dict[int, tuple[float, int]] = {}
    matched_count = 0
    zero_guard_inputs: list[ParsedVoce] = []

    def _assign_from_signature(sig: str, voce: VoceComputo) -> bool:
        nonlocal matched_count
        queue = signature_queues.get(sig)
        if not queue:
            return False
        while queue:
            idx = queue.popleft()
            entry = excel_entries[idx]
            if entry["used"]:
                continue
            entry["used"] = True
            price_overrides[voce.id] = (entry["price"], idx)
            matched_count += 1
            return True
        return False

    def _project_sort_key(voce: VoceComputo) -> tuple[str, int]:
        code = voce.codice or ""
        order = voce.ordine or 0
        return (code, order)

    for sig, items in signature_projects.items():
        ordered = sorted(items, key=_project_sort_key)
        for voce in ordered:
            _assign_from_signature(sig, voce)

    unmatched_voice_ids = {voce.id for voce in progetto_voci if voce.id not in price_overrides}
    candidate_indices = [idx for idx, entry in enumerate(excel_entries) if not entry["used"]]
    for voce in progetto_voci:
        if voce.id not in unmatched_voice_ids:
            continue
        idx = _match_excel_entry_fuzzy(voce, excel_entries, candidate_indices)
        if idx is None:
            continue
        entry = excel_entries[idx]
        entry["used"] = True
        candidate_indices.remove(idx)
        price_overrides[voce.id] = (entry["price"], idx)
        matched_count += 1

    voci_allineate: list[ParsedVoce] = []
    legacy_pairs: list[tuple[VoceComputo | None, ParsedVoce]] = []

    for voce_progetto in progetto_voci:
        quantita = voce_progetto.quantita
        prezzo_unitario = voce_progetto.prezzo_unitario
        importo = voce_progetto.importo
        override = price_overrides.get(voce_progetto.id)
        lock_price_override = False

        if override is not None:
            price_from_excel, entry_idx = override
            entry = excel_entries[entry_idx]
            voce_excel = entry.get("voce")
            excel_quantity = None
            excel_importo = None
            if voce_excel is not None:
                excel_quantity = getattr(voce_excel, "quantita", None)
                excel_importo = getattr(voce_excel, "importo", None)
            else:
                excel_quantity = entry.get("quantity")
                excel_importo = entry.get("importo")

            # Usa sempre la quantit�� del ritorno se presente; serve per confrontare con quella di progetto.
            if excel_quantity is not None:
                quantita = excel_quantity

            prezzo_unitario = price_from_excel
            if quantita not in (None, 0):
                _, importo = _calculate_line_amount(quantita, price_from_excel)
            elif excel_importo is not None:
                importo = excel_importo
            else:
                importo = None
            lock_price_override = True
            if _requires_zero_guard(voce_progetto.codice, voce_progetto.descrizione):
                zero_guard_inputs.append(
                    _build_zero_guard_entry(
                        voce_progetto.codice,
                        voce_progetto.descrizione,
                        quantita,
                        price_from_excel,
                        importo,
                    )
                )

        parsed_voce = _build_parsed_from_progetto(
            voce_progetto,
            quantita,
            prezzo_unitario,
            importo,
        )
        meta = dict(parsed_voce.metadata or {})
        if lock_price_override:
            meta["lock_return_price"] = True
        else:
            meta["missing_from_return"] = True
        parsed_voce.metadata = meta or None
        voci_allineate.append(parsed_voce)
        legacy_pairs.append((voce_progetto, parsed_voce))

    return_only_labels = [entry["label"] for entry in excel_entries if not entry["used"]]

    return _ReturnAlignmentResult(
        voci_allineate=voci_allineate,
        legacy_pairs=legacy_pairs,
        matched_count=matched_count,
        price_adjustments=[],
        zero_guard_inputs=zero_guard_inputs,
        return_only_labels=return_only_labels,
        progress_quantity_mismatches=[],
        progress_price_conflicts=[],
        excel_only_groups=[],
    )



# parsing utilities moved to importer_parser
def _build_parsed_from_progetto(
    voce: VoceComputo,
    quantita: float | None,
    prezzo_unitario: float | None,
    importo: float | None,
) -> ParsedVoce:
    livelli: list[ParsedWbsLevel] = []
    for level in range(1, MAX_WBS_LEVELS + 1):
        code = getattr(voce, f"wbs_{level}_code")
        description = getattr(voce, f"wbs_{level}_description")
        if code or description:
            livelli.append(
                ParsedWbsLevel(level=level, code=code, description=description)
            )

    if quantita is not None:
        quantita = _ceil_quantity(quantita)

    if prezzo_unitario is not None:
        prezzo_unitario = round(float(prezzo_unitario), 4)
    if importo is not None:
        importo = _ceil_amount(importo)

    return ParsedVoce(
        ordine=voce.ordine,
        progressivo=voce.progressivo,
        codice=voce.codice,
        descrizione=voce.descrizione,
        wbs_levels=livelli,
        unita_misura=voce.unita_misura,
        quantita=quantita,
        prezzo_unitario=prezzo_unitario,
        importo=importo,
        note=voce.note,
        metadata=voce.extra_metadata,
    )


def _build_project_snapshot_from_price_offers(
    progetto_voci: Sequence[VoceComputo],
    price_items: Sequence[PriceListItem],
    offer_price_map: dict[int, float],
) -> tuple[list[ParsedVoce], list[tuple[VoceComputo, ParsedVoce]]]:
    if not progetto_voci:
        return [], []

    product_index: dict[str, PriceListItem] = {}
    for item in price_items:
        product_id = (item.product_id or "").strip()
        if product_id:
            product_index[product_id] = item

    parsed_voci: list[ParsedVoce] = []
    legacy_pairs: list[tuple[VoceComputo, ParsedVoce]] = []
    for voce in progetto_voci:
        metadata = voce.extra_metadata or {}
        product_id = metadata.get("product_id") if isinstance(metadata, dict) else None
        target_item = product_index.get(product_id) if product_id else None
        prezzo = offer_price_map.get(target_item.id) if target_item else None

        quantita = voce.quantita
        prezzo_value = prezzo if prezzo is not None else voce.prezzo_unitario
        importo_value = voce.importo
        if (
            prezzo is not None
            and quantita not in (None, 0)
        ):
            importo_value = _ceil_amount(
                Decimal(str(prezzo)) * Decimal(str(quantita))
            )

        parsed = _build_parsed_from_progetto(
            voce,
            quantita,
            prezzo_value,
            importo_value,
        )
        parsed_voci.append(parsed)
        legacy_pairs.append((voce, parsed))
    return parsed_voci, legacy_pairs


def _build_return_index(
    voci: Sequence[ParsedVoce],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    wrappers: list[dict[str, Any]] = []
    for voce in voci:
        base_key = _wbs_base_key_from_parsed(voce)
        full_key = _wbs_key_from_parsed(voce)
        is_wbs_shareable = (
            base_key is not None
            and voce.progressivo is None
            and _looks_like_wbs7_code(voce.codice)
        )
        wrapper: dict[str, Any] = {
            "voce": voce,
            "used": False,
            "matched": False,
            "tokens": _descr_tokens(voce.descrizione),
            "base_key": base_key,
            "full_key": full_key,
            "reusable": is_wbs_shareable,
        }
        wrappers.append(wrapper)
        keys = _keys_from_parsed_voce(voce)
        if not keys:
            continue
        for key in keys:
            index.setdefault(key, []).append(wrapper)
        if base_key:
            index.setdefault(f"__wbs__:{base_key}", []).append(wrapper)
    return index, wrappers


def _build_wbs_wrapper_map(
    wrappers: Sequence[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    mapping: dict[str, list[dict[str, Any]]] = {}
    for wrapper in wrappers:
        base_key = wrapper.get("base_key")
        if not base_key:
            continue
        mapping.setdefault(base_key, []).append(wrapper)
    return mapping


def _build_wbs_price_map(
    wbs_wrapper_map: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    price_map: dict[str, dict[str, Any]] = {}
    for base_key, wrappers in wbs_wrapper_map.items():
        for wrapper in wrappers:
            if not wrapper.get("reusable"):
                continue
            voce = wrapper["voce"]
            price = voce.prezzo_unitario
            if price in (None, 0):
                continue
            price_map[base_key] = {
                "price": price,
                "group_key": wrapper.get("full_key") or _wbs_key_from_parsed(voce),
            }
            break
    return price_map


def _build_description_price_map(
    ritorno_voci: Sequence[ParsedVoce],
) -> dict[str, list[float]]:
    mapping: dict[str, list[float]] = defaultdict(list)
    for voce in ritorno_voci:
        signature = _description_signature_from_parsed(voce)
        if not signature:
            continue
        mapping[signature].append(voce.prezzo_unitario or 0.0)
    return dict(mapping)


def _build_price_list_lookup(
    items: Sequence[PriceListItem],
) -> tuple[
    dict[str, list[PriceListItem]],
    dict[str, list[PriceListItem]],
    dict[str, list[PriceListItem]],
    dict[str, list[PriceListItem]],
    dict[str, list[PriceListItem]],
    dict[str, list[tuple[PriceListItem, list[float]]]],
]:
    code_map: dict[str, list[PriceListItem]] = defaultdict(list)
    signature_map: dict[str, list[PriceListItem]] = defaultdict(list)
    description_map: dict[str, list[PriceListItem]] = defaultdict(list)
    head_signature_map: dict[str, list[PriceListItem]] = defaultdict(list)
    tail_signature_map: dict[str, list[PriceListItem]] = defaultdict(list)
    embedding_map: dict[str, list[tuple[PriceListItem, list[float]]]] = defaultdict(list)

    for item in items:
        code_token = _normalize_code_token(item.item_code)
        if code_token:
            code_map[code_token].append(item)

        signature = _description_signature(
            item.item_description,
            item.unit_label,
            item.wbs6_code,
        )
        if signature:
            signature_map[signature].append(item)

        desc_token = _normalize_description_token(item.item_description)
        if desc_token:
            description_map[desc_token].append(item)

        head_sig, tail_sig = _head_tail_signatures(item.item_description)
        if head_sig:
            head_signature_map[head_sig].append(item)
        if tail_sig:
            tail_signature_map[tail_sig].append(item)

        metadata = item.extra_metadata or {}
        if isinstance(metadata, dict):
            nlp_payload = metadata.get("nlp")
            if isinstance(nlp_payload, dict):
                embedding_info = semantic_embedding_service.extract_embedding_payload(nlp_payload)
                if isinstance(embedding_info, dict):
                    vector = embedding_info.get("vector")
                    model_id = embedding_info.get("model_id") or nlp_payload.get("model_id")
                    if model_id and model_id != semantic_embedding_service.model_id:
                        continue
                    if isinstance(vector, list) and vector:
                        normalized_wbs6 = _normalize_code_token(item.wbs6_code) or _SEMANTIC_DEFAULT_BUCKET
                        payload = (item, [float(val) for val in vector])
                        embedding_map[normalized_wbs6].append(payload)
                        embedding_map[_SEMANTIC_DEFAULT_BUCKET].append(payload)

    return (
        code_map,
        signature_map,
        description_map,
        head_signature_map,
        tail_signature_map,
        embedding_map,
    )


def _match_price_list_item_entry(
    parsed: ParsedVoce,
    code_map: dict[str, list[PriceListItem]],
    signature_map: dict[str, list[PriceListItem]],
    description_map: dict[str, list[PriceListItem]],
    head_signature_map: dict[str, list[PriceListItem]],
    tail_signature_map: dict[str, list[PriceListItem]],
    embedding_map: dict[str, list[tuple[PriceListItem, list[float]]]],
) -> PriceListItem | None:
    code_token = _normalize_code_token(parsed.codice)
    if code_token:
        candidates = code_map.get(code_token, [])
        candidate = _select_price_list_item_candidate(candidates, parsed)
        if candidate:
            return candidate

    signature = _description_signature_from_parsed(parsed)
    if signature:
        candidate = _select_price_list_item_candidate(
            signature_map.get(signature, []),
            parsed,
        )
        if candidate:
            return candidate

    desc_token = _normalize_description_token(parsed.descrizione)
    if desc_token:
        return _select_price_list_item_candidate(
            description_map.get(desc_token, []),
            parsed,
        )
    head_sig, tail_sig = _head_tail_signatures(parsed.descrizione)
    if head_sig:
        candidate = _select_price_list_item_candidate(
            head_signature_map.get(head_sig, []),
            parsed,
        )
        if candidate:
            return candidate
    if tail_sig:
        candidate = _select_price_list_item_candidate(
            tail_signature_map.get(tail_sig, []),
            parsed,
        )
        if candidate:
            return candidate
    return _match_price_list_item_semantic(parsed, embedding_map)


def _select_price_list_item_candidate(
    candidates: Sequence[PriceListItem],
    parsed: ParsedVoce,
) -> PriceListItem | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    parsed_wbs6 = _parsed_wbs6_code(parsed)
    if parsed_wbs6:
        normalized_wbs6 = _normalize_code_token(parsed_wbs6)
        filtered = [
            item
            for item in candidates
            if _normalize_code_token(item.wbs6_code) == normalized_wbs6
        ]
        if len(filtered) == 1:
            return filtered[0]
        if filtered:
            candidates = filtered

    return sorted(
        candidates,
        key=lambda item: (item.item_code or item.product_id or "").lower(),
    )[0]


def _parsed_wbs6_code(parsed: ParsedVoce) -> str | None:
    for level in parsed.wbs_levels:
        if getattr(level, "level", None) == 6:
            if level.code:
                return level.code
            if level.description:
                return level.description
    return None


def _description_signature(
    description: str | None,
    unit: str | None,
    wbs6_code: str | None,
) -> str | None:
    # We now rely exclusively on the extended description so we can match Excel
    # rows regardless of how codes, units or WBS labels were exported.
    token = _normalize_description_token(description)
    if not token:
        return None
    return token


def _description_signature_from_parsed(voce: ParsedVoce) -> str | None:
    wbs6_code = None
    for level in voce.wbs_levels:
        if level.level == 6:
            wbs6_code = level.code or level.description
            break
    return _description_signature(voce.descrizione, voce.unita_misura, wbs6_code)


def _description_signature_from_model(voce: VoceComputo) -> str | None:
    return _description_signature(voce.descrizione, voce.unita_misura, voce.wbs_6_code)


_SEMANTIC_DEFAULT_BUCKET = "__all__"
_SEMANTIC_MIN_SCORE = 0.58
_HEAD_TAIL_WORD_LIMIT = 30
_WORD_TOKENIZER = re.compile(r"[A-Za-z0-9]+")


def _head_tail_signatures(
    description: str | None,
    limit: int = _HEAD_TAIL_WORD_LIMIT,
) -> tuple[str, str]:
    if not description:
        return "", ""
    tokens = _tokenize_words(description)
    if not tokens:
        return "", ""
    head_tokens = tokens[:limit]
    tail_tokens = tokens[-limit:] if len(tokens) > limit else tokens
    return " ".join(head_tokens), " ".join(tail_tokens)


def _tokenize_words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    return _WORD_TOKENIZER.findall(normalized)


def _match_price_list_item_semantic(
    parsed: ParsedVoce,
    embedding_map: dict[str, list[tuple[PriceListItem, list[float]]]],
) -> PriceListItem | None:
    if not embedding_map:
        return None
    text = _compose_semantic_text_from_parsed(parsed)
    if not text:
        return None
    try:
        query_vector = semantic_embedding_service.embed_text(text)
    except RuntimeError:
        return None
    if not query_vector:
        return None

    normalized_wbs6 = _normalize_code_token(_parsed_wbs6_code(parsed)) or _SEMANTIC_DEFAULT_BUCKET
    candidate_buckets = [
        embedding_map.get(normalized_wbs6, []),
        embedding_map.get(_SEMANTIC_DEFAULT_BUCKET, []),
    ]

    best_score = _SEMANTIC_MIN_SCORE
    best_item: PriceListItem | None = None
    seen_ids: set[int] = set()
    for bucket in candidate_buckets:
        if not bucket:
            continue
        for item, vector in bucket:
            if item.id in seen_ids:
                continue
            seen_ids.add(item.id)
            if not vector or len(vector) != len(query_vector):
                continue
            try:
                score = float(sum(float(a) * float(b) for a, b in zip(query_vector, vector)))
            except (TypeError, ValueError):
                continue
            if score > best_score:
                best_score = score
                best_item = item
    return best_item




def _build_matching_report(
    legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]],
    excel_only_labels: Sequence[str] | None = None,
    excel_only_groups: Sequence[str] | None = None,
    quantity_mismatches: Sequence[str] | None = None,
    quantity_totals: dict[str, float] | None = None,
) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for legacy, parsed in legacy_pairs:
        project_label = _voce_label(legacy) if legacy else None
        excel_label = parsed.descrizione or parsed.codice or "Voce senza descrizione"
        project_quantity = legacy.quantita if legacy else None
        return_quantity = parsed.quantita
        quantity_delta = None
        if project_quantity is not None and return_quantity is not None:
            quantity_delta = return_quantity - project_quantity
        entry = {
            "project_label": project_label,
            "excel_label": excel_label,
            "price": parsed.prezzo_unitario,
            "project_quantity": project_quantity,
            "return_quantity": return_quantity,
            "quantity_delta": quantity_delta,
            # Mantieni "quantity" per retrocompatibilità
            "quantity": return_quantity,
        }
        metadata = parsed.metadata or {}
        if metadata.get("missing_from_return"):
            missing.append(entry)
        else:
            matched.append(entry)
    report = {
        "matched": matched,
        "missing": missing,
        "excel_only": list(excel_only_labels or []),
    }
    if excel_only_groups:
        report["excel_only_groups"] = list(excel_only_groups)
    if quantity_mismatches:
        report["quantity_mismatches"] = list(quantity_mismatches)
    if quantity_totals:
        report["quantity_totals"] = quantity_totals
        report["quantity_total_mismatch"] = (
            abs(quantity_totals.get("delta", 0.0)) > 1e-6
        )
    return report


def _describe_parsed_voce(voce: ParsedVoce) -> str:
    code = voce.codice or (f"PROG-{voce.progressivo}" if voce.progressivo is not None else "SENZA-CODICE")
    price = f"{voce.prezzo_unitario:.2f}" if isinstance(voce.prezzo_unitario, (int, float)) else "n/d"
    return f"{code} @ {price}"


def _log_unmatched_price_entries(entries: Sequence[ParsedVoce], limit: int = 5) -> None:
    samples = ", ".join(_describe_parsed_voce(voce) for voce in entries[:limit])
    logger.warning(
        "Import LC: %s righe non hanno trovato corrispondenza nel listino (prime: %s)",
        len(entries),
        samples or "n/d",
    )


def _log_price_conflicts(conflicts: Iterable[dict[str, Any]], limit: int = 5) -> None:
    conflicts = list(conflicts)
    if not conflicts:
        return
    formatted = []
    for entry in conflicts[:limit]:
        prices = entry.get("prices") or []
        formatted.append(
            f"{entry.get('item_code') or entry.get('price_list_item_id')} -> {sorted(prices)}"
        )
    logger.warning(
        "Import LC: %s codici con prezzi multipli (prime: %s)",
        len(conflicts),
        "; ".join(formatted) or "n/d",
    )


def _build_lc_matching_report(summary: dict[str, Any]) -> dict[str, Any]:
    price_items: Sequence[PriceListItem] = summary.get("price_items") or []
    matched_ids: set[int] = set(summary.get("matched_item_ids") or [])
    unmatched_entries: Sequence[ParsedVoce] = summary.get("unmatched_entries") or []

    missing_items = [
        {
            "price_list_item_id": item.id,
            "item_code": item.item_code,
            "item_description": item.item_description,
        }
        for item in price_items
        if item.id not in matched_ids
    ]

    unmatched_rows_sample = [
        _shorten_label(voce.descrizione or voce.codice or "voce senza descrizione")
        for voce in unmatched_entries[:10]
    ]

    return {
        "mode": "lc",
        "total_price_items": len(price_items),
        "matched_price_items": len(matched_ids),
        "missing_price_items": missing_items,
        "unmatched_rows_sample": unmatched_rows_sample,
        "price_conflicts": summary.get("conflicting_price_items") or [],
    }


def _build_project_description_buckets(
    progetto_voci: Sequence[VoceComputo],
) -> dict[str, list[tuple[VoceComputo, set[str]]]]:
    buckets: dict[str, list[tuple[VoceComputo, set[str]]]] = {}
    for voce in progetto_voci:
        key = _wbs_key_from_model(voce)
        if not key:
            continue
        tokens = _descr_tokens(voce.descrizione)
        buckets.setdefault(key, []).append((voce, tokens))
    return buckets


def _assign_wrapper_preferences(
    wrappers: Sequence[dict[str, Any]],
    project_buckets: dict[str, list[tuple[VoceComputo, set[str]]]],
) -> None:
    for wrapper in wrappers:
        base_key = wrapper.get("base_key")
        if not base_key:
            continue
        candidates = project_buckets.get(base_key)
        if not candidates:
            continue
        wrapper_tokens: set[str] = wrapper.get("tokens") or set()
        if not wrapper_tokens:
            continue
        best_voice: VoceComputo | None = None
        best_score = 0.0
        second_score = 0.0
        for voce, tokens in candidates:
            score = _jaccard_similarity(tokens, wrapper_tokens)
            if score > best_score:
                second_score = best_score
                best_score = score
                best_voice = voce
            elif score > second_score:
                second_score = score
        if best_voice and best_score >= 0.15 and (best_score - second_score) >= 0.01:
            wrapper["preferred_voice_id"] = best_voice.id


def _filter_entries_by_primary(
    entries: Sequence[tuple[ParsedVoce, VoceComputo]],
    primary: str | None,
) -> list[tuple[ParsedVoce, VoceComputo]]:
    if not primary:
        return list(entries)
    filtered: list[tuple[ParsedVoce, VoceComputo]] = []
    for parsed, legacy in entries:
        project_key = _wbs_key_from_model(legacy)
        project_primary, _ = _split_wbs_key(project_key)
        if project_primary == primary:
            filtered.append((parsed, legacy))
    return filtered


def _keys_from_voce_progetto(voce: VoceComputo) -> list[str]:
    keys: list[str] = []
    _append_description_tokens(keys, voce.descrizione)
    if voce.progressivo is not None:
        _append_token(keys, f"progressivo-{voce.progressivo}")
    _append_token(keys, voce.wbs_7_description)
    _append_token(keys, voce.wbs_6_description)
    _append_token(keys, voce.wbs_5_description)
    _append_token(keys, voce.wbs_4_description)
    _append_token(keys, voce.wbs_3_description)
    _append_token(keys, voce.wbs_2_description)
    _append_token(keys, voce.wbs_1_description)
    _append_token(keys, voce.wbs_7_code)
    _append_token(keys, voce.wbs_6_code)
    _append_token(keys, voce.wbs_5_code)
    _append_token(keys, voce.wbs_4_code)
    _append_token(keys, voce.wbs_3_code)
    _append_token(keys, voce.wbs_2_code)
    _append_token(keys, voce.wbs_1_code)
    _append_token(keys, voce.codice)
    if voce.progressivo is not None:
        _append_token(keys, f"progressivo-{voce.progressivo}")
    return keys


def _keys_from_parsed_voce(voce: ParsedVoce) -> list[str]:
    keys: list[str] = []
    _append_description_tokens(keys, voce.descrizione)
    _append_token(keys, voce.codice)
    for livello in voce.wbs_levels:
        _append_token(keys, livello.description)
        _append_token(keys, livello.code)
    if voce.progressivo is not None:
        _append_token(keys, f"progressivo-{voce.progressivo}")
    return keys


def _append_token(target: list[str], value: str | None) -> None:
    token = _normalize_token(value)
    if token and token not in target:
        target.append(token)

def _descr_tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens: set[str] = set()
    # Parole comuni da ignorare (articoli, preposizioni, congiunzioni)
    stopwords = {
        "per", "con", "dei", "del", "dalla", "dallo", "dalle", "dagli",
        "alla", "allo", "alle", "agli", "nella", "nello", "nelle", "negli",
        "sulla", "sullo", "sulle", "sugli", "della", "dello", "delle", "degli",
        "una", "uno", "gli", "le", "il", "lo", "la", "di", "da", "in", "su",
        "a", "e", "o", "ma", "se", "che", "the", "of", "and", "or", "for",
        "with", "from", "to", "in", "on", "at", "by"
    }

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    for segment in [normalized_text, *[part.strip() for part in normalized_text.split("\n") if part.strip()]]:
        token = _normalize_token(segment)
        if token and len(token) >= 6:
            tokens.add(token)

    for token in re.split(r"[^A-Za-z0-9]+", text):
        if len(token) >= 3 and token.lower() not in stopwords:
            tokens.add(token.lower())
    return tokens

def _append_description_tokens(target: list[str], value: str | None) -> None:
    """
    Tokenizza la descrizione in modo leggero:
    - intera descrizione / riga
    - singole parole con lunghezza >= 3 (abbassata da 4 a 3)
    Niente n-gram, altrimenti esplode il numero di chiavi.
    """
    if not value:
        return

    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    segments = [text]
    segments.extend(part.strip() for part in text.split("\n") if part.strip())

    # Stopwords da ignorare
    stopwords = {
        "per", "con", "dei", "del", "dalla", "dallo", "dalle", "dagli",
        "alla", "allo", "alle", "agli", "nella", "nello", "nelle", "negli",
        "sulla", "sullo", "sulle", "sugli", "della", "dello", "delle", "degli",
        "una", "uno", "gli", "le", "il", "lo", "la", "di", "da", "in", "su",
        "a", "e", "o", "ma", "se", "che"
    }

    for segment in segments:
        if not segment:
            continue
        # token "intera frase"
        _append_token(target, segment)

        # token parola singola (escluse stopwords)
        words = [
            w for w in re.split(r"[^A-Za-z0-9]+", segment)
            if len(w) >= 3 and w.lower() not in stopwords
        ]
        for word in words:
            _append_token(target, word)

def _normalize_token(value: str | None) -> str | None:
    if not value:
        return None
    normalized = unicodedata.normalize("NFKD", str(value))
    cleaned = "".join(ch.lower() for ch in normalized if ch.isalnum())
    return cleaned or None


def _pick_match(
    index: dict[str, list[dict[str, Any]]],
    keys: Sequence[str],
    voce_progetto: VoceComputo | None = None,
) -> ParsedVoce | None:
    """
    Versione ottimizzata: usa token pre-calcolati e limita il numero di candidati.
    """

    project_wbs_key = None
    project_base_key = None
    if voce_progetto:
        project_wbs_key = _wbs_key_from_model(voce_progetto)
        project_base_key = _base_wbs_key_from_key(project_wbs_key)
        if project_base_key:
            wbs_bucket = index.get(f"__wbs__:{project_base_key}")
            voce_wbs = _claim_wbs_bucket(wbs_bucket, voce_progetto)
            if voce_wbs:
                return voce_wbs

    if voce_progetto and voce_progetto.codice:
        token_code = _normalize_token(voce_progetto.codice)
        if token_code:
            bucket = index.get(token_code)
            if bucket:
                for wrapper in bucket:
                    base_scope = wrapper.get("base_key")
                    if base_scope and project_base_key and base_scope != project_base_key:
                        continue
                    preferred_id = wrapper.get("preferred_voice_id")
                    if (
                        preferred_id
                        and voce_progetto.id != preferred_id
                        and not wrapper.get("reusable")
                    ):
                        continue
                    if wrapper["used"]:
                        continue
                    voce_match = wrapper["voce"]
                    metadata = getattr(voce_match, "metadata", {}) or {}
                    if metadata.get("group_total_only"):
                        continue
                    wrapper["matched"] = True
                    wrapper["used"] = True
                    return voce_match

    # 2) Candidati da keys (ma evitando duplicati)
    candidates: list[dict[str, Any]] = []
    seen_wrappers: set[int] = set()
    for key in keys:
        if len(key) < 4:
            continue
        bucket = index.get(key)
        if not bucket:
            continue
        for wrapper in bucket:
            base_scope = wrapper.get("base_key")
            if base_scope and project_base_key and base_scope != project_base_key:
                continue
            preferred_id = wrapper.get("preferred_voice_id")
            if (
                preferred_id
                and voce_progetto
                and voce_progetto.id != preferred_id
                and not wrapper.get("reusable")
            ):
                continue
            wid = id(wrapper)
            if wid in seen_wrappers:
                continue
            if wrapper["used"]:
                continue
            seen_wrappers.add(wid)
            candidates.append(wrapper)
        # opzionale: hard cap per sicurezza
        if len(candidates) >= 100:
            break

    if not candidates:
        return None

    project_tokens = _descr_tokens(
        voce_progetto.descrizione if voce_progetto else None
    )
    if not project_tokens:
        return None

    # 3) Pre-filtra: almeno 1 parola forte in comune (abbassata da 2 a 1)
    filtered: list[tuple[dict[str, Any], set[str]]] = []
    for wrapper in candidates:
        ret_tokens = wrapper.get("tokens") or set()
        if len(project_tokens & ret_tokens) >= 1:
            filtered.append((wrapper, ret_tokens))

    if not filtered:
        return None

    # Limitiamo ulteriormente per sicurezza
    filtered = filtered[:30]

    # 4) Similarità Jaccard (soglia abbassata da 0.10 a 0.05)
    best_score = 0.0
    best_wrapper: dict[str, Any] | None = None
    for wrapper, ret_tokens in filtered:
        score = _jaccard_similarity(project_tokens, ret_tokens)
        if score > best_score:
            best_score = score
            best_wrapper = wrapper

    if not best_wrapper or best_score < 0.05:
        best_wrapper = _match_by_description_similarity(
            voce_progetto,
            [wrapper for wrapper in candidates if not wrapper.get("used")],
        )
        if not best_wrapper:
            return None

    voce = best_wrapper["voce"]
    best_wrapper["matched"] = True
    best_wrapper["used"] = True
    return voce


def _claim_wbs_bucket(
    bucket: list[dict[str, Any]] | None,
    voce_progetto: VoceComputo | None,
) -> ParsedVoce | None:
    if not bucket:
        return None
    project_tokens = _descr_tokens(voce_progetto.descrizione if voce_progetto else None)
    preferred_id = voce_progetto.id if voce_progetto else None
    best_wrapper: dict[str, Any] | None = None
    best_score = -1.0
    for wrapper in bucket:
        if wrapper["used"]:
            continue
        metadata = getattr(wrapper["voce"], "metadata", {}) or {}
        if metadata.get("group_total_only"):
            continue
        wrapper_preferred = wrapper.get("preferred_voice_id")
        if (
            preferred_id
            and wrapper_preferred
            and wrapper_preferred != preferred_id
            and not wrapper.get("reusable")
        ):
            continue
        if project_tokens and wrapper.get("tokens"):
            score = _jaccard_similarity(project_tokens, wrapper["tokens"])
        else:
            score = 0.0
        if score > best_score:
            best_score = score
            best_wrapper = wrapper
    if not best_wrapper:
        return None
    best_wrapper["matched"] = True
    base_scope = best_wrapper.get("base_key")
    if not (best_wrapper.get("reusable") and base_scope and voce_progetto):
        best_wrapper["used"] = True
    else:
        project_base = _base_wbs_key_from_key(_wbs_key_from_model(voce_progetto))
        if project_base != base_scope:
            best_wrapper["used"] = True
    voce = best_wrapper["voce"]
    if best_wrapper.get("reusable"):
        voce = copy.deepcopy(voce)
    return voce

def _voce_label(voce: VoceComputo) -> str:
    parts: list[str] = []
    if voce.progressivo is not None:
        parts.append(f"progressivo {voce.progressivo}")
    if voce.codice:
        parts.append(voce.codice)
    if voce.descrizione:
        parts.append(voce.descrizione)
    return " - ".join(parts) or f"Voce ordine {voce.ordine}"


def _sum_project_quantities(voci: Sequence[VoceComputo]) -> Decimal | None:
    total = Decimal("0")
    count = 0
    for voce in voci:
        if voce.quantita is None:
            continue
        total += Decimal(str(voce.quantita))
        count += 1
    return total if count else None


def _format_quantity_value(value: Decimal) -> str:
    text = format(value, ".4f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _progress_price_key(voce: VoceComputo | None) -> tuple[int, str] | None:
    if voce is None or voce.progressivo is None:
        return None
    return (voce.progressivo, _normalize_code_token(voce.codice) or "")


def _has_progressivi(voci: Sequence[ParsedVoce]) -> bool:
    return any(getattr(voce, "progressivo", None) is not None for voce in voci)


def _quantities_match(
    project_value: float | None, offered_value: float | None, tolerance: float = 1e-4
) -> bool:
    if project_value in (None,) or offered_value in (None,):
        return True
    project_dec = Decimal(str(project_value))
    offered_dec = Decimal(str(offered_value))
    return abs(project_dec - offered_dec) <= Decimal(str(tolerance))


def _prices_match(
    first_value: float | None, second_value: float | None, tolerance: float = 1e-2
) -> bool:
    if first_value in (None,) or second_value in (None,):
        return True
    first_dec = Decimal(str(first_value))
    second_dec = Decimal(str(second_value))
    return abs(first_dec - second_dec) <= Decimal(str(tolerance))


def _shorten_label(label: str, limit: int = 120) -> str:
    text = label.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _match_by_description_similarity(
    voce_progetto: VoceComputo | None,
    candidates: Sequence[dict[str, Any]],
    *,
    min_ratio: float = 0.30,  # Abbassata da 0.45 a 0.30 per matching più permissivo
) -> dict[str, Any] | None:
    if not voce_progetto or not candidates:
        return None
    target_tokens = _descr_tokens(voce_progetto.descrizione)
    if not target_tokens:
        return None
    best_ratio = 0.0
    best_wrapper: dict[str, Any] | None = None
    for wrapper in candidates:
        if wrapper.get("used"):
            continue
        voce = wrapper["voce"]
        metadata = getattr(voce, "metadata", {}) or {}
        if metadata.get("group_total_only"):
            continue
        candidate_tokens = wrapper.get("tokens") or _descr_tokens(voce.descrizione)
        if not candidate_tokens:
            continue
        overlap = target_tokens & candidate_tokens
        denom = max(len(target_tokens), len(candidate_tokens))
        if denom == 0:
            continue
        ratio = len(overlap) / denom
        if ratio > best_ratio:
            best_ratio = ratio
            best_wrapper = wrapper
    if not best_wrapper or best_ratio < min_ratio:
        return None
    return best_wrapper


def _match_excel_entry_fuzzy(
    voce_progetto: VoceComputo,
    excel_entries: Sequence[dict[str, Any]],
    candidate_indices: list[int],
    *,
    min_ratio: float = 0.30,
) -> int | None:
    if not candidate_indices:
        return None
    tokens = _descr_tokens(voce_progetto.descrizione)
    if not tokens:
        return None
    best_ratio = 0.0
    best_idx: int | None = None
    for idx in candidate_indices:
        entry_tokens = excel_entries[idx]["tokens"]
        if not entry_tokens:
            continue
        overlap = tokens & entry_tokens
        denom = len(tokens | entry_tokens)
        if denom == 0:
            continue
        ratio = len(overlap) / denom
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = idx
    if best_idx is None or best_ratio < min_ratio:
        return None
    return best_idx


_FORCED_ZERO_CODE_PREFIXES = ("A004010",)
_FORCED_ZERO_DESCRIPTION_KEYWORDS = (
    "mark up fee",
    "mark-up fee",
    "markup fee",
)


def _detect_forced_zero_violations(voci: Sequence[ParsedVoce]) -> list[str]:
    alerts: list[str] = []
    for voce in voci:
        if not _is_forced_zero_voce(voce):
            continue
        fields: list[str] = []
        if _is_nonzero(voce.quantita):
            fields.append(f"Q={_format_quantity_for_warning(voce.quantita)}")
        if _is_nonzero(voce.prezzo_unitario):
            fields.append(f"P={format(voce.prezzo_unitario, '.2f')}")
        if _is_nonzero(voce.importo):
            fields.append(f"I={format(voce.importo, '.2f')}")
        if fields:
            label = voce.codice or (voce.descrizione or "voce senza descrizione")
            alerts.append(f"{_shorten_label(label)} ({', '.join(fields)})")
    return alerts


def _is_nonzero(value: float | None, tolerance: float = 1e-6) -> bool:
    return value is not None and abs(value) > tolerance


def _is_forced_zero_voce(voce: ParsedVoce) -> bool:
    return _requires_zero_guard(voce.codice, voce.descrizione)


def _requires_zero_guard(code: str | None, description: str | None) -> bool:
    code_token = _normalize_code_token(code)
    if code_token:
        for prefix in _FORCED_ZERO_CODE_PREFIXES:
            if code_token.startswith(prefix):
                return True
    description_token = _normalize_description_token(description)
    if not description_token:
        return False
    return any(keyword in description_token for keyword in _FORCED_ZERO_DESCRIPTION_KEYWORDS)


def _build_zero_guard_entry(
    codice: str | None,
    descrizione: str | None,
    quantita: float | None,
    prezzo: float | None,
    importo: float | None,
) -> ParsedVoce:
    return ParsedVoce(
        ordine=0,
        progressivo=None,
        codice=codice,
        descrizione=descrizione,
        wbs_levels=[],
        unita_misura=None,
        quantita=quantita,
        prezzo_unitario=prezzo,
        importo=importo,
        note=None,
        metadata=None,
    )


def _detect_duplicate_progressivi(voci: Sequence[ParsedVoce]) -> list[str]:
    by_progressivo: dict[int, list[ParsedVoce]] = defaultdict(list)
    for voce in voci:
        if voce.progressivo is None:
            continue
        by_progressivo[voce.progressivo].append(voce)
    duplicates: list[str] = []
    for progressivo, items in by_progressivo.items():
        if len(items) <= 1:
            continue
        codes = {voce.codice or "" for voce in items if voce.codice}
        label = f"{progressivo}" + (f" ({', '.join(sorted(codes))})" if codes else "")
        duplicates.append(_shorten_label(label))
    return duplicates


def _normalize_code_token(code: str | None) -> str:
    if not code:
        return ""
    normalized = str(code).upper()
    return re.sub(r"[^A-Z0-9]", "", normalized)


def _normalize_description_token(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _format_quantity_for_warning(value: float) -> str:
    text = format(value, ".4f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _price_bundle(voce: ParsedVoce) -> tuple[float | None, float | None, float | None]:
    prezzo = voce.prezzo_unitario
    quantita = voce.quantita
    importo = voce.importo
    return (
        round(prezzo, 4) if prezzo is not None else None,
        quantita,
        _ceil_amount(importo) if importo is not None else None,
    )


def _stabilize_return_price(
    value: float,
    reference_price: float | None,
) -> tuple[float, bool]:
    if reference_price in (None, 0):
        return value, False

    safe_reference = abs(reference_price)
    if safe_reference < 1e-6:
        return value, False

    # NEW: se il prezzo di riferimento è troppo basso (tipico delle voci a corpo
    # con Q.t = 0), non tentiamo di normalizzare: il valore di ritorno è più
    # affidabile del progetto.
    if safe_reference < 1:
        return value, False

    adjusted = value
    ratio = abs(adjusted) / safe_reference
    if ratio <= 250 or abs(adjusted) < 1000:
        return value, False

    for _ in range(4):
        adjusted /= 1000
        ratio = abs(adjusted) / safe_reference
        if ratio <= 250 or abs(adjusted) < 1000:
            return adjusted, True

    return value, False


def _wbs_key_from_model(voce: VoceComputo) -> str | None:
    primary = None
    for value in (
        voce.wbs_6_code,
        voce.wbs_6_description,
        voce.wbs_5_code,
        voce.wbs_5_description,
    ):
        token = _normalize_token(value)
        if token:
            primary = token
            break

    secondary = None
    for value in (
        voce.wbs_7_code,
        voce.wbs_7_description,
        voce.descrizione,
    ):
        token = _normalize_token(value)
        if token:
            secondary = token
            break

    if primary and secondary:
        return f"{primary}|{secondary}"
    return secondary or primary


def _wbs_key_from_parsed(voce: ParsedVoce) -> str | None:
    primary = None
    secondary = None
    description_token = _normalize_token(voce.descrizione)
    for livello in voce.wbs_levels:
        if livello.level == 6 and primary is None:
            primary = _normalize_token(livello.code) or _normalize_token(
                livello.description
            )
        if livello.level == 7 and secondary is None:
            secondary = _normalize_token(livello.code) or _normalize_token(
                livello.description
            )
    if secondary is None:
        secondary = (
            _normalize_token(voce.codice)
            or _normalize_token(voce.descrizione)
        )
    if primary and secondary:
        if description_token:
            return f"{primary}|{secondary}|{description_token}"
        return f"{primary}|{secondary}"
    if secondary and description_token and secondary != description_token:
        return f"{secondary}|{description_token}"
    return description_token or secondary or primary


def _wbs_base_key_from_parsed(voce: ParsedVoce) -> str | None:
    primary = None
    secondary = None
    for livello in voce.wbs_levels:
        if livello.level == 6 and primary is None:
            primary = _normalize_token(livello.code) or _normalize_token(
                livello.description
            )
        if livello.level == 7 and secondary is None:
            secondary = _normalize_token(livello.code) or _normalize_token(
                livello.description
            )
    if secondary is None:
        secondary = (
            _normalize_token(voce.codice)
            or _normalize_token(voce.descrizione)
        )
    if primary and secondary:
        return f"{primary}|{secondary}"
    return secondary or primary


def _split_wbs_key(key: str | None) -> tuple[str | None, str | None]:
    if not key:
        return None, None
    if "|" in key:
        primary, secondary = key.split("|", 1)
        return (primary or None), (secondary or None)
    return None, key


def _base_wbs_key_from_key(key: str | None) -> str | None:
    primary, secondary = _split_wbs_key(key)
    if primary and secondary:
        if "|" in secondary:
            secondary = secondary.split("|", 1)[0]
        return f"{primary}|{secondary}"
    if primary:
        return primary
    return secondary


def _collect_code_tokens(code: str | None) -> set[str]:
    if not code:
        return set()
    normalized = _normalize_token(code)
    tokens = set()
    if not normalized:
        return tokens
    tokens.add(normalized)
    segments = [segment for segment in re.split(r"[^A-Za-z0-9]+", code) if segment]
    builder = ""
    for segment in segments:
        cleaned = _normalize_token(segment)
        if not cleaned:
            continue
        builder += cleaned
        tokens.add(builder)
    return tokens


def _collect_description_tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens: set[str] = set()

    # Prima aggiungiamo il testo completo normalizzato (e le sue varianti per riga)
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    for segment in [normalized_text, *[part.strip() for part in normalized_text.split("\n") if part.strip()]]:
        token = _normalize_token(segment)
        if token and len(token) >= 6:
            tokens.add(token)

    # Poi aggiungiamo i singoli pezzi (come prima)
    for segment in re.split(r"[^A-Za-z0-9]+", text):
        token = _normalize_token(segment)
        if token and len(token) >= 4:
            tokens.add(token)
    return tokens


def _distribute_group_targets(
    excel_targets: dict[str, Decimal],
    matched_entries: dict[str, list[ParsedVoce]],
    project_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]],
    project_code_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]],
    project_primary_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]],
    project_description_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]],
    excel_details: dict[str, dict[str, Any]],
) -> tuple[int, set[str]]:
    resolved = 0
    satisfied_keys: set[str] = set()
    for key, target in excel_targets.items():
        details = excel_details.get(key, {})
        project_entries: list[tuple[ParsedVoce, VoceComputo]] | None = None

        primary = details.get("primary")
        if primary is None:
            primary, _ = _split_wbs_key(key)

        description_tokens = list(details.get("description_tokens") or [])
        for token in description_tokens:
            candidates = project_description_groups.get(token)
            if not candidates:
                continue
            filtered = _filter_entries_by_primary(candidates, primary)
            if filtered:
                project_entries = filtered
                break

        if not project_entries:
            code_tokens = list(details.get("code_tokens") or [])
            for token in code_tokens:
                candidates = project_code_groups.get(token)
                if not candidates:
                    continue
                filtered = _filter_entries_by_primary(candidates, primary)
                if filtered:
                    project_entries = filtered
                    break

        if not project_entries:
            base_key = _base_wbs_key_from_key(key)
            if base_key:
                project_entries = project_groups.get(base_key)
            if not project_entries:
                project_entries = project_groups.get(key)

        if not project_entries and primary:
            project_entries = project_primary_groups.get(primary)
        if not project_entries:
            continue
        matched_list = matched_entries.get(key, [])
        matched_ids = {id(entry) for entry in matched_list}
        unmatched_entries = [
            (parsed, legacy)
            for parsed, legacy in project_entries
            if id(parsed) not in matched_ids
            and (parsed.metadata or {}).get("missing_from_return")
        ]
        if not unmatched_entries:
            continue
        assigned_total = sum(
            Decimal(str(entry.importo))
            for entry in matched_list
            if entry.importo is not None
        )
        residual = (target - assigned_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if residual <= Decimal("0"):
            continue
        weight_values: list[Decimal] = []
        for _, legacy in unmatched_entries:
            base_value = legacy.importo
            if base_value is None and (
                legacy.quantita not in (None, 0)
                and legacy.prezzo_unitario is not None
            ):
                base_value = legacy.quantita * legacy.prezzo_unitario
            if base_value in (None, 0):
                weight_values.append(Decimal("0"))
            else:
                weight_values.append(Decimal(str(base_value)))
        total_weight = sum(weight_values)
        if total_weight <= Decimal("0"):
            weight_values = [Decimal("1")] * len(unmatched_entries)
            total_weight = Decimal(len(unmatched_entries))
        distributed = Decimal("0")
        allocated_any = False
        for index, ((parsed, legacy), weight) in enumerate(
            zip(unmatched_entries, weight_values)
        ):
            if index == len(unmatched_entries) - 1:
                share = residual - distributed
            else:
                share = (residual * weight / total_weight).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                distributed += share
            if share <= Decimal("0"):
                continue
            parsed.quantita = legacy.quantita
            parsed.importo = float(share)
            if legacy.quantita not in (None, 0):
                price = (share / Decimal(str(legacy.quantita))).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
                parsed.prezzo_unitario = float(price)
            elif legacy.prezzo_unitario is not None:
                parsed.prezzo_unitario = legacy.prezzo_unitario
            metadata = dict(parsed.metadata or {})
            metadata.pop("missing_from_return", None)
            metadata["group_allocation"] = {
                "wbs_key": key,
                "allocated_value": float(share),
            }
            parsed.metadata = metadata
            matched_entries.setdefault(key, []).append(parsed)
            resolved += 1
            allocated_any = True
        if allocated_any:
            satisfied_keys.add(key)
    return resolved, satisfied_keys


def _apply_rounding_to_match(
    entries: Sequence[ParsedVoce],
    target_total: Decimal,
) -> None:
    if not entries:
        return

    target_total = target_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    import_values: list[Decimal] = []
    quantities: list[Decimal | None] = []
    adjustable: list[tuple[Decimal, int]] = []
    fallback: list[tuple[Decimal, int]] = []

    for idx, voce in enumerate(entries):
        quantita_val = voce.quantita
        prezzo_val = voce.prezzo_unitario
        importo_val = voce.importo
        preserve_price = (voce.metadata or {}).get("lock_return_price")

        quant_dec: Decimal | None = None
        if quantita_val not in (None, 0):
            quant_dec = Decimal(str(quantita_val))

        price_dec: Decimal | None = None
        if prezzo_val is not None:
            price_dec = Decimal(str(prezzo_val)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        if quant_dec is not None and price_dec is not None:
            import_dec = (price_dec * quant_dec).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            voce.prezzo_unitario = float(price_dec)
            voce.importo = float(import_dec)
            if not preserve_price:
                adjustable.append((import_dec.copy_abs(), idx))
        elif importo_val is not None:
            import_dec = Decimal(str(importo_val)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            voce.importo = float(import_dec)
            if quant_dec is not None and not preserve_price:
                fallback.append((import_dec.copy_abs(), idx))
        else:
            import_dec = Decimal("0")

        import_values.append(import_dec)
        quantities.append(quant_dec)
        if not preserve_price and quant_dec is None and import_dec != Decimal("0"):
            fallback.append((import_dec.copy_abs(), idx))

    current_total = sum(import_values, Decimal("0"))
    difference = (target_total - current_total).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if difference == Decimal("0"):
        return

    candidates = adjustable if adjustable else fallback
    if not candidates:
        return

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    target_idx = candidates[0][1]

    new_import = (import_values[target_idx] + difference).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if new_import < Decimal("0"):
        new_import = Decimal("0")
    import_values[target_idx] = new_import

    voce = entries[target_idx]
    quant_dec = quantities[target_idx]
    if quant_dec not in (None, Decimal("0")):
        new_price = (new_import / quant_dec).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        voce.prezzo_unitario = float(new_price)
    voce.importo = float(new_import)
