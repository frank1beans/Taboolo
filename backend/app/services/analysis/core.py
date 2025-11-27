from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from statistics import fmean, pstdev
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Any

from sqlmodel import Session, select

from app.db.models import (
    Commessa,
    Computo,
    ComputoTipo,
    PriceListOffer,
    Settings,
    VoceComputo,
)
from app.db.models_wbs import Voce as VoceNorm
from app.schemas import (
    AnalisiDistribuzioneItemSchema,
    AnalisiVoceCriticaSchema,
)
from app.services.wbs_visibility import WbsVisibilityService
from app.services.analysis.cache import AnalysisCacheService


def _safe_float(value: Any) -> float | None:
    """Converte numeri o stringhe numeriche (anche con virgola) in float, altrimenti None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip().replace("\u00a0", "")
        text = text.replace(",", ".")
        text = "".join(ch for ch in text if ch not in (" ", "\t"))
        return float(text)
    except Exception:  # noqa: BLE001
        return None


class CoreAnalysisService:
    WBS6_UNCLASSIFIED_LABEL = "Non Classificata WBS6"
    DEFAULT_THRESHOLD_MEDIA = 25.0
    DEFAULT_THRESHOLD_ALTA = 50.0

    @staticmethod
    def load_thresholds(session: Session) -> dict[str, float]:
        settings = session.exec(select(Settings).limit(1)).first()
        media = (
            float(settings.criticita_media_percent)
            if settings and settings.criticita_media_percent is not None
            else CoreAnalysisService.DEFAULT_THRESHOLD_MEDIA
        )
        alta = (
            float(settings.criticita_alta_percent)
            if settings and settings.criticita_alta_percent is not None
            else CoreAnalysisService.DEFAULT_THRESHOLD_ALTA
        )
        media = max(0.0, media)
        alta = max(media, alta)
        return {"media": media, "alta": alta}

    @staticmethod
    def classify_delta(delta: float | None, thresholds: dict[str, float]) -> Optional[str]:
        if delta is None:
            return None
        value = abs(delta)
        if value >= thresholds["alta"]:
            return "alta"
        if value >= thresholds["media"]:
            return "media"
        return "bassa"

    @staticmethod
    def prepare_commessa_data(session: Session, commessa_id: int) -> dict:
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

        cache_version = AnalysisCacheService.compute_dataset_version(session, commessa_id)
        cached = AnalysisCacheService.try_get(commessa_id, cache_version)
        if cached is not None:
            return cached

        hidden_codes_by_level = WbsVisibilityService.hidden_codes_by_level(session, commessa_id)

        computi = (
            session.exec(
                select(Computo)
                .where(Computo.commessa_id == commessa_id)
                .order_by(Computo.created_at)
            )
            .all()
        )

        if not computi:
            data = {
                "commessa": commessa,
                "computi": [],
                "progetto": None,
                "ritorni": [],
                "entries": [],
                "imprese": [],
                "label_by_id": {},
                "voci_by_computo": {},
            }
            AnalysisCacheService.store(commessa_id, cache_version, data)
            return data

        progetto = next(
            (c for c in sorted(computi, key=lambda c: c.created_at, reverse=True) if c.tipo == ComputoTipo.progetto),
            None,
        )
        ritorni = [c for c in computi if c.tipo == ComputoTipo.ritorno]

        computo_ids = [c.id for c in computi]
        voci_by_computo: Dict[int, List[SimpleNamespace]] = {cid: [] for cid in computo_ids}
        voci_rows = CoreAnalysisService._load_voci_dataframe(session, computo_ids)
        for voce in voci_rows:
            voci_by_computo[voce.computo_id].append(voce)

        legacy_to_normalized: Dict[int, VoceNorm] = {}
        if computo_ids:
            normalized_rows = session.exec(
                select(VoceNorm).where(VoceNorm.commessa_id == commessa_id)
            ).all()
            for voce_norm in normalized_rows:
                if voce_norm.legacy_vocecomputo_id:
                    legacy_to_normalized[voce_norm.legacy_vocecomputo_id] = voce_norm

        offers_by_key: Dict[tuple[int, int], PriceListOffer] = {}
        if computo_ids:
            offers_rows = session.exec(
                select(PriceListOffer).where(PriceListOffer.computo_id.in_(computo_ids))
            ).all()
            for offer in offers_rows:
                offers_by_key[(offer.computo_id, offer.price_list_item_id)] = offer

        entries: List[dict] = []
        index_map: Dict[str, List[int]] = defaultdict(list)

        def _voce_is_hidden(voce: VoceComputo, wbs_info: dict) -> bool:
            if not hidden_codes_by_level:
                return False
            for level, codes in hidden_codes_by_level.items():
                if not codes:
                    continue
                if level == 7:
                    code = wbs_info.get("wbs7_code") or voce.codice
                elif level == 6:
                    code = wbs_info.get("wbs6_code")
                elif level == 5:
                    code = wbs_info.get("wbs5_code")
                else:
                    code = getattr(voce, f"wbs_{level}_code", None)
                if code and code in codes:
                    return True
            return False

        def _apply_price_list_offer(
            offer: PriceListOffer | None,
            quantity: float | None,
            price: float | None,
            amount: float | None,
        ) -> tuple[float | None, float | None, float | None]:
            if not offer:
                return quantity, price, amount
            resolved_quantity = _safe_float(quantity)
            if resolved_quantity is None:
                resolved_quantity = _safe_float(offer.quantita)
            resolved_price = offer.prezzo_unitario
            if resolved_quantity is not None:
                resolved_amount = round(resolved_price * resolved_quantity, 2)
            elif offer.quantita is not None:
                resolved_amount = round(resolved_price * offer.quantita, 2)
            else:
                resolved_amount = amount
            return resolved_quantity, resolved_price, resolved_amount

        if progetto:
            for voce in voci_by_computo.get(progetto.id, []):
                wbs_info = CoreAnalysisService._extract_wbs_info(voce)
                if _voce_is_hidden(voce, wbs_info):
                    continue
                code = CoreAnalysisService._resolve_primary_code(voce, wbs_info)
                raw_descrizione = CoreAnalysisService._resolve_primary_description(voce, wbs_info)
                descrizione = CoreAnalysisService._canonical_description(raw_descrizione)
                voce_norm = legacy_to_normalized.get(voce.id)
                price_item_id = voce_norm.price_list_item_id if voce_norm else None
                project_offer = (
                    offers_by_key.get((progetto.id, price_item_id))
                    if price_item_id is not None
                    else None
                )
                quantita_val, prezzo_val, importo_val = _apply_price_list_offer(
                    project_offer,
                    voce.quantita,
                    voce.prezzo_unitario,
                    voce.importo,
                )
                entry = {
                    "voce_id": voce.id,
                    "computo_id": voce.computo_id,
                    "is_project": True,
                    "source": "progetto",
                    "aggregation_key": CoreAnalysisService._aggregation_key(voce, code),
                    "codice": code,
                    "descrizione": descrizione or raw_descrizione,
                    "descrizione_originale": raw_descrizione,
                    "unita_misura": voce.unita_misura,
                    "quantita": quantita_val,
                    "quantita_progetto": quantita_val,
                    "prezzo_unitario_progetto": prezzo_val,
                    "importo_totale_progetto": importo_val,
                    "offerte": {},
                    "categoria": CoreAnalysisService._resolve_categoria(voce),
                    "progressivo": voce.progressivo,
                    "ordine": voce.ordine,
                    "wbs6_code": wbs_info["wbs6_code"],
                    "wbs6_description": wbs_info["wbs6_description"],
                    "wbs7_code": wbs_info["wbs7_code"],
                    "wbs7_description": wbs_info["wbs7_description"],
                }
                entries.append(entry)
                idx = len(entries) - 1
                for key in CoreAnalysisService._voce_keys(voce, code, wbs_info):
                    index_map[key].append(idx)

        imprese: List[dict] = []
        label_by_id: Dict[int, str] = {}
        used_names: set[str] = set()
        for counter, ritorno in enumerate(ritorni, start=1):
            base_name = CoreAnalysisService._label_ritorno(ritorno, fallback_index=counter)
            nome = CoreAnalysisService._ensure_unique_name(base_name, used_names)
            used_names.add(nome)
            imprese.append(
                {
                    "id": ritorno.id,
                    "nome": nome,
                    "impresa": ritorno.impresa,
                    "round_number": ritorno.round_number,
                }
            )
            label_by_id[ritorno.id] = nome

            for voce in voci_by_computo.get(ritorno.id, []):
                wbs_info = CoreAnalysisService._extract_wbs_info(voce)
                if _voce_is_hidden(voce, wbs_info):
                    continue
                code = CoreAnalysisService._resolve_primary_code(voce, wbs_info)
                raw_descrizione = CoreAnalysisService._resolve_primary_description(voce, wbs_info)
                descrizione = CoreAnalysisService._canonical_description(raw_descrizione)
                voce_norm = legacy_to_normalized.get(voce.id)
                price_item_id = voce_norm.price_list_item_id if voce_norm else None
                entry_idx = CoreAnalysisService._find_entry(index_map, voce, code, wbs_info)
                if entry_idx is None:
                    entry = {
                        "voce_id": voce.id,
                        "computo_id": voce.computo_id,
                        "is_project": False,
                        "source": "ritorno",
                        "aggregation_key": CoreAnalysisService._aggregation_key(voce, code),
                        "codice": code,
                        "descrizione": descrizione or raw_descrizione,
                        "descrizione_originale": raw_descrizione,
                        "unita_misura": voce.unita_misura,
                        "quantita": None,
                        "quantita_progetto": None,
                        "prezzo_unitario_progetto": None,
                        "importo_totale_progetto": None,
                        "offerte": {},
                        "categoria": CoreAnalysisService._resolve_categoria(voce),
                        "progressivo": voce.progressivo,
                        "ordine": voce.ordine,
                        "wbs6_code": wbs_info["wbs6_code"],
                        "wbs6_description": wbs_info["wbs6_description"],
                        "wbs7_code": wbs_info["wbs7_code"],
                        "wbs7_description": wbs_info["wbs7_description"],
                    }
                    entries.append(entry)
                    entry_idx = len(entries) - 1
                    for key in CoreAnalysisService._voce_keys(voce, code, wbs_info):
                        index_map[key].append(entry_idx)

                offerte = entries[entry_idx]["offerte"]
                offer = (
                    offers_by_key.get((ritorno.id, price_item_id))
                    if price_item_id is not None
                    else None
                )
                quantita_off = _safe_float(voce.quantita) or 0.0
                prezzo_off = offer.prezzo_unitario if offer else voce.prezzo_unitario
                if prezzo_off is not None:
                    importo_off = round(prezzo_off * quantita_off, 2)
                else:
                    importo_off = voce.importo
                offerte[nome] = {
                    "quantita": quantita_off,
                    "prezzo_unitario": prezzo_off,
                    "importo_totale": importo_off,
                    "note": voce.note,
                }

        entries = CoreAnalysisService._merge_entries(entries)

        result = {
            "commessa": commessa,
            "computi": computi,
            "progetto": progetto,
            "ritorni": ritorni,
            "entries": entries,
            "imprese": imprese,
            "label_by_id": label_by_id,
            "voci_by_computo": voci_by_computo,
        }
        AnalysisCacheService.store(commessa_id, cache_version, result)
        return result

    @staticmethod
    def build_distribuzione(entries: Iterable[dict]) -> List[AnalisiDistribuzioneItemSchema]:
        counts = {"sotto": 0, "in_linea": 0, "sopra": 0}
        for entry in entries:
            offerte = entry.get("offerte") or {}
            if not offerte:
                continue

            progetto = float(entry.get("importo_totale_progetto") or 0.0)
            if abs(progetto) <= 1e-9:
                continue

            valori_ritorni = [
                float(data.get("importo_totale") or 0.0)
                for data in offerte.values()
                if data is not None
            ]
            if not valori_ritorni:
                continue

            media = sum(valori_ritorni) / len(valori_ritorni)
            delta = ((media - progetto) / progetto) * 100

            if delta <= -10:
                counts["sotto"] += 1
            elif delta >= 10:
                counts["sopra"] += 1
            else:
                counts["in_linea"] += 1

        mapping = [
            ("sotto", "Sotto media (<= -10%)", "#10b981"),
            ("in_linea", "Vicino alla media (-10% a +10%)", "#6b7280"),
            ("sopra", "Sopra media (>= +10%)", "#ef4444"),
        ]

        return [
            AnalisiDistribuzioneItemSchema(nome=label, valore=counts[key], colore=color)
            for key, label, color in mapping
        ]

    @staticmethod
    def build_voci_critiche(
        entries: Iterable[dict],
        thresholds: dict[str, float],
    ) -> List[AnalisiVoceCriticaSchema]:
        risultati: List[AnalisiVoceCriticaSchema] = []
        for entry in entries:
            offerte = entry["offerte"]
            if not offerte:
                continue

            progetto = float(entry.get("importo_totale_progetto") or 0.0)
            importi_details = [
                (nome, float(data.get("importo_totale") or 0.0))
                for nome, data in offerte.items()
                if data.get("importo_totale") is not None
            ]
            if not importi_details:
                continue
            prezzi = [
                float(data.get("prezzo_unitario"))
                for data in offerte.values()
                if data.get("prezzo_unitario") is not None
            ]
            media_importo = fmean(value for _, value in importi_details)
            media_prezzo = fmean(prezzi) if prezzi else None

            delta = None
            prezzo_progetto = entry.get("prezzo_unitario_progetto")
            if (
                media_prezzo is not None
                and prezzo_progetto is not None
                and float(prezzo_progetto) != 0
            ):
                delta = (
                    (media_prezzo - float(prezzo_progetto)) / float(prezzo_progetto) * 100
                )

            delta_assoluto = media_importo - progetto
            criticita = CoreAnalysisService.classify_delta(delta, thresholds) or "bassa"
            direzione = "neutro"
            if delta is not None:
                if delta > 0:
                    direzione = "positivo"
                elif delta < 0:
                    direzione = "negativo"

            imprese_map = {
                nome: round(float(dati.get("importo_totale") or 0.0), 2)
                for nome, dati in offerte.items()
            }

            impresa_min = None
            impresa_max = None
            min_offerta = None
            max_offerta = None
            if importi_details:
                impresa_min, min_offerta = min(importi_details, key=lambda item: item[1])
                impresa_max, max_offerta = max(importi_details, key=lambda item: item[1])

            deviazione_standard = pstdev([value for _, value in importi_details]) if len(importi_details) >= 2 else None

            risultati.append(
                AnalisiVoceCriticaSchema(
                    codice=entry["codice"],
                    descrizione=entry["descrizione"],
                    descrizione_estesa=entry.get("descrizione_originale") or entry.get("descrizione"),
                    progetto=round(progetto, 2),
                    imprese=imprese_map,
                    delta=round(delta or 0.0, 1),
                    criticita=criticita,
                    delta_assoluto=round(delta_assoluto, 2),
                    media_prezzo_unitario=round(media_prezzo, 2) if media_prezzo is not None else None,
                    media_importo_totale=round(media_importo, 2),
                    min_offerta=round(min_offerta, 2) if min_offerta is not None else None,
                    max_offerta=round(max_offerta, 2) if max_offerta is not None else None,
                    impresa_min=impresa_min,
                    impresa_max=impresa_max,
                    deviazione_standard=round(deviazione_standard, 2) if deviazione_standard is not None else None,
                    direzione=direzione,
                )
            )

        risultati.sort(key=lambda item: abs(item.delta), reverse=True)
        return risultati

    @staticmethod
    def _load_voci_dataframe(session: Session, computo_ids: list[int]) -> list[SimpleNamespace]:
        if not computo_ids:
            return []

        engine = session.get_bind()
        query = (
            select(
                VoceComputo.id,
                VoceComputo.computo_id,
                VoceComputo.progressivo,
                VoceComputo.codice,
                VoceComputo.descrizione,
                VoceComputo.unita_misura,
                VoceComputo.quantita,
                VoceComputo.prezzo_unitario,
                VoceComputo.importo,
                VoceComputo.note,
                VoceComputo.ordine,
                VoceComputo.wbs_1_code,
                VoceComputo.wbs_1_description,
                VoceComputo.wbs_2_code,
                VoceComputo.wbs_2_description,
                VoceComputo.wbs_3_code,
                VoceComputo.wbs_3_description,
                VoceComputo.wbs_4_code,
                VoceComputo.wbs_4_description,
                VoceComputo.wbs_5_code,
                VoceComputo.wbs_5_description,
                VoceComputo.wbs_6_code,
                VoceComputo.wbs_6_description,
                VoceComputo.wbs_7_code,
                VoceComputo.wbs_7_description,
            )
            .where(VoceComputo.computo_id.in_(computo_ids))
            .order_by(VoceComputo.computo_id, VoceComputo.ordine)
        )

        with engine.connect() as connection:
            rows = connection.execute(query).all()

        namespaces: list[SimpleNamespace] = []
        for row in rows:
            if hasattr(row, "_mapping"):
                data = dict(row._mapping)
            else:
                data = dict(row)
            namespaces.append(SimpleNamespace(**data))
        return namespaces

    @staticmethod
    def build_wbs6_analisi(
        entries: Iterable[dict],
        *,
        totale_imprese: int,
        thresholds: dict[str, float],
    ) -> List[dict]:
        """Aggrega le voci per WBS6 calcolando importi progetto e media offerte."""

        wbs6_groups: Dict[tuple, dict] = {}
        for entry in entries:
            key, info = CoreAnalysisService._wbs6_identity(entry)
            bucket = wbs6_groups.setdefault(
                key,
                {
                    "wbs6_id": info["wbs6_id"],
                    "wbs6_label": info["wbs6_label"],
                    "wbs6_code": info.get("wbs6_code"),
                    "wbs6_description": info.get("wbs6_description"),
                    "progetto": 0.0,
                    "ritorni": defaultdict(float),
                    "voci": [],
                    "conteggi_criticita": {"alta": 0, "media": 0, "bassa": 0},
                },
            )

            progetto = float(entry.get("importo_totale_progetto") or 0.0)
            bucket["progetto"] += progetto

            voce_info = CoreAnalysisService._build_wbs6_voce(entry, thresholds)
            bucket["voci"].append(voce_info)
            criticita = voce_info.get("criticita")
            if criticita in ("alta", "media", "bassa"):
                bucket["conteggi_criticita"][criticita] += 1

            offerte = entry.get("offerte") or {}
            for nome, dati in offerte.items():
                bucket["ritorni"][nome] += float(dati.get("importo_totale") or 0.0)

        risultati: List[dict] = []
        for bucket in wbs6_groups.values():
            ritorni_valori = list(bucket["ritorni"].values())
            # Calcola la media su TUTTE le offerte totali, includendo quelle che non hanno voci (= 0)
            totale_ritorni = sum(ritorni_valori)
            media = totale_ritorni / totale_imprese if totale_imprese > 0 else 0.0
            progetto = bucket["progetto"]
            if progetto and abs(progetto) > 1e-9:
                delta = ((media - progetto) / progetto) * 100
            else:
                delta = 0.0

            risultati.append(
                {
                    "wbs6_id": bucket["wbs6_id"],
                    "wbs6_label": bucket["wbs6_label"],
                    "wbs6_code": bucket.get("wbs6_code"),
                    "wbs6_description": bucket.get("wbs6_description"),
                    "progetto": round(progetto, 2),
                    "media_ritorni": round(media, 2),
                    "delta_percentuale": round(delta, 1),
                    "delta_assoluto": round(media - progetto, 2),
                    "conteggi_criticita": bucket["conteggi_criticita"],
                    "offerte_considerate": len(bucket["ritorni"]),
                    "offerte_totali": totale_imprese,
                    "voci": sorted(
                        bucket["voci"],
                        key=lambda voce: (
                            voce.get("descrizione") or "",
                            voce.get("codice") or "",
                        ),
                    ),
                }
            )

        risultati.sort(key=lambda item: item["progetto"], reverse=True)
        return risultati

    @staticmethod
    def _wbs6_identity(entry: dict) -> tuple[tuple, dict]:
        """Restituisce l'identità (codice/descrizione) di aggregazione basata sulla WBS6."""

        w6_code = (entry.get("wbs6_code") or "").strip() or None
        raw_w6_desc = (entry.get("wbs6_description") or "").strip() or None

        def _sanitize_description(text: str | None) -> str | None:
            if not text:
                return None
            cleaned = text
            if w6_code:
                pattern = re.compile(rf"^(?:{re.escape(w6_code)}\s*[-–:])\s*", re.IGNORECASE)
                cleaned = pattern.sub("", cleaned)
            cleaned = cleaned.strip()
            return cleaned or None

        w6_desc = _sanitize_description(raw_w6_desc)

        code = w6_code
        description = w6_desc or (w6_code or CoreAnalysisService.WBS6_UNCLASSIFIED_LABEL)

        label_parts = [part for part in (code, description) if part]
        label = " - ".join(label_parts) if label_parts else CoreAnalysisService.WBS6_UNCLASSIFIED_LABEL
        slug_source = "::".join(part for part in (code, description) if part)
        slug = CoreAnalysisService._normalize_text(slug_source or label or CoreAnalysisService.WBS6_UNCLASSIFIED_LABEL)
        identifier = (
            code or CoreAnalysisService.WBS6_UNCLASSIFIED_LABEL,
            description or CoreAnalysisService.WBS6_UNCLASSIFIED_LABEL,
        )
        return identifier, {
            "wbs6_id": slug or "wbs6-unclassified",
            "wbs6_label": label,
            "wbs6_code": code,
            "wbs6_description": description,
        }

    @staticmethod
    def _build_wbs6_voce(entry: dict, thresholds: dict[str, float]) -> dict:
        offerte = entry.get("offerte") or {}
        prezzi = [
            float(offerta.get("prezzo_unitario"))
            for offerta in offerte.values()
            if offerta.get("prezzo_unitario") is not None
        ]
        importi = [
            float(offerta.get("importo_totale"))
            for offerta in offerte.values()
            if offerta.get("importo_totale") is not None
        ]
        importi_details = [
            (nome, float(dati.get("importo_totale")))
            for nome, dati in offerte.items()
            if dati.get("importo_totale") is not None
        ]

        media_prezzo = fmean(prezzi) if prezzi else None
        media_importo = fmean(importi) if importi else None

        prezzo_progetto = entry.get("prezzo_unitario_progetto")
        if prezzo_progetto is not None:
            prezzo_progetto = float(prezzo_progetto)
        importo_progetto = entry.get("importo_totale_progetto")
        if importo_progetto is not None:
            importo_progetto = float(importo_progetto)

        delta = None
        if (
            media_prezzo is not None
            and prezzo_progetto is not None
            and abs(prezzo_progetto) > 1e-9
        ):
            delta = ((media_prezzo - prezzo_progetto) / prezzo_progetto) * 100

        delta_assoluto = None
        if media_importo is not None and importo_progetto is not None:
            delta_assoluto = media_importo - importo_progetto

        criticita = CoreAnalysisService.classify_delta(delta, thresholds)
        direzione = "neutro"
        if delta is not None:
            if delta > 0:
                direzione = "positivo"
            elif delta < 0:
                direzione = "negativo"

        importo_minimo = None
        importo_massimo = None
        impresa_min = None
        impresa_max = None
        if importi_details:
            impresa_min, importo_minimo = min(importi_details, key=lambda item: item[1])
            impresa_max, importo_massimo = max(importi_details, key=lambda item: item[1])

        deviazione_standard = pstdev(importi) if len(importi) >= 2 else None

        return {
            "codice": entry.get("codice"),
            "descrizione": entry.get("descrizione"),
            "descrizione_estesa": entry.get("descrizione_originale") or entry.get("descrizione"),
            "unita_misura": entry.get("unita_misura"),
            "quantita": entry.get("quantita"),
            "prezzo_unitario_progetto": prezzo_progetto,
            "importo_totale_progetto": entry.get("importo_totale_progetto"),
            "media_prezzo_unitario": round(media_prezzo, 2) if media_prezzo is not None else None,
            "media_importo_totale": round(media_importo, 2) if media_importo is not None else None,
            "delta_percentuale": round(delta, 1) if delta is not None else None,
            "delta_assoluto": round(delta_assoluto, 2) if delta_assoluto is not None else None,
            "offerte_considerate": len(prezzi),
            "importo_minimo": round(importo_minimo, 2) if importo_minimo is not None else None,
            "importo_massimo": round(importo_massimo, 2) if importo_massimo is not None else None,
            "impresa_min": impresa_min,
            "impresa_max": impresa_max,
            "deviazione_standard": round(deviazione_standard, 2) if deviazione_standard is not None else None,
            "criticita": criticita,
            "direzione": direzione,
        }

    @staticmethod
    def _find_entry(
        index_map: Dict[str, List[int]],
        voce: VoceComputo,
        code: Optional[str],
        wbs_info: dict,
    ) -> Optional[int]:
        for key in CoreAnalysisService._voce_keys(voce, code, wbs_info):
            indices = index_map.get(key)
            if indices:
                return indices[0]
        return None

    @staticmethod
    def _voce_keys(voce: VoceComputo, code: Optional[str], wbs_info: dict) -> List[str]:
        keys: List[str] = []
        w5_desc = wbs_info.get("wbs5_description")
        w6_code = wbs_info.get("wbs6_code")
        w6_desc = wbs_info.get("wbs6_description")
        w7_code = wbs_info.get("wbs7_code")
        w7_desc = wbs_info.get("wbs7_description")

        if voce.progressivo is not None:
            keys.append(f"progressivo::{int(voce.progressivo)}")
        if voce.ordine is not None:
            keys.append(f"ordine::{voce.ordine}")

        if code:
            keys.append(f"code::{code.lower()}")
        elif voce.codice:
            keys.append(f"code::{voce.codice.lower()}")

        for label in (w7_code, w6_code):
            if label:
                keys.append(f"wbs_code::{label.lower()}")

        for label in (w7_desc, w6_desc, w5_desc):
            if label:
                keys.append(f"desc::{CoreAnalysisService._normalize_text(label)}")

        canonical = CoreAnalysisService._canonical_description(voce.descrizione)
        if canonical:
            keys.append(f"desc::{CoreAnalysisService._normalize_text(canonical)}")

        return keys

    @staticmethod
    def _aggregation_key(voce: VoceComputo, code: Optional[str] = None) -> str:
        candidates = (
            code,
            voce.codice,
            voce.descrizione,
            getattr(voce, "wbs_7_code", None),
            getattr(voce, "wbs_6_code", None),
            getattr(voce, "wbs_5_code", None),
        )
        for candidate in candidates:
            if candidate:
                text = str(candidate).strip()
                if text:
                    return text
        if voce.id is not None:
            return f"voce-{voce.id}"
        if voce.progressivo is not None:
            return f"progressivo-{int(voce.progressivo)}"
        if voce.ordine is not None:
            return f"ordine-{voce.ordine}"
        return "aggregated-entry"

    @staticmethod
    def _resolve_code(voce: VoceComputo) -> Optional[str]:
        if voce.codice:
            return voce.codice
        if voce.progressivo is not None:
            return f"PROG-{int(voce.progressivo):05d}"
        if voce.descrizione:
            slug = CoreAnalysisService._normalize_text(voce.descrizione)
            if slug:
                return f"DESC-{slug[:12]}"
        return f"ORD-{voce.ordine:05d}"

    @staticmethod
    def _resolve_categoria(voce: VoceComputo) -> str:
        return (
            voce.wbs_6_description
            or voce.wbs_6_code
            or voce.wbs_5_description
            or voce.wbs_5_code
            or voce.wbs_2_description
            or voce.wbs_2_code
            or "Generale"
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(ch.lower() for ch in normalized if ch.isalnum())

    @staticmethod
    def _canonical_description(value: str | None) -> str | None:
        if not value:
            return None
        sanitized = value.replace("\r", "\n")
        parts = [part.strip() for part in sanitized.split("\n\n") if part.strip()]
        if not parts:
            return value.strip()

        filler_prefixes = (
            "compresi nel prezzo",
            "nel prezzo",
            "sono compresi",
            "si intendono compresi",
        )
        action_keywords = (
            "fornitura",
            "posa",
            "realizzazione",
            "smontaggio",
            "installazione",
            "demolizione",
        )

        def score(part: str, index: int) -> int:
            lowered = part.lower()
            value_len = len(part)
            if any(lowered.startswith(prefix) for prefix in filler_prefixes):
                value_len -= 200
            if any(keyword in lowered for keyword in action_keywords):
                value_len += 50
            if index == 0:
                value_len += 25
            return value_len

        best_idx = max(range(len(parts)), key=lambda idx: score(parts[idx], idx))
        candidate = parts[best_idx]
        if candidate:
            return candidate

        lines = [line.strip() for line in sanitized.split("\n") if line.strip()]
        return max(lines, key=len) if lines else value.strip()

    @staticmethod
    def _merge_entries(entries: list[dict]) -> list[dict]:
        bucket: dict[str, dict] = {}

        for entry in entries:
            key = str(entry.get("aggregation_key") or "").strip()

            if not key:
                progressivo = entry.get("progressivo")
                ordine = entry.get("ordine")
                voce_id = entry.get("voce_id")
                computo_id = entry.get("computo_id")

                key_candidates: list[str] = []

                def push(value) -> None:
                    if value is None:
                        return
                    text = str(value).strip()
                    if text:
                        key_candidates.append(text)

                push(voce_id)
                if computo_id is not None and progressivo is not None:
                    push(f"{computo_id}-{int(progressivo)}")
                if computo_id is not None and ordine is not None:
                    push(f"{computo_id}-{ordine}")
                push(entry.get("codice"))
                push(entry.get("wbs7_code"))
                push(entry.get("wbs6_code"))
                push(entry.get("wbs5_code"))
                push(entry.get("descrizione"))
                push(entry.get("wbs7_description"))
                push(entry.get("wbs6_description"))
                push(entry.get("wbs5_description"))
                push(entry.get("categoria"))

                for candidate in key_candidates:
                    normalized = CoreAnalysisService._normalize_text(candidate)
                    key = normalized or candidate
                    if key:
                        break

            if not key:
                key = f"entry::{len(bucket)}"

            existing = bucket.get(key)
            if existing is None:
                existing = {
                    **entry,
                    "quantita": _safe_float(entry.get("quantita")) or 0.0,
                    "importo_totale_progetto": _safe_float(entry.get("importo_totale_progetto")) or 0.0,
                    "offerte": {},
                }
                existing["prezzo_unitario_progetto"] = entry.get("prezzo_unitario_progetto")
                existing["aggregation_key"] = key
                bucket[key] = existing
            else:
                existing["quantita"] += _safe_float(entry.get("quantita")) or 0.0
                existing["importo_totale_progetto"] += _safe_float(entry.get("importo_totale_progetto")) or 0.0
                if not existing.get("unita_misura") and entry.get("unita_misura"):
                    existing["unita_misura"] = entry.get("unita_misura")
                for field in (
                    "wbs5_code",
                    "wbs5_description",
                    "wbs6_code",
                    "wbs6_description",
                    "wbs7_code",
                    "wbs7_description",
                    "codice",
                    "descrizione",
                    "descrizione_originale",
                ):
                    if not existing.get(field) and entry.get(field):
                        existing[field] = entry.get(field)

            for impresa, offerta in entry.get("offerte", {}).items():
                target = existing["offerte"].setdefault(
                    impresa,
                    {
                        "quantita": 0.0,
                        "prezzo_unitario": offerta.get("prezzo_unitario") or 0.0,
                        "importo_totale": 0.0,
                        "note": offerta.get("note"),
                        "criticita": offerta.get("criticita"),
                    },
                )
                target["quantita"] += _safe_float(offerta.get("quantita")) or 0.0
                target["importo_totale"] += _safe_float(offerta.get("importo_totale")) or 0.0
                if offerta.get("note"):
                    target["note"] = offerta.get("note")
                if offerta.get("criticita"):
                    target["criticita"] = offerta.get("criticita")

        for entry in bucket.values():
            qty = _safe_float(entry.get("quantita")) or 0.0
            if qty and abs(qty) > 1e-9:
                entry["prezzo_unitario_progetto"] = round(entry["importo_totale_progetto"] / qty, 4)
            else:
                entry["prezzo_unitario_progetto"] = entry.get("prezzo_unitario_progetto")

            project_qty_rounded = round(qty, 2)
            for offerta in entry["offerte"].values():
                qty_off = _safe_float(offerta.get("quantita")) or 0.0
                if qty_off and abs(qty_off) > 1e-9:
                    offerta["prezzo_unitario"] = round(offerta["importo_totale"] / qty_off, 4)
                else:
                    offerta["prezzo_unitario"] = offerta.get("prezzo_unitario") or 0.0
                offerta["delta_quantita"] = round(qty_off - project_qty_rounded, 2)

        merged = list(bucket.values())
        merged.sort(key=lambda item: (item.get("descrizione") or "", item.get("codice") or ""))
        return merged

    @staticmethod
    def _ensure_unique_name(base: str, used: set[str]) -> str:
        if base not in used:
            return base
        counter = 2
        while f"{base} ({counter})" in used:
            counter += 1
        return f"{base} ({counter})"

    @staticmethod
    def _label_ritorno(ritorno: Computo, fallback_index: int | None = None) -> str:
        if ritorno.impresa:
            return ritorno.impresa
        if ritorno.nome:
            return ritorno.nome
        if fallback_index is not None:
            return f"Ritorno {fallback_index}"
        return f"Ritorno {ritorno.id}"

    @staticmethod
    def _normalize_impresa_label(value: str | None) -> str | None:
        if not value:
            return None
        text = value.strip()
        if not text:
            return None
        text = text.replace("Round", "").strip()
        text = re.sub(r"\(\d+\)$", "", text).strip()
        return text or None

    @staticmethod
    def normalize_imprese(imprese: Iterable[dict]) -> List[dict]:
        normalizzati: List[dict] = []
        for info in imprese:
            nome = info.get("nome")  # Original base name used as offerte key
            originale = info.get("impresa")
            etichetta = CoreAnalysisService._normalize_impresa_label(originale or nome)
            round_number = info.get("round_number")
            round_label = f"Round {round_number}" if round_number is not None else None
            composite_label = f"{etichetta} ({round_label})" if round_label else etichetta
            normalized_key = f"{etichetta}|r{round_number}" if round_number is not None else etichetta
            normalizzati.append(
                {
                    "computo_id": info.get("id") or info.get("computo_id"),
                    "nome": composite_label or nome,
                    "nome_originale": nome,  # Original name used as offerte key for filtering
                    "impresa": originale,
                    "etichetta": composite_label or etichetta or nome,
                    "base_label": etichetta or nome,  # Nome base senza round per il raggruppamento
                    "impresa_normalizzata": normalized_key,
                    "round_number": round_number,
                    "round_label": round_label,
                }
            )

        normalizzati.sort(
            key=lambda item: (
                item.get("round_number") or 0,
                item.get("nome") or "",
            )
        )
        return normalizzati

    @staticmethod
    def build_rounds(imprese: Iterable[dict]) -> List[dict]:
        mapping: Dict[int, dict] = {}
        for info in imprese:
            numero = info.get("round_number")
            if numero is None:
                continue
            bucket = mapping.setdefault(
                numero,
                {
                    "numero": numero,
                    "label": info.get("round_label") or f"Round {numero}",
                    "imprese": [],
                },
            )
            bucket["imprese"].append(info["nome"])

        risultati = []
        for numero, bucket in mapping.items():
            risultati.append(
                {
                    "numero": numero,
                    "label": bucket["label"],
                    "imprese": bucket["imprese"],
                    "imprese_count": len(bucket["imprese"]),
                }
            )

        risultati.sort(key=lambda item: item["numero"])
        return risultati

    @staticmethod
    def determine_allowed_offerte(
        imprese: Iterable[dict],
        *,
        round_number: int | None,
        impresa: str | None,
    ) -> tuple[set[int] | None, set[str] | None, str | None]:
        normalized_impresa = CoreAnalysisService._normalize_impresa_label(impresa)
        ids: set[int] = set()
        labels: set[str] = set()

        for info in imprese:
            nome = info["nome"]
            # Use nome_originale for filtering as it matches offerte keys
            nome_originale = info.get("nome_originale") or nome
            round_ok = (
                round_number is None or info.get("round_number") == round_number
            )
            base_label = info.get("etichetta") or CoreAnalysisService._normalize_impresa_label(
                info.get("impresa") or nome
            )
            impresa_ok = (
                normalized_impresa is None
                or (base_label and base_label.lower() == normalized_impresa.lower())
            )
            if round_ok and impresa_ok:
                ids.add(info["computo_id"])
                labels.add(nome_originale)

        if round_number is None and normalized_impresa is None:
            return None, None, None

        if not ids:
            return set(), set(), normalized_impresa

        return ids, labels, normalized_impresa

    @staticmethod
    def filter_entries(entries: Iterable[dict], allowed: set[str] | None) -> list[dict]:
        if allowed is None:
            return list(entries)
        filtered: list[dict] = []
        for entry in entries:
            offerte = entry.get("offerte") or {}
            filtered_offerte = (
                {key: value for key, value in offerte.items() if key in allowed}
                if offerte
                else {}
            )
            new_entry = dict(entry)
            new_entry["offerte"] = filtered_offerte
            filtered.append(new_entry)
        return filtered

    @staticmethod
    def _extract_wbs_info(voce: VoceComputo) -> dict:
        return {
            "wbs1_code": getattr(voce, "wbs_1_code", None),
            "wbs1_description": getattr(voce, "wbs_1_description", None),
            "wbs2_code": getattr(voce, "wbs_2_code", None),
            "wbs2_description": getattr(voce, "wbs_2_description", None),
            "wbs3_code": getattr(voce, "wbs_3_code", None),
            "wbs3_description": getattr(voce, "wbs_3_description", None),
            "wbs4_code": getattr(voce, "wbs_4_code", None),
            "wbs4_description": getattr(voce, "wbs_4_description", None),
            "wbs5_code": getattr(voce, "wbs_5_code", None),
            "wbs5_description": getattr(voce, "wbs_5_description", None),
            "wbs6_code": getattr(voce, "wbs_6_code", None),
            "wbs6_description": getattr(voce, "wbs_6_description", None),
            "wbs7_code": getattr(voce, "wbs_7_code", None),
            "wbs7_description": getattr(voce, "wbs_7_description", None),
        }

    @staticmethod
    def _resolve_primary_code(voce: VoceComputo, wbs_info: dict) -> Optional[str]:
        slug = CoreAnalysisService._normalize_text(voce.descrizione or "")
        return (
            voce.codice
            or wbs_info.get("wbs7_code")
            or wbs_info.get("wbs6_code")
            or wbs_info.get("wbs5_code")
            or (f"DESC-{slug[:16]}" if slug else None)
            or (f"ORD-{voce.ordine:05d}" if voce.ordine is not None else None)
        )

    @staticmethod
    def _resolve_primary_description(voce: VoceComputo, wbs_info: dict) -> Optional[str]:
        return (
            voce.descrizione
            or wbs_info.get("wbs7_description")
            or wbs_info.get("wbs6_description")
            or wbs_info.get("wbs5_description")
        )
