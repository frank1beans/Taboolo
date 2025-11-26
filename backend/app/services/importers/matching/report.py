"""
Generazione report e warning per matching.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Iterable, Sequence

from app.db.models import PriceListItem, VoceComputo
from app.excel import ParsedVoce

logger = logging.getLogger(__name__)


def voce_label(voce: VoceComputo) -> str:
    """Genera label descrittiva per VoceComputo."""
    parts: list[str] = []
    if voce.progressivo is not None:
        parts.append(f"progressivo {voce.progressivo}")
    if voce.codice:
        parts.append(voce.codice)
    if voce.descrizione:
        parts.append(voce.descrizione)
    return " - ".join(parts) or f"Voce ordine {voce.ordine}"


def shorten_label(label: str, limit: int = 120) -> str:
    """Accorcia label troppo lunga."""
    text = label.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_quantity_value(value: Decimal) -> str:
    """Formatta Decimal quantità per display (rimuove zeri trailing)."""
    text = format(value, ".4f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def format_quantity_for_warning(value: float) -> str:
    """Formatta float quantità per warning (rimuove zeri trailing)."""
    text = format(value, ".4f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def describe_parsed_voce(voce: ParsedVoce) -> str:
    """Descrizione breve ParsedVoce (codice @ prezzo)."""
    code = voce.codice or (
        f"PROG-{voce.progressivo}" if voce.progressivo is not None else "SENZA-CODICE"
    )
    price = (
        f"{voce.prezzo_unitario:.2f}"
        if isinstance(voce.prezzo_unitario, (int, float))
        else "n/d"
    )
    return f"{code} @ {price}"


def build_matching_report(
    legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]],
    excel_only_labels: Sequence[str] | None = None,
    excel_only_groups: Sequence[str] | None = None,
    quantity_mismatches: Sequence[str] | None = None,
    quantity_totals: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Costruisce report di matching tra progetto e ritorno.
    Include: voci matched, missing, excel_only, quantity mismatches.
    """
    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for legacy, parsed in legacy_pairs:
        project_label = voce_label(legacy) if legacy else None
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
        report["quantity_total_mismatch"] = abs(quantity_totals.get("delta", 0.0)) > 1e-6

    return report


def build_lc_matching_report(summary: dict[str, Any]) -> dict[str, Any]:
    """
    Costruisce report specifico per import LC (basato su listino prezzi).
    """
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
        shorten_label(voce.descrizione or voce.codice or "voce senza descrizione")
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


def log_unmatched_price_entries(entries: Sequence[ParsedVoce], limit: int = 5) -> None:
    """Log warning per entry non matched con listino."""
    samples = ", ".join(describe_parsed_voce(voce) for voce in entries[:limit])
    logger.warning(
        "Import LC: %s righe non hanno trovato corrispondenza nel listino (prime: %s)",
        len(entries),
        samples or "n/d",
    )


def log_price_conflicts(conflicts: Iterable[dict[str, Any]], limit: int = 5) -> None:
    """Log warning per conflitti prezzi multipli."""
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
