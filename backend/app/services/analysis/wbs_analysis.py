from __future__ import annotations

from typing import Dict, Iterable, Tuple
import re

from sqlmodel import Session, select

from app.db.models import Computo, VoceComputo
from app.excel.parser import MAX_WBS_LEVELS
from app.schemas import AggregatedVoceSchema, ComputoWbsSummary, WbsNodeSchema, WbsPathEntrySchema
from app.services.wbs_visibility import WbsVisibilityService


class WbsAnalysisService:
    """Calcola aggregazioni WBS e lista lavorazioni per un computo."""

    @staticmethod
    def get_wbs_summary(session: Session, computo_id: int) -> ComputoWbsSummary:
        computo = session.get(Computo, computo_id)
        if not computo:
            raise ValueError("Computo non trovato")

        voci = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == computo_id)
            .order_by(VoceComputo.ordine)
        ).all()

        _normalize_voci_wbs(voci)
        hidden_codes_by_level = WbsVisibilityService.hidden_codes_by_level(
            session, computo.commessa_id
        )
        if hidden_codes_by_level:
            filtered: list[VoceComputo] = []
            for voce in voci:
                skip = False
                for level, codes in hidden_codes_by_level.items():
                    if not codes:
                        continue
                    if level == 7:
                        voce_code = getattr(voce, "wbs_7_code", None) or getattr(voce, "codice", None)
                    else:
                        voce_code = getattr(voce, f"wbs_{level}_code", None)
                    if voce_code and voce_code in codes:
                        skip = True
                        break
                if not skip:
                    filtered.append(voce)
            voci = filtered

        totale_importo = round(sum(voce.importo or 0 for voce in voci), 2)
        tree = _build_wbs_tree(voci)
        aggregate = _aggregate_voci(voci)

        return ComputoWbsSummary(
            importo_totale=totale_importo,
            tree=tree,
            voci=aggregate,
        )


def _build_wbs_tree(voci: Iterable[VoceComputo]) -> list[WbsNodeSchema]:
    root: Dict[Tuple[int, str | None, str | None], dict] = {}

    def get_child(
        container: dict, key: Tuple[int, str | None, str | None], ordine: int
    ):
        child = container.get(key)
        if child is None:
            child = {
                "level": key[0],
                "code": key[1],
                "description": key[2],
                "importo": 0.0,
                "children": {},
                "order": ordine,
            }
            container[key] = child
        else:
            child["order"] = min(child["order"], ordine)
        return child

    for voce in voci:
        importo = float(voce.importo or 0)
        node_children = root
        for level in range(1, MAX_WBS_LEVELS + 1):
            code = getattr(voce, f"wbs_{level}_code")
            desc = getattr(voce, f"wbs_{level}_description")
            if level == 7:
                code = getattr(voce, "wbs_7_code", None) or getattr(voce, "codice", None)
                desc = getattr(voce, "wbs_7_description", None)
            if level == 6 and not desc:
                desc = getattr(voce, "wbs_6_description", None)
            if not code and not desc:
                continue
            key = (level, code, desc)
            child = get_child(node_children, key, voce.ordine)
            child["importo"] += importo
            node_children = child["children"]

    return _convert_tree(root)


def _convert_tree(
    children: Dict[Tuple[int, str | None, str | None], dict],
) -> list[WbsNodeSchema]:
    nodes: list[WbsNodeSchema] = []
    for data in sorted(children.values(), key=lambda item: item["order"]):
        nodes.append(
            WbsNodeSchema(
                level=data["level"],
                code=data["code"],
                description=data["description"],
                importo=round(data["importo"], 2),
                children=_convert_tree(data["children"]),
            )
        )
    return nodes


def _aggregate_voci(voci: Iterable[VoceComputo]) -> list[AggregatedVoceSchema]:
    bucket: dict[str, dict] = {}
    for voce in voci:
        normalized_wbs6, normalized_wbs7 = _normalize_wbs_codes(
            voce.wbs_6_code, voce.wbs_7_code, voce.codice
        )

        path_entries: list[WbsPathEntrySchema] = []
        path_key_parts: list[str] = []

        for level in range(1, MAX_WBS_LEVELS + 1):
            code = getattr(voce, f"wbs_{level}_code", None)
            desc = getattr(voce, f"wbs_{level}_description", None)
            if level == 7 and not code:
                code = getattr(voce, "wbs_7_code", None) or getattr(voce, "codice", None)
                desc = getattr(voce, "wbs_7_description", None)
            if not code and not desc:
                continue
            entry = WbsPathEntrySchema(level=level, code=code, description=desc)
            path_entries.append(entry)
            if code:
                path_key_parts.append(f"L{level}:{code}")

        path_key = "|".join(path_key_parts) if path_key_parts else "root"
        progressivo_part = f"prog:{voce.progressivo}" if voce.progressivo is not None else "noprog"
        key = f"{path_key}::{progressivo_part}::{voce.codice or voce.descrizione or str(voce.id)}"
        entry = bucket.get(key)
        if entry is None:
            entry = {
                "progressivo": voce.progressivo,
                "codice": voce.codice,
                "descrizione": voce.descrizione,
                "quantita": 0.0,
                "importo": 0.0,
                "unita_misura": voce.unita_misura,
                "wbs_6_code": normalized_wbs6,
                "wbs_6_description": voce.wbs_6_description,
                "wbs_7_code": normalized_wbs7,
                "wbs_7_description": voce.wbs_7_description,
                "wbs_path": path_entries,
            }
            bucket[key] = entry
        else:
            if normalized_wbs6 and not entry.get("wbs_6_code"):
                entry["wbs_6_code"] = normalized_wbs6
            if normalized_wbs7 and not entry.get("wbs_7_code"):
                entry["wbs_7_code"] = normalized_wbs7
            if not entry.get("wbs_path"):
                entry["wbs_path"] = path_entries
            # Keep the minimum progressivo when aggregating
            if voce.progressivo is not None:
                if entry.get("progressivo") is None or voce.progressivo < entry["progressivo"]:
                    entry["progressivo"] = voce.progressivo

        entry["quantita"] += voce.quantita or 0.0
        entry["importo"] += voce.importo or 0.0
        if not entry.get("unita_misura") and voce.unita_misura:
            entry["unita_misura"] = voce.unita_misura

    aggregated: list[AggregatedVoceSchema] = []
    for entry in bucket.values():
        quantita = entry["quantita"]
        importo = entry["importo"]
        prezzo = None
        if quantita and abs(quantita) > 1e-9:
            prezzo = round(importo / quantita, 4)

        aggregated.append(
            AggregatedVoceSchema(
                progressivo=entry.get("progressivo"),
                codice=entry["codice"],
                descrizione=entry["descrizione"],
                quantita_totale=round(quantita, 6),
                importo_totale=round(importo, 2),
                prezzo_unitario=prezzo,
                unita_misura=entry.get("unita_misura"),
                wbs_6_code=entry["wbs_6_code"],
                wbs_6_description=entry["wbs_6_description"],
                wbs_7_code=entry["wbs_7_code"],
                wbs_7_description=entry["wbs_7_description"],
                wbs_path=entry.get("wbs_path", []),
            )
        )

    aggregated.sort(key=lambda item: (item.codice or "", item.descrizione or ""))
    return aggregated


_BASE_WBS_RE = re.compile(r"^([A-Za-z]\d{3})")
_BASE_WITH_SECOND_RE = re.compile(r"^([A-Za-z]\d{3})[.\s_-]?(\d{3})")


def _normalize_wbs_codes(
    wbs6: str | None, wbs7: str | None, codice: str | None
) -> tuple[str | None, str | None]:
    base, second = _extract_wbs_parts(wbs7, codice, wbs6)
    if base is None:
        return wbs6, wbs7
    if not second:
        second = "000"
    return base, f"{base}.{second}"


def _extract_wbs_parts(
    *candidates: str | None,
) -> tuple[str | None, str | None]:
    base: str | None = None
    second: str | None = None

    for candidate in candidates:
        if not candidate:
            continue
        text = str(candidate).strip()
        if not text:
            continue

        match = _BASE_WITH_SECOND_RE.match(text)
        if match:
            base = match.group(1)
            second = match.group(2)
            break

        match = _BASE_WBS_RE.match(text)
        if match:
            base = match.group(1)
            remainder = text[match.end() :]
            digits = re.search(r"(\d{3})", remainder)
            if digits:
                second = digits.group(1)
                break
            if base:
                second = second or None

    return base, second


def _normalize_voci_wbs(voci: Iterable[VoceComputo]) -> None:
    for voce in voci:
        normalized6, normalized7 = _normalize_wbs_codes(
            voce.wbs_6_code, voce.wbs_7_code, voce.codice
        )
        if normalized6:
            voce.wbs_6_code = normalized6
        if normalized7:
            voce.wbs_7_code = normalized7
