from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Optional, Sequence, Tuple

from sqlmodel import Session, select

from app.db.models import Computo, PriceListItem, VoceComputo
from app.db.models_wbs import Impresa, Voce as VoceNorm, Wbs6, Wbs7, WbsSpaziale
from app.excel import ParsedVoce, ParsedWbsLevel
from app.excel.parser import MAX_WBS_LEVELS


def sanitize_impresa_label(label: str | None) -> str | None:
    """Normalizza il nome impresa rimuovendo suffissi duplicati e spazi superflui."""
    if not label:
        return None
    text = label.strip()
    if not text:
        return None
    text = re.sub(r"\s*\(\d+\)\s*$", "", text).strip()
    return text or None


def _ceil_decimal_value(value: float | Decimal | int, exponent: str) -> Decimal:
    decimal_value = Decimal(str(value))
    return decimal_value.quantize(Decimal(exponent), rounding=ROUND_HALF_UP)


def _ceil_quantity(value: float | Decimal | int | None) -> float | None:
    if value is None:
        return None
    return float(_ceil_decimal_value(value, "0.000001"))


def _ceil_amount(value: float | Decimal | int | None) -> float | None:
    if value is None:
        return None
    return float(_ceil_decimal_value(value, "0.01"))


def _calculate_line_amount(
    quantita: float | Decimal | None,
    prezzo: float | None,
) -> tuple[float | None, float | None]:
    """
    Calcola importo da quantità e prezzo usando logica consistente con importer.
    Restituisce (quantita, importo) arrotondati.
    """
    if quantita is None or prezzo is None:
        return quantita, None

    decimal_qty = Decimal(str(quantita))
    decimal_price = Decimal(str(prezzo))

    if decimal_qty == Decimal("0"):
        return 0.0, 0.0

    line_amount = (decimal_qty * decimal_price).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return float(decimal_qty), float(line_amount)


def _normalize_wbs6_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return text or None


def _normalize_wbs7_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = re.sub(r"[^A-Za-z0-9._-]", "", str(value)).upper()
    return text or None


def _looks_like_wbs7_code(value: Optional[str]) -> bool:
    if not value:
        return False
    text = str(value).strip().upper()
    if not any(sep in text for sep in (".", "_", "-")):
        return False
    if len(text) < 3:
        return False
    return bool(re.match(r"^[A-Z0-9]{1,10}(?:[._-][A-Z0-9]+)+$", text))


def _map_wbs_levels(levels: Sequence) -> dict[str, str | None]:
    data: dict[str, str | None] = {}
    by_level = {level.level: level for level in levels}
    for idx in range(1, MAX_WBS_LEVELS + 1):
        entry = by_level.get(idx)
        data[f"wbs_{idx}_code"] = entry.code if entry else None
        data[f"wbs_{idx}_description"] = entry.description if entry else None
    return data


def _normalize_commessa_tag(commessa_id: int | None, commessa_code: str | None) -> str | None:
    code = (commessa_code or "commessa").strip() or "commessa"
    identifier = commessa_id or 0
    return f"{identifier}::{code}"


def _build_global_voce_code(commessa_tag: str | None, parsed: ParsedVoce) -> str | None:
    if not commessa_tag:
        return None
    base = parsed.codice or (
        f"PROG-{parsed.progressivo}"
        if parsed.progressivo is not None
        else f"ORD-{parsed.ordine}"
    )
    if not base:
        return None
    normalized_code = str(base).strip()
    if not normalized_code:
        return None
    wbs6_code = None
    for livello in parsed.wbs_levels:
        if getattr(livello, "level", None) == 6 and getattr(livello, "code", None):
            wbs6_code = livello.code
            break
    suffix = normalized_code
    if wbs6_code:
        suffix = f"{suffix}@{wbs6_code}"
    return f"{commessa_tag}::{suffix}"


class BaseImportService:
    """Metodi e utilità condivise tra import MC e LC."""

    @staticmethod
    def _sanitize_impresa_label(label: str | None) -> str | None:
        return sanitize_impresa_label(label)

    def _bulk_insert_voci(
        self,
        session: Session,
        computo: Computo,
        voci: Iterable[ParsedVoce],
    ) -> list[VoceComputo]:
        session.exec(
            VoceComputo.__table__.delete().where(VoceComputo.computo_id == computo.id)
        )

        voce_models = []
        commessa_id = computo.commessa_id
        commessa_code = getattr(computo, "commessa_code", None)
        commessa_tag = _normalize_commessa_tag(commessa_id, commessa_code)
        for parsed in voci:
            wbs_kwargs = _map_wbs_levels(parsed.wbs_levels)
            global_code = _build_global_voce_code(commessa_tag, parsed)

            voce_models.append(
                VoceComputo(
                    commessa_id=commessa_id,
                    commessa_code=commessa_code,
                    computo_id=computo.id,
                    global_code=global_code,
                    progressivo=parsed.progressivo,
                    codice=parsed.codice,
                    descrizione=parsed.descrizione,
                    unita_misura=parsed.unita_misura,
                    quantita=parsed.quantita,
                    prezzo_unitario=parsed.prezzo_unitario,
                    importo=parsed.importo,
                    note=parsed.note,
                    ordine=parsed.ordine,
                    extra_metadata=parsed.metadata,
                    **wbs_kwargs,
                )
            )

        session.add_all(voce_models)
        session.flush()
        return voce_models


class _WbsNormalizeContext:
    """Gestisce la creazione/ricerca dei nodi WBS e delle voci normalizzate."""

    def __init__(self, session: Session, commessa_id: int) -> None:
        self.session = session
        self.commessa_id = commessa_id
        self.spatial_cache: Dict[Tuple[int, int, str], WbsSpaziale] = {}
        self.wbs6_cache: Dict[str, Wbs6] = {}
        self.wbs7_cache: Dict[Tuple[int, Optional[str]], Wbs7] = {}
        self.voce_cache: Dict[Tuple[int, Optional[int], Optional[str], int], VoceNorm] = {}
        self.voce_by_legacy: Dict[int, VoceNorm] = {}
        self.impresa_cache: Dict[str, Impresa] = {}
        self._price_list_item_cache: Dict[str, Optional[int]] = {}

    def ensure_voce(
        self,
        parsed: ParsedVoce,
        legacy: Optional[VoceComputo],
        *,
        price_list_item_id: Optional[int] = None,
    ) -> Optional[VoceNorm]:
        info = self._analyze_parsed(parsed)
        if not info:
            return None
        spatial_levels, wbs6_code, wbs6_desc, wbs7_code, wbs7_desc = info
        spatial_leaf = self._ensure_spatial_hierarchy(spatial_levels)
        wbs6 = self._ensure_wbs6(wbs6_code, wbs6_desc, spatial_leaf)
        wbs7 = self._ensure_wbs7(wbs6, wbs7_code, wbs7_desc)
        resolved_price_list_id = price_list_item_id or self.resolve_price_list_item_id(parsed)

        target_wbs7_id = wbs7.id if wbs7 else None
        # Include progressivo nella chiave per evitare aggregazioni non volute
        # quando lo stesso prodotto appare in WBS6/WBS7 uguali con progressivi diversi
        key = (wbs6.id, target_wbs7_id, parsed.codice, parsed.progressivo, parsed.ordine)
        voce = self.voce_cache.get(key)
        if not voce and legacy:
            voce = self.get_voce_from_legacy(legacy.id)
        if not voce:
            # Cerca prima per legacy_id se disponibile per preservare riferimenti esistenti
            if legacy and legacy.id:
                voce = self.session.exec(
                    select(VoceNorm).where(
                        VoceNorm.legacy_vocecomputo_id == legacy.id
                    )
                ).first()
            # Altrimenti cerca per chiave naturale includendo progressivo
            if not voce:
                stmt = select(VoceNorm).where(
                    VoceNorm.commessa_id == self.commessa_id,
                    VoceNorm.wbs6_id == wbs6.id,
                    VoceNorm.wbs7_id == target_wbs7_id,
                    VoceNorm.codice == parsed.codice,
                    VoceNorm.ordine == parsed.ordine,
                )
                # Aggiungi progressivo solo se presente (per compatibilità con import senza progressivo)
                if parsed.progressivo is not None:
                    stmt = stmt.where(VoceNorm.progressivo == parsed.progressivo)
                voce = self.session.exec(stmt).first()
        if voce:
            updated = False
            if voce.wbs6_id != wbs6.id:
                voce.wbs6_id = wbs6.id
                updated = True
            if voce.wbs7_id != target_wbs7_id:
                voce.wbs7_id = target_wbs7_id
                updated = True
            if voce.codice != parsed.codice:
                voce.codice = parsed.codice
                updated = True
            if voce.ordine != parsed.ordine:
                voce.ordine = parsed.ordine
                updated = True
            if parsed.descrizione and voce.descrizione != parsed.descrizione:
                voce.descrizione = parsed.descrizione
                updated = True
            if parsed.unita_misura and voce.unita_misura != parsed.unita_misura:
                voce.unita_misura = parsed.unita_misura
                updated = True
            if parsed.note and voce.note != parsed.note:
                voce.note = parsed.note
                updated = True
            if legacy and voce.legacy_vocecomputo_id is None:
                voce.legacy_vocecomputo_id = legacy.id
                updated = True
            if resolved_price_list_id and voce.price_list_item_id is None:
                voce.price_list_item_id = resolved_price_list_id
                updated = True
            if updated:
                self.session.add(voce)
        else:
            voce = VoceNorm(
                commessa_id=self.commessa_id,
                wbs6_id=wbs6.id,
                wbs7_id=target_wbs7_id,
                progressivo=parsed.progressivo,
                codice=parsed.codice,
                descrizione=parsed.descrizione,
                unita_misura=parsed.unita_misura,
                note=parsed.note,
                ordine=parsed.ordine,
                legacy_vocecomputo_id=legacy.id if legacy else None,
                price_list_item_id=resolved_price_list_id,
            )
            self.session.add(voce)
            self.session.flush()
        self.voce_cache[key] = voce
        if voce.legacy_vocecomputo_id:
            self.voce_by_legacy[voce.legacy_vocecomputo_id] = voce
        return voce

    def get_voce_from_legacy(self, legacy_id: int) -> Optional[VoceNorm]:
        voce = self.voce_by_legacy.get(legacy_id)
        if voce:
            return voce
        voce = self.session.exec(
            select(VoceNorm).where(VoceNorm.legacy_vocecomputo_id == legacy_id)
        ).first()
        if voce:
            self.voce_by_legacy[legacy_id] = voce
            key = (voce.wbs6_id, voce.wbs7_id, voce.codice, voce.ordine)
            self.voce_cache[key] = voce
        return voce

    def get_or_create_impresa(self, label: Optional[str]) -> Optional[Impresa]:
        if not label:
            return None
        label = sanitize_impresa_label(label)
        if not label:
            return None
        normalized = re.sub(r"\s+", " ", label.strip()).lower()
        if not normalized:
            return None
        impresa = self.impresa_cache.get(normalized)
        if impresa:
            return impresa
        impresa = self.session.exec(
            select(Impresa).where(Impresa.normalized_label == normalized)
        ).first()
        if not impresa:
            impresa = Impresa(label=label.strip(), normalized_label=normalized)
            self.session.add(impresa)
            self.session.flush()
        self.impresa_cache[normalized] = impresa
        return impresa

    def resolve_price_list_item_id(self, parsed: ParsedVoce) -> Optional[int]:
        metadata = parsed.metadata or {}
        product_id = metadata.get("product_id")
        if not product_id:
            return None
        cached = self._price_list_item_cache.get(product_id)
        if cached is not None:
            return cached
        item = self.session.exec(
            select(PriceListItem).where(
                PriceListItem.commessa_id == self.commessa_id,
                PriceListItem.product_id == product_id,
            )
        ).first()
        item_id = item.id if item else None
        self._price_list_item_cache[product_id] = item_id
        return item_id

    def _analyze_parsed(
        self,
        parsed: ParsedVoce,
    ) -> Optional[Tuple[list[ParsedWbsLevel], str, Optional[str], Optional[str], Optional[str]]]:
        spatial = [lvl for lvl in parsed.wbs_levels if lvl.level <= 5]
        wbs6_level = next((lvl for lvl in parsed.wbs_levels if lvl.level == 6), None)
        wbs7_level = next((lvl for lvl in parsed.wbs_levels if lvl.level == 7), None)
        wbs6_code = _normalize_wbs6_code(wbs6_level.code if wbs6_level else None)
        if not wbs6_code:
            return None
        wbs6_desc = (wbs6_level.description if wbs6_level else None) or f"WBS6 {wbs6_code}"
        wbs7_code = _normalize_wbs7_code(wbs7_level.code if wbs7_level else None)
        wbs7_desc = wbs7_level.description if wbs7_level else None
        return spatial, wbs6_code, wbs6_desc, wbs7_code, wbs7_desc

    def _ensure_spatial_hierarchy(self, levels: Sequence[ParsedWbsLevel]) -> Optional[WbsSpaziale]:
        parent: Optional[WbsSpaziale] = None
        last: Optional[WbsSpaziale] = None
        for lvl in levels:
            code = (lvl.code or "").strip()
            if not code:
                continue
            key = (self.commessa_id, lvl.level, code)
            node = self.spatial_cache.get(key)
            if not node:
                node = self.session.exec(
                    select(WbsSpaziale).where(
                        WbsSpaziale.commessa_id == self.commessa_id,
                        WbsSpaziale.level == lvl.level,
                        WbsSpaziale.code == code,
                    )
                ).first()
            if not node:
                node = WbsSpaziale(
                    commessa_id=self.commessa_id,
                    parent_id=parent.id if parent else None,
                    level=lvl.level,
                    code=code,
                    description=lvl.description,
                )
                self.session.add(node)
                self.session.flush()
            self.spatial_cache[key] = node
            parent = node
            last = node
        return last

    def _ensure_wbs6(
        self,
        code: str,
        description: Optional[str],
        spatial_leaf: Optional[WbsSpaziale],
    ) -> Wbs6:
        node = self.wbs6_cache.get(code)
        if not node:
            node = self.session.exec(
                select(Wbs6).where(
                    Wbs6.commessa_id == self.commessa_id,
                    Wbs6.code == code,
                )
            ).first()
        if not node:
            desc = description or f"WBS6 {code}"
            if desc and desc.lower().startswith(code.lower()):
                label = desc
            else:
                label = f"{code} - {desc}" if desc else code
            node = Wbs6(
                commessa_id=self.commessa_id,
                wbs_spaziale_id=spatial_leaf.id if spatial_leaf else None,
                code=code,
                description=desc,
                label=label,
            )
            self.session.add(node)
            self.session.flush()
        self.wbs6_cache[code] = node
        return node

    def _ensure_wbs7(
        self,
        wbs6: Wbs6,
        code: Optional[str],
        description: Optional[str],
    ) -> Optional[Wbs7]:
        key = (wbs6.id, code)
        node = self.wbs7_cache.get(key)
        if not node:
            stmt = select(Wbs7).where(
                Wbs7.commessa_id == self.commessa_id,
                Wbs7.wbs6_id == wbs6.id,
            )
            if code:
                stmt = stmt.where(Wbs7.code == code)
            node = self.session.exec(stmt).first()
        if not node and code:
            label = f"{code} - {description}" if description else code
            node = Wbs7(
                commessa_id=self.commessa_id,
                wbs6_id=wbs6.id,
                code=code,
                description=label,
            )
            self.session.add(node)
            self.session.flush()
        if node:
            self.wbs7_cache[key] = node
        return node
