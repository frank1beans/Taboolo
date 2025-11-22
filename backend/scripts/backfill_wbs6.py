from __future__ import annotations

"""
Script di backfill per popolare lo schema WBS normalizzato a partire
dalle tabelle legacy (vocecomputo / computo).

Il processo:
1. Crea nodi WBS spaziali (1-5) per ogni commessa.
2. Genera i nodi WBS6 canonici (codice A###) e WBS7 opzionali.
3. Crea le voci normalizzate (voce) collegate alle WBS.
4. Popola i prezzi di progetto e le offerte delle imprese.
"""

import re
from collections import defaultdict
from typing import Dict, Optional, Tuple

from sqlmodel import Session, select

from app.db import engine
from app.db.models import Commessa, Computo, ComputoTipo, VoceComputo
from app.db.models_wbs import (
    Impresa,
    Voce,
    VoceOfferta,
    VoceProgetto,
    Wbs6,
    Wbs7,
    WbsSpaziale,
)

WBS6_RE = re.compile(r"^([A-Za-z]\d{3})")
WBS7_RE = re.compile(r"^([A-Za-z]\d{3})(?:[.\s_-]?(\d{3}))")


def normalize_wbs6(code: Optional[str], fallback: Optional[str]) -> Optional[str]:
    candidates = [code, fallback]
    for value in candidates:
        if not value:
            continue
        match = WBS6_RE.match(value.strip())
        if match:
            return match.group(1).upper()
    return None


def normalize_wbs7(code: Optional[str], fallback: Optional[str]) -> Optional[str]:
    candidates = [code, fallback]
    for value in candidates:
        if not value:
            continue
        match = WBS7_RE.match(value.strip())
        if match:
            prefix, suffix = match.groups()
            if suffix:
                return f"{prefix.upper()}.{suffix}"
    return None


def get_or_create_spatial_node(
    session: Session,
    cache: Dict[Tuple[int, int, str], WbsSpaziale],
    commessa_id: int,
    level: int,
    code: str,
    description: Optional[str],
    parent: Optional[WbsSpaziale],
) -> WbsSpaziale:
    key = (commessa_id, level, code)
    node = cache.get(key)
    if node:
        return node
    node = WbsSpaziale(
        commessa_id=commessa_id,
        level=level,
        code=code,
        description=description,
        parent_id=parent.id if parent else None,
    )
    session.add(node)
    session.flush()
    cache[key] = node
    return node


def get_or_create_wbs6(
    session: Session,
    cache: Dict[Tuple[int, str], Wbs6],
    commessa_id: int,
    code: str,
    description: Optional[str],
    spatial_leaf: Optional[WbsSpaziale],
) -> Wbs6:
    key = (commessa_id, code)
    node = cache.get(key)
    if node:
        return node
    desc = description or f"WBS6 {code}"
    label = f"{code} - {desc}" if desc else code
    node = Wbs6(
        commessa_id=commessa_id,
        wbs_spaziale_id=spatial_leaf.id if spatial_leaf else None,
        code=code,
        description=desc,
        label=label,
    )
    session.add(node)
    session.flush()
    cache[key] = node
    return node


def get_or_create_wbs7(
    session: Session,
    cache: Dict[Tuple[int, Optional[str]], Wbs7],
    commessa_id: int,
    wbs6_id: int,
    code: Optional[str],
    description: Optional[str],
) -> Optional[Wbs7]:
    if not code:
        return None
    key = (wbs6_id, code)
    node = cache.get(key)
    if node:
        return node
    node = Wbs7(
        commessa_id=commessa_id,
        wbs6_id=wbs6_id,
        code=code,
        description=description,
    )
    session.add(node)
    session.flush()
    cache[key] = node
    return node


def get_or_create_impresa(session: Session, cache: Dict[str, Impresa], label: Optional[str]) -> Optional[Impresa]:
    if not label:
        return None
    normalized = re.sub(r"\s+", " ", label.strip()).lower()
    if not normalized:
        return None
    node = cache.get(normalized)
    if node:
        return node
    node = Impresa(label=label.strip(), normalized_label=normalized)
    session.add(node)
    session.flush()
    cache[normalized] = node
    return node


def build_spatial_nodes(session: Session, commessa: Commessa) -> Dict[int, WbsSpaziale]:
    cache: Dict[Tuple[int, int, str], WbsSpaziale] = {}
    nodes_by_level: Dict[int, Dict[str, WbsSpaziale]] = defaultdict(dict)

    computi_ids = session.exec(select(Computo.id).where(Computo.commessa_id == commessa.id)).all()
    if not computi_ids:
        return {}

    voci = session.exec(
        select(VoceComputo).where(VoceComputo.computo_id.in_(computi_ids))
    ).all()

    for voce in voci:
        parent = None
        for level in range(1, 6):
            code = getattr(voce, f"wbs_{level}_code")
            desc = getattr(voce, f"wbs_{level}_description")
            if not code:
                break
            node = get_or_create_spatial_node(
                session,
                cache,
                commessa.id,
                level,
                code,
                desc,
                parent,
            )
            parent = node
            nodes_by_level[level][code] = node

    session.commit()
    return {node.id: node for node in (session.exec(select(WbsSpaziale).where(WbsSpaziale.commessa_id == commessa.id)).all())}


def backfill_commessa(session: Session, commessa: Commessa) -> None:
    spatial_cache: Dict[Tuple[int, int, str], WbsSpaziale] = {}
    wbs6_cache: Dict[Tuple[int, str], Wbs6] = {}
    wbs7_cache: Dict[Tuple[int, Optional[str]], Wbs7] = {}
    impresa_cache: Dict[str, Impresa] = {}
    voce_cache: Dict[Tuple[int, str, Optional[str], Optional[str]], Voce] = {}

    computi = session.exec(select(Computo).where(Computo.commessa_id == commessa.id)).all()
    if not computi:
        return

    progetto = next((c for c in computi if c.tipo == ComputoTipo.progetto), None)
    if not progetto:
        return

    voce_rows = session.exec(
        select(VoceComputo).where(VoceComputo.computo_id.in_([c.id for c in computi]))
    ).all()

    for voce_row in voce_rows:
        wbs6_code = normalize_wbs6(voce_row.wbs_6_code, voce_row.codice)
        if not wbs6_code:
            continue
        wbs6_desc = voce_row.wbs_6_description

        # crea percorso spaziale
        parent = None
        for level in range(1, 6):
            code = getattr(voce_row, f"wbs_{level}_code")
            desc = getattr(voce_row, f"wbs_{level}_description")
            if not code:
                break
            parent = get_or_create_spatial_node(
                session,
                spatial_cache,
                commessa.id,
                level,
                code,
                desc,
                parent,
            )

        wbs6 = get_or_create_wbs6(
            session,
            wbs6_cache,
            commessa.id,
            wbs6_code,
            wbs6_desc,
            parent,
        )
        wbs7_code = normalize_wbs7(voce_row.wbs_7_code, voce_row.codice)
        wbs7 = get_or_create_wbs7(
            session,
            wbs7_cache,
            commessa.id,
            wbs6.id,
            wbs7_code,
            voce_row.wbs_7_description,
        )

        voce_key = (commessa.id, wbs6.code, wbs7.code if wbs7 else None, voce_row.codice)
        voce_entry = voce_cache.get(voce_key)
        if not voce_entry:
            voce_entry = Voce(
                commessa_id=commessa.id,
                wbs6_id=wbs6.id,
                wbs7_id=wbs7.id if wbs7 else None,
                codice=voce_row.codice,
                descrizione=voce_row.descrizione,
                unita_misura=voce_row.unita_misura,
                note=voce_row.note,
                ordine=voce_row.ordine,
                legacy_vocecomputo_id=voce_row.id if voce_row.computo_id == progetto.id else None,
            )
            session.add(voce_entry)
            session.flush()
            voce_cache[voce_key] = voce_entry
        elif voce_entry.legacy_vocecomputo_id is None and voce_row.computo_id == progetto.id:
            voce_entry.legacy_vocecomputo_id = voce_row.id
            session.add(voce_entry)

        if voce_row.computo_id == progetto.id:
            session.add(
                VoceProgetto(
                    voce_id=voce_entry.id,
                    computo_id=progetto.id,
                    quantita=voce_row.quantita,
                    prezzo_unitario=voce_row.prezzo_unitario,
                    importo=voce_row.importo,
                    note=voce_row.note,
                )
            )
        else:
            computo = next((c for c in computi if c.id == voce_row.computo_id), None)
            if not computo:
                continue
            impresa = get_or_create_impresa(session, impresa_cache, computo.impresa)
            if not impresa:
                continue
            session.add(
                VoceOfferta(
                    voce_id=voce_entry.id,
                    computo_id=computo.id,
                    impresa_id=impresa.id,
                    round_number=computo.round_number,
                    quantita=voce_row.quantita,
                    prezzo_unitario=voce_row.prezzo_unitario,
                    importo=voce_row.importo,
                    note=voce_row.note,
                )
            )

    session.commit()


def main() -> None:
    with Session(engine) as session:
        commesse = session.exec(select(Commessa)).all()
        for commessa in commesse:
            backfill_commessa(session, commessa)


if __name__ == "__main__":
    main()
