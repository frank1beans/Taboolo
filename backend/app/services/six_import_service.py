from __future__ import annotations

import ast
import io
import logging
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET
from typing import Any, Optional, Sequence
from decimal import Decimal, ROUND_UP, ROUND_HALF_UP
import unicodedata

from sqlalchemy import func, select
from sqlmodel import Session

from app.db.models import Commessa, Computo, ComputoTipo, VoceComputo
from app.db.models_wbs import (
    Voce as VoceNorm,
    VoceOfferta,
    VoceProgetto,
    Wbs6,
    Wbs7,
    WbsSpaziale,
)
from app.excel import ParsedComputo, ParsedVoce, ParsedWbsLevel
from app.services.importer import ImportService
from app.services.price_catalog import price_catalog_service

logger = logging.getLogger(__name__)
MEASURE_QUANTUM = Decimal("0.01")


class PreventivoSelectionError(ValueError):
    """Richiede che l'utente scelga un preventivo specifico."""

    def __init__(self, options: list["PreventivoOption"]) -> None:
        self.options = options
        labels = ", ".join(
            f"{opt.label} ({opt.internal_id})" if opt.label else opt.internal_id
            for opt in options
        )
        super().__init__(
            "Seleziona un preventivo valido per l'import STR Vision."
            + (f" Disponibili: {labels}" if labels else "")
        )


@dataclass
class _GroupValue:
    grp_id: str
    code: str
    description: str | None
    kind: str  # spatial | wbs6 | wbs7 | other
    level: int | None = None


@dataclass
class _ProductEntry:
    prodotto_id: str
    code: str
    description: str
    unit_id: str | None
    unit_label: str | None
    price_by_list: dict[str, float]
    price_priorities: dict[str, int]
    wbs6_code: str | None
    wbs6_description: str | None
    wbs7_code: str | None
    wbs7_description: str | None
    soa_category: str | None = None
    soa_description: str | None = None

    def pick_price(
        self,
        lista_id: str | None,
        preferred_lists: list[str],
    ) -> float | None:
        if lista_id and lista_id in self.price_by_list:
            return self.price_by_list[lista_id]
        for candidate in preferred_lists:
            if candidate in self.price_by_list:
                return self.price_by_list[candidate]
        if self.price_by_list:
            return next(iter(self.price_by_list.values()))
        return None


@dataclass
class _AggregatedVoce:
    product: _ProductEntry
    prezzo: float
    wbs_levels: list[ParsedWbsLevel]
    unita: str | None
    progressivo: int | None
    preventivo_id: str | None
    ordine: int
    quantita: Decimal = field(default_factory=lambda: Decimal("0"))
    notes: set[str] = field(default_factory=set)
    progressivi: set[tuple[str, int]] = field(default_factory=set)
    lista_ids: set[str] = field(default_factory=set)
    reference_ids: set[tuple[str, int]] = field(default_factory=set)
    line_amount_total: Decimal = field(default_factory=lambda: Decimal("0.00"))


@dataclass
class _MisuraContext:
    product: Decimal | None
    references: list[int]

    @property
    def has_references(self) -> bool:
        return bool(self.references)


@dataclass
class PreventivoOption:
    internal_id: str
    code: str | None
    description: str | None
    # Extended metadata
    author: str | None = None
    version: str | None = None
    date: str | None = None
    price_list_id: str | None = None
    price_list_label: str | None = None
    rilevazioni: int = 0
    items: int = 0
    total_importo: float | None = None

    @property
    def label(self) -> str | None:
        if self.description:
            return self.description
        if self.code:
            return self.code
        return self.internal_id


class SixImportService:
    """
    Importa file STR Vision (.six o .xml) popolando WBS, elenco prezzi e computo di progetto.
    """

    def __init__(self) -> None:
        self._excel_importer = ImportService()
        self._parser_cls = SixParser

    def import_six_file(
        self,
        session: Session,
        commessa_id: int,
        file_path: Path,
        *,
        preventivo_id: str | None = None,
        compute_embeddings: bool = False,
        extract_properties: bool = False,
    ) -> dict:
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

        xml_bytes = _load_xml_bytes(file_path)
        parser = self._parser_cls(xml_bytes)
        price_list_labels = dict(parser.price_lists)
        preferred_lists = list(parser.preferred_price_lists)
        resolved_preventivo_id: str | None = None
        has_preventivi = bool(parser.preventivi)

        # Scenario 1: preventivo presente -> import completo (computo + listino)
        if has_preventivi:
            parsed_computo = parser.parse(preventivo_id=preventivo_id)
            if not parsed_computo.voci:
                raise ValueError("Nessuna voce di computo trovata nel file STR Vision")
            price_catalog = parser.export_price_catalog()
            resolved_preventivo_id = parser.last_preventivo_id or preventivo_id
            transaction_ctx = (
                session.begin_nested() if session.in_transaction() else session.begin()
            )
            with transaction_ctx:
                self._import_parsed_computo(
                    session=session,
                    commessa=commessa,
                    file_path=file_path,
                    parsed_computo=parsed_computo,
                    price_catalog=price_catalog,
                    price_list_labels=price_list_labels,
                    preferred_lists=preferred_lists,
                    preventivo_id=resolved_preventivo_id,
                    compute_embeddings=compute_embeddings,
                    extract_properties=extract_properties,
                )
            report = self._build_report(session, commessa_id)
            report["importo_totale"] = parsed_computo.totale_importo or 0.0
            report["commessa_id"] = commessa_id
            report["price_items"] = len(price_catalog)
            report["preventivo_id"] = resolved_preventivo_id
            report["listino_only"] = False
            return report

        # Scenario 2: nessun preventivo -> importa solo listino prezzi
        price_catalog = parser.export_price_catalog()
        transaction_ctx = session.begin_nested() if session.in_transaction() else session.begin()
        with transaction_ctx:
            self._import_price_catalog_only(
                session=session,
                commessa=commessa,
                file_path=file_path,
                price_catalog=price_catalog,
                price_list_labels=price_list_labels,
                preferred_lists=preferred_lists,
                compute_embeddings=compute_embeddings,
                extract_properties=extract_properties,
            )

        report = self._build_report(session, commessa_id)
        report["importo_totale"] = 0.0
        report["commessa_id"] = commessa_id
        report["price_items"] = len(price_catalog)
        report["preventivo_id"] = None
        report["listino_only"] = True
        return report

    def inspect_content(self, file_bytes: bytes, filename: str | None = None) -> list[PreventivoOption]:
        xml_bytes = _load_xml_from_upload(file_bytes, filename)
        parser = self._parser_cls(xml_bytes)
        return parser.list_preventivi()

    def inspect_details(self, file_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
        """
        Esplora il contenuto di un file SIX/XML senza importare nulla.

        Restituisce una panoramica di preventivi, listini e WBS per consentire all'utente
        di investigare cosa contiene il file prima di procedere con l'import.
        """
        xml_bytes = _load_xml_from_upload(file_bytes, filename)
        parser = self._parser_cls(xml_bytes)
        return parser.inspect_structure()

    def _import_parsed_computo(
        self,
        session: Session,
        commessa: Commessa,
        file_path: Path,
        parsed_computo: ParsedComputo,
        *,
        price_catalog: Sequence[dict[str, Any]],
        price_list_labels: dict[str, str],
        preferred_lists: Sequence[str],
        preventivo_id: str | None,
        compute_embeddings: bool,
        extract_properties: bool,
    ) -> None:
        self._purge_commessa_data(session, commessa.id)
        price_catalog_service.replace_catalog(
            session=session,
            commessa=commessa,
            entries=price_catalog,
            source_file=file_path.name,
            preventivo_id=preventivo_id,
            price_list_labels=price_list_labels,
            preferred_lists=list(preferred_lists),
            compute_embeddings=compute_embeddings,
            extract_properties=extract_properties,
        )

        computo = Computo(
            commessa_id=commessa.id,
            commessa_code=commessa.codice,
            nome=parsed_computo.titolo
            or f"{commessa.nome} - Computo STR Vision",
            tipo=ComputoTipo.progetto,
            file_nome=file_path.name,
            file_percorso=str(file_path),
            importo_totale=parsed_computo.totale_importo,
        )
        session.add(computo)
        session.flush()

        self._excel_importer.persist_project_from_parsed(
            session=session,
            commessa_id=commessa.id,
            computo=computo,
            parsed_voci=parsed_computo.voci,
        )

    def _purge_commessa_data(self, session: Session, commessa_id: int) -> None:
        voce_ids_subquery = select(VoceNorm.id).where(VoceNorm.commessa_id == commessa_id)

        session.exec(
            VoceOfferta.__table__.delete().where(VoceOfferta.voce_id.in_(voce_ids_subquery))
        )
        session.exec(
            VoceProgetto.__table__.delete().where(VoceProgetto.voce_id.in_(voce_ids_subquery))
        )
        session.exec(VoceNorm.__table__.delete().where(VoceNorm.commessa_id == commessa_id))
        session.exec(Wbs7.__table__.delete().where(Wbs7.commessa_id == commessa_id))
        session.exec(Wbs6.__table__.delete().where(Wbs6.commessa_id == commessa_id))
        session.exec(WbsSpaziale.__table__.delete().where(WbsSpaziale.commessa_id == commessa_id))

        computi_rows = session.exec(
            select(Computo.id).where(
                Computo.commessa_id == commessa_id,
                Computo.tipo == ComputoTipo.progetto,
            )
        ).all()
        computi_ids: list[int] = []
        for row in computi_rows:
            try:
                value = row[0]  # type: ignore[index]
            except Exception:  # noqa: BLE001
                value = getattr(row, "id", None)
            if value is None:
                continue
            computi_ids.append(int(value))
        if computi_ids:
            session.exec(
                VoceComputo.__table__.delete().where(VoceComputo.computo_id.in_(computi_ids))
            )
            session.exec(Computo.__table__.delete().where(Computo.id.in_(computi_ids)))

    def _build_report(self, session: Session, commessa_id: int) -> dict:
        wbs_spaziali = self._scalar_count(
            session,
            select(func.count(WbsSpaziale.id)).where(WbsSpaziale.commessa_id == commessa_id),
        )
        wbs6 = self._scalar_count(
            session,
            select(func.count(Wbs6.id)).where(Wbs6.commessa_id == commessa_id),
        )
        wbs7 = self._scalar_count(
            session,
            select(func.count(Wbs7.id)).where(Wbs7.commessa_id == commessa_id),
        )
        voci = self._scalar_count(
            session,
            select(func.count(VoceNorm.id)).where(VoceNorm.commessa_id == commessa_id),
        )
        return {
            "wbs_spaziali": wbs_spaziali,
            "wbs6": wbs6,
            "wbs7": wbs7,
            "voci": voci,
        }

    def _import_price_catalog_only(
        self,
        *,
        session: Session,
        commessa: Commessa,
        file_path: Path,
        price_catalog: Sequence[dict[str, Any]],
        price_list_labels: dict[str, str],
        preferred_lists: Sequence[str],
        compute_embeddings: bool,
        extract_properties: bool,
    ) -> None:
        """
        Importa solo l'elenco prezzi senza toccare WBS e computi.

        Utile per file SIX che non contengono preventivi ma includono listini.
        """
        price_catalog_service.replace_catalog(
            session=session,
            commessa=commessa,
            entries=price_catalog,
            source_file=file_path.name,
            preventivo_id=None,
            price_list_labels=price_list_labels,
            preferred_lists=list(preferred_lists),
            compute_embeddings=compute_embeddings,
            extract_properties=extract_properties,
        )

    @staticmethod
    def _scalar_count(session: Session, statement) -> int:
        value = session.exec(statement).scalar_one()
        if value is None:
            return 0
        return int(value)


class SixParser:
    # Improved pattern to capture multiple reference formats
    _reference_pattern = re.compile(
        r"(?:voce|rif\.?|riferimento|prog\.?|progressivo)\s*(?:n\.|nr\.?|num\.?)?\s*(\d+)|"  # voce n. 123, rif. 123, prog. 123
        r"#(\d+)|"  # #123
        r"→\s*(\d+)|"  # → 123
        r"\[(\d+)\]|"  # [123]
        r"<(\d+)>",  # <123>
        re.IGNORECASE
    )
    _price_list_key_pattern = re.compile(r"[^a-z0-9]+")

    def __init__(self, xml_bytes: bytes) -> None:
        self.root = ET.fromstring(xml_bytes)
        self.ns = self._detect_namespace(self.root)
        self.group_values: dict[str, _GroupValue] = {}
        self.units: dict[str, str] = {}
        self.products: dict[str, _ProductEntry] = {}
        self.soa_categories: dict[str, tuple[str, str]] = {}  # soaId -> (code, description)
        self.primary_title: str | None = None
        self.preventivi: dict[str, PreventivoOption] = {}
        self._preventivo_nodes: dict[str, ET.Element] = {}
        self._preventivo_index_by_code: dict[str, str] = {}
        self.last_preventivo_id: str | None = None
        self._parse_soa_categories()
        self._parse_groups()
        self.price_lists: dict[str, str] = {}
        self.preferred_price_lists: list[str] = []
        self._price_list_aliases: dict[str, str] = {}
        self._price_list_alias_priorities: dict[str, int] = {}
        self.primary_price_list_id: str | None = None
        self._primary_price_list_priority: int = -1
        # progressivo_key = (preventivo_id, progressivo)
        self._raw_progressivo_quantities: dict[tuple[str, int], Decimal] = {}
        self._progressivo_references: dict[tuple[str, int], list[tuple[tuple[str, int], Decimal]]] = {}
        self._resolved_progressivo_quantities: dict[tuple[str, int], Decimal | None] = {}
        self.last_used_product_ids: set[str] | None = None
        self._parse_price_lists()
        self._parse_units()
        self._parse_products()
        self._precompute_raw_quantities()
        self._parse_preventivi_metadata()

    def list_preventivi(self) -> list[PreventivoOption]:
        return list(self.preventivi.values())

    def inspect_structure(self) -> dict[str, Any]:
        price_lists = self._build_price_list_stats()

        preventivi: list[dict[str, Any]] = []
        for preventivo_id, option in self.preventivi.items():
            node = self._preventivo_nodes.get(preventivo_id)
            rilevazioni = 0
            prodotti: set[str] = set()
            if node is not None:
                for rilevazione in node.findall(f"{self.ns}prvRilevazione"):
                    rilevazioni += 1
                    prodotto_id = rilevazione.attrib.get("prodottoId")
                    if prodotto_id:
                        prodotti.add(prodotto_id)
            preventivi.append(
                {
                    "internal_id": option.internal_id,
                    "code": option.code,
                    "description": option.description,
                    "author": option.author,
                    "version": option.version,
                    "date": option.date,
                    "price_list_id": option.price_list_id,
                    "rilevazioni": rilevazioni,
                    "items": len(prodotti),
                }
            )
        preventivi.sort(
            key=lambda item: (
                item.get("description") or "",
                item.get("code") or item["internal_id"],
            )
        )

        return {
            "preventivi": preventivi,
            "price_lists": price_lists,
            "wbs_spaziali": self._collect_group_kind("spatial"),
            "wbs6": self._collect_group_kind("wbs6"),
            "wbs7": self._collect_group_kind("wbs7"),
            "products_total": len(self.products),
        }

    def export_price_catalog(self) -> list[dict[str, Any]]:
        aggregated: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        allowed_products = self.last_used_product_ids
        for prodotto_id in sorted(self.products.keys()):
            if allowed_products is not None and prodotto_id not in allowed_products:
                continue
            entry = self.products[prodotto_id]
            key = self._price_catalog_key(entry)
            payload = {
                "product_id": entry.prodotto_id,
                "code": entry.code,
                "description": entry.description,
                "unit_id": entry.unit_id,
                "unit_label": entry.unit_label,
                "wbs6_code": entry.wbs6_code,
                "wbs6_description": entry.wbs6_description,
                "wbs7_code": entry.wbs7_code,
                "wbs7_description": entry.wbs7_description,
                "soa_category": entry.soa_category,
                "soa_description": entry.soa_description,
                "price_lists": dict(entry.price_by_list),
                "_price_priorities": dict(entry.price_priorities),
            }
            existing = aggregated.get(key)
            if existing is None:
                aggregated[key] = payload
            else:
                self._merge_catalog_entry(existing, payload)
                self._merge_price_list_payload(
                    existing.get("price_lists") or {},
                    existing.get("_price_priorities") or {},
                    payload["price_lists"],
                    payload["_price_priorities"],
                )

        catalog: list[dict[str, Any]] = []
        for entry in aggregated.values():
            entry.pop("_price_priorities", None)
            catalog.append(entry)
        catalog.sort(
            key=lambda item: (
                item["code"],
                item.get("wbs6_code") or "",
                item.get("wbs7_code") or "",
                item.get("description") or "",
            )
        )
        return catalog

    def parse(self, preventivo_id: str | None = None) -> ParsedComputo:
        target_id = self._resolve_preventivo_id(preventivo_id)
        self.last_preventivo_id = target_id
        preventivo_node = self._preventivo_nodes[target_id]
        option = self.preventivi[target_id]
        self.primary_title = option.description or option.code or option.internal_id
        preventivo_price_list = self._map_price_list_id(option.price_list_id)
        price_preference = self._build_price_preference(preventivo_price_list)

        aggregates: dict[
            tuple[str, int | None, tuple[tuple[int, str], ...], str | None, str | None],
            _AggregatedVoce,
        ] = {}
        ordered_keys: list[
            tuple[str, int | None, tuple[tuple[int, str], ...], str | None, str | None]
        ] = []
        used_product_ids: set[str] = set()

        for rilevazione in preventivo_node.findall(f"{self.ns}prvRilevazione"):
            prodotto_id = rilevazione.attrib.get("prodottoId")
            if not prodotto_id:
                continue
            product = self.products.get(prodotto_id)
            if not product:
                logger.warning("Prodotto %s non trovato nel prezzario", prodotto_id)
                continue
            used_product_ids.add(product.prodotto_id)

            progressivo = _to_int(rilevazione.attrib.get("progressivo"))
            comments = self._collect_comments(rilevazione)
            reference_entries = self._collect_reference_entries(rilevazione, target_id)
            raw_quantita = self._compute_quantity(rilevazione)
            quantita: Decimal = raw_quantita if raw_quantita is not None else Decimal("0")
            lista_id = self._map_price_list_id(
                rilevazione.attrib.get("listaQuotazioneId")
            )

            missing_refs: list[int] = []
            if reference_entries:
                ref_total = Decimal("0")
                for ref_key, factor in reference_entries:
                    ref_value = self._resolved_progressivo_quantities.get(ref_key)
                    if ref_value is None:
                        ref_value = self._raw_progressivo_quantities.get(ref_key)
                    if ref_value is None:
                        missing_refs.append(ref_key[1])
                        continue
                    ref_total += Decimal(str(factor)) * ref_value
                if ref_total:
                    quantita += ref_total
            if missing_refs:
                logger.warning(
                    "Voce %s progressivo %s: riferimenti non risolti %s",
                    product.code,
                    progressivo,
                    missing_refs,
                )

            prezzo = product.pick_price(lista_id, price_preference)
            if prezzo is None:
                logger.warning("Voce %s ignorata: prezzo non disponibile", product.code)
                continue

            wbs_levels = self._collect_wbs_levels(rilevazione, product)
            if not any(level.level == 6 for level in wbs_levels):
                logger.warning(
                    "Voce %s ignorata: impossibile determinare WBS6",
                    product.code,
                )
                continue

            aggregate_key = self._build_aggregate_key(
                product,
                wbs_levels,
                progressivo,
                target_id,
            )
            entry = aggregates.get(aggregate_key)
            if entry is None:
                entry = _AggregatedVoce(
                    product=product,
                    prezzo=prezzo,
                    wbs_levels=wbs_levels,
                    unita=product.unit_label,
                    progressivo=progressivo,
                    preventivo_id=target_id,
                    ordine=len(ordered_keys),
                )
                aggregates[aggregate_key] = entry
                ordered_keys.append(aggregate_key)
            else:
                if entry.prezzo != prezzo:
                    logger.warning(
                        "Voce %s: rilevato prezzo differente (%s vs %s), uso il primo",
                        product.code,
                        prezzo,
                        entry.prezzo,
                    )

            if progressivo is not None:
                entry.progressivi.add((target_id, progressivo))
            if lista_id:
                entry.lista_ids.add(lista_id)
            if reference_entries:
                entry.reference_ids.update(ref_key for ref_key, _ in reference_entries)

            quantita, line_amount = self._calculate_line_amount(quantita, prezzo)
            entry.quantita += quantita
            if line_amount is not None:
                entry.line_amount_total += line_amount
            entry.notes.update(comments)

        total_amount_decimal = Decimal("0.00")
        voci: list[ParsedVoce] = []
        for key in ordered_keys:
            entry = aggregates[key]
            quantita = entry.quantita
            prezzo = entry.prezzo
            importo: float | None = None

            # Arrotonda la quantità a 2 decimali solo all'output finale
            quantita_rounded = quantita.quantize(MEASURE_QUANTUM, rounding=ROUND_HALF_UP)
            quantita_float = float(quantita_rounded)
            importo_decimal = entry.line_amount_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            importo = float(importo_decimal)
            total_amount_decimal += importo_decimal

            code = entry.product.code
            if importo is None:
                logger.warning("Voce %s ignorata: importo non valido", code)
                continue

            # Se la quantità o l'importo sono trascurabili, azzera per evitare -0.00
            if abs(quantita_float) < 1e-9:
                quantita_float = 0.0
            if abs(importo) < 1e-9:
                importo = 0.0

            note = self._build_note(sorted(entry.notes))
            meta_wbs_path = [
                {
                    "level": livello.level,
                    "code": livello.code,
                    "description": livello.description,
                }
                for livello in entry.wbs_levels
            ]
            voce_metadata = {
                "source": "six",
                "product_id": entry.product.prodotto_id,
                "unit_id": entry.product.unit_id,
                "unit_label": entry.unita,
                "price_lists": entry.product.price_by_list,
                "preferred_price_lists": self.preferred_price_lists,
                "lista_quotazione_ids": sorted(entry.lista_ids),
                "price_list_labels": {
                    list_id: self.price_lists.get(list_id)
                    for list_id in entry.lista_ids
                    if list_id in self.price_lists
                },
                "progressivi": [
                    {"preventivo_id": pid, "progressivo": prog}
                    for pid, prog in sorted(entry.progressivi, key=lambda x: (x[0], x[1]))
                ],
                "reference_progressivi": [
                    {"preventivo_id": pid, "progressivo": prog}
                    for pid, prog in sorted(entry.reference_ids, key=lambda x: (x[0], x[1]))
                ],
                "preventivo_id": entry.preventivo_id,
                "wbs6_code": entry.product.wbs6_code,
                "wbs7_code": entry.product.wbs7_code,
                "wbs_path": meta_wbs_path,
            }
            if entry.notes:
                voce_metadata["comments"] = sorted(entry.notes)
            voce = ParsedVoce(
                ordine=len(voci),
                progressivo=entry.progressivo,
                codice=code,
                descrizione=entry.product.description,
                wbs_levels=entry.wbs_levels,
                unita_misura=entry.unita,
                quantita=quantita_float,
                prezzo_unitario=prezzo,
                importo=importo,
                note=note,
                metadata=voce_metadata,
            )
            logger.debug(
                "Voce %s - Q=%.3f P=%.2f I=%.2f",
                code,
                voce.quantita or 0,
                prezzo or 0,
                importo,
            )
            voci.append(voce)

        totale_importo = (
            float(total_amount_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            if voci
            else None
        )
        quantita_values = [voce.quantita for voce in voci if voce.quantita is not None]
        totale_quantita = (
            round(sum(quantita_values), 4) if quantita_values else None
        )
        self.last_used_product_ids = used_product_ids or set()
        return ParsedComputo(
            titolo=self.primary_title,
            totale_importo=totale_importo,
            totale_quantita=totale_quantita,
            voci=voci,
        )


    def _collect_wbs_levels(
        self,
        rilevazione: ET.Element,
        product: _ProductEntry,
    ) -> list[ParsedWbsLevel]:
        levels: dict[int, ParsedWbsLevel] = {}
        for grp in rilevazione.findall(f"{self.ns}prvGrpValore"):
            grp_id = grp.attrib.get("grpValoreId")
            if not grp_id:
                continue
            meta = self.group_values.get(grp_id)
            if not meta or meta.kind != "spatial" or not meta.level:
                continue
            levels[meta.level] = ParsedWbsLevel(
                level=meta.level,
                code=meta.code,
                description=meta.description,
            )
        if product.wbs6_code:
            levels[6] = ParsedWbsLevel(
                level=6,
                code=product.wbs6_code,
                description=product.wbs6_description or product.wbs6_code,
            )
        if product.wbs7_code:
            levels[7] = ParsedWbsLevel(
                level=7,
                code=product.wbs7_code,
                description=product.wbs7_description or product.wbs7_code,
            )
        return [levels[idx] for idx in sorted(levels.keys())]

    def _collect_group_kind(self, kind: str) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        for meta in self.group_values.values():
            if meta.kind != kind:
                continue
            groups.append(
                {
                    "grp_id": meta.grp_id,
                    "code": meta.code,
                    "description": meta.description,
                    "level": meta.level,
                }
            )
        groups.sort(key=lambda item: ((item["level"] or 99), item["code"] or ""))
        return groups

    def _build_aggregate_key(
        self,
        product: _ProductEntry,
        wbs_levels: Sequence[ParsedWbsLevel],
        progressivo: int | None,
        preventivo_id: str,
    ) -> tuple[str, int | None, tuple[tuple[int, str], ...], str | None, str | None]:
        spatial_tokens: list[tuple[int, str]] = []
        wbs6_token: str | None = None
        wbs7_token: str | None = None
        for livello in wbs_levels:
            token = self._pick_identifier(livello.code, livello.description)
            if not token:
                continue
            if livello.level <= 5:
                spatial_tokens.append((livello.level, token))
            elif livello.level == 6 and wbs6_token is None:
                wbs6_token = token
            elif livello.level == 7 and wbs7_token is None:
                wbs7_token = token
        if wbs6_token is None:
            wbs6_token = self._pick_identifier(product.wbs6_code, product.wbs6_description)
        if wbs7_token is None:
            wbs7_token = self._pick_identifier(product.wbs7_code, product.wbs7_description)
        # Includiamo preventivo e progressivo nell'aggregate key
        return (preventivo_id, progressivo, tuple(spatial_tokens), wbs6_token, wbs7_token)

    def _build_price_list_stats(self) -> list[dict[str, Any]]:
        stats: dict[str, dict[str, Any]] = {}

        def _ensure_entry(canonical_id: str) -> dict[str, Any]:
            return stats.setdefault(
                canonical_id,
                {
                    "canonical_id": canonical_id,
                    "label": self.price_lists.get(canonical_id) or canonical_id,
                    "aliases": set(),
                    "priority": -1,
                    "products": set(),
                    "rilevazioni": 0,
                },
            )

        for canonical_id in self.price_lists.keys():
            _ensure_entry(canonical_id)
        for alias, canonical in self._price_list_aliases.items():
            entry = _ensure_entry(canonical)
            if alias:
                entry["aliases"].add(alias)
            priority = self._price_list_alias_priorities.get(alias, -1)
            entry["priority"] = max(entry["priority"], priority)

        for prodotto in self.products.values():
            for list_id in prodotto.price_by_list.keys():
                entry = _ensure_entry(list_id)
                entry["products"].add(prodotto.prodotto_id)

        for preventivo in self._preventivo_nodes.values():
            for rilevazione in preventivo.findall(f"{self.ns}prvRilevazione"):
                mapped = self._map_price_list_id(rilevazione.attrib.get("listaQuotazioneId"))
                if not mapped:
                    continue
                entry = _ensure_entry(mapped)
                entry["rilevazioni"] += 1

        price_lists: list[dict[str, Any]] = []
        for canonical_id, entry in stats.items():
            price_lists.append(
                {
                    "canonical_id": canonical_id,
                    "label": entry["label"],
                    "aliases": sorted(entry["aliases"]),
                    "priority": entry["priority"] if entry["priority"] >= 0 else 0,
                    "products": len(entry["products"]),
                    "rilevazioni": entry["rilevazioni"],
                }
            )
        price_lists.sort(key=lambda item: (-item["priority"], item["canonical_id"]))
        return price_lists

    def _price_catalog_key(self, entry: _ProductEntry) -> tuple[str, str, str, str]:
        return (
            self._catalog_token(entry.code),
            self._catalog_token(entry.unit_label, entry.unit_id),
            self._catalog_token(entry.wbs6_code),
            self._catalog_token(entry.wbs7_code),
        )

    @staticmethod
    def _merge_catalog_entry(target: dict[str, Any], source: dict[str, Any]) -> None:
        if not target.get("description") and source.get("description"):
            target["description"] = source["description"]
        elif (
            target.get("description")
            and source.get("description")
            and len(source["description"]) > len(target["description"])
        ):
            target["description"] = source["description"]

        for field in ("unit_id", "unit_label", "wbs6_code", "wbs6_description", "wbs7_code", "wbs7_description"):
            if not target.get(field) and source.get(field):
                target[field] = source[field]

    @staticmethod
    def _merge_price_list_payload(
        target_prices: dict[str, float],
        target_priorities: dict[str, int],
        source_prices: dict[str, float],
        source_priorities: dict[str, int],
    ) -> None:
        for list_id, value in source_prices.items():
            source_priority = source_priorities.get(list_id, 0)
            existing_priority = target_priorities.get(list_id, -1)
            if list_id not in target_prices or source_priority > existing_priority:
                target_prices[list_id] = value
                target_priorities[list_id] = source_priority

    @staticmethod
    def _catalog_token(*values: str | None) -> str:
        for value in values:
            if not value:
                continue
            normalized = unicodedata.normalize("NFKD", value)
            normalized = normalized.replace("²", "2").replace("³", "3")
            cleaned = "".join(ch for ch in normalized if ch.isalnum())
            cleaned = cleaned.lower()
            if cleaned:
                return cleaned
        return ""

    @staticmethod
    def _pick_identifier(*values: str | None) -> str | None:
        for value in values:
            if not value:
                continue
            text = value.strip()
            if text:
                return text.casefold()
        return None

    @staticmethod
    def _parse_numeric_value(raw: str | None) -> Decimal | None:
        """
        Interpreta il contenuto testuale di una cella misura.
        Supporta espressioni semplici (somma, sottrazione, moltiplicazione, divisione)
        con separatore decimale sia punto che virgola e operatori moltiplicativi
        scritti come "x", "·" o "×". Converte anche separatori di lista ";"/a capo
        in somme.

        Restituisce Decimal per preservare la precisione decimale ed evitare
        errori di rappresentazione floating-point.
        """
        if not raw:
            return None
        cleaned = raw.replace(",", ".")
        cleaned = cleaned.replace("×", "*").replace("·", "*").replace("x", "*").replace("X", "*")
        cleaned = re.sub(r"[;\r\n]+", "+", cleaned).strip()
        if not cleaned:
            return None

        allowed_bin_ops = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
        }
        allowed_unary_ops = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}

        def _eval(node: ast.AST) -> Decimal:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_bin_ops:
                left = _eval(node.left)
                right = _eval(node.right)
                return allowed_bin_ops[type(node.op)](left, right)
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary_ops:
                operand = _eval(node.operand)
                return allowed_unary_ops[type(node.op)](operand)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return Decimal(str(node.value))
            # Python <=3.7 compat
            if hasattr(ast, "Num") and isinstance(node, ast.Num):  # type: ignore[attr-defined]
                return Decimal(str(node.n))  # type: ignore[attr-defined]
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")

        def _evaluate_expression(expr_text: str) -> Decimal:
            parsed = ast.parse(expr_text, mode="eval")
            return _eval(parsed)

        # Gestione espressioni condizionali (es. "2.07*1<4" → 1 se 2.07<4, altrimenti 0)
        comparison_match = re.match(r"^(.+?)([<>]=?)(.+)$", cleaned)
        if comparison_match:
            left_expr = comparison_match.group(1).strip()
            operator = comparison_match.group(2)
            right_expr = comparison_match.group(3).strip()
            try:
                left_val = _evaluate_expression(left_expr)
                right_val = _evaluate_expression(right_expr)
                # Applica il confronto e restituisce 1 (vero) o 0 (falso)
                if operator == "<":
                    result = Decimal("1") if left_val < right_val else Decimal("0")
                elif operator == "<=":
                    result = Decimal("1") if left_val <= right_val else Decimal("0")
                elif operator == ">":
                    result = Decimal("1") if left_val > right_val else Decimal("0")
                elif operator == ">=":
                    result = Decimal("1") if left_val >= right_val else Decimal("0")
                else:
                    return None
                return result
            except Exception:
                return None

        try:
            result = _evaluate_expression(cleaned)
            # Arrotonda secondo la granularità di misura configurata (0.01 di default)
            return result.quantize(MEASURE_QUANTUM, rounding=ROUND_HALF_UP)
        except Exception:
            # fallback: tenta un semplice Decimal
            float_val = _to_float(cleaned)
            if float_val is None:
                return None
            result = Decimal(str(float_val))
            return result.quantize(MEASURE_QUANTUM, rounding=ROUND_HALF_UP)

    def _collect_comments(self, rilevazione: ET.Element) -> list[str]:
        comments: list[str] = []
        for commento in rilevazione.findall(f".//{self.ns}prvCommento"):
            text = commento.attrib.get("estesa") or commento.text
            if not text:
                continue
            cleaned = text.strip()
            if cleaned:
                comments.append(cleaned)
        return comments

    @staticmethod
    def _normalize_measure(value: Decimal | None) -> Decimal | None:
        """Arrotonda il prodotto delle misure alla granularità configurata."""
        if value is None:
            return None
        return value.quantize(MEASURE_QUANTUM, rounding=ROUND_HALF_UP)

    def _parse_misura_context(self, misura: ET.Element) -> _MisuraContext:
        grouped: dict[int, Decimal] = {}
        all_cells_raw: list[tuple[int, str, Decimal | None]] = []
        for cella in misura.findall(f"{self.ns}prvCella"):
            raw_text = cella.attrib.get("testo")
            value = self._parse_numeric_value(raw_text)
            pos_label = cella.attrib.get("posizione") or "0"
            try:
                position = int(pos_label)
            except ValueError:
                position = 0
            all_cells_raw.append((position, raw_text or "", value))

            if value is None:
                continue
            grouped[position] = grouped.get(position, Decimal("0")) + value

        if all_cells_raw:
            logger.debug("Celle misura: %s -> grouped=%s", all_cells_raw, grouped)

        # Raccogli commenti e riferimenti
        references: list[int] = []
        for commento in misura.findall(f"{self.ns}prvCommento"):
            text = commento.attrib.get("estesa") or commento.text
            if not text:
                continue
            for match in self._reference_pattern.findall(text):
                # Pattern has multiple capture groups, find the non-empty one
                if isinstance(match, tuple):
                    raw = next((g for g in match if g), None)
                else:
                    raw = match
                if not raw:
                    continue
                try:
                    references.append(int(raw))
                except ValueError:
                    continue

        # Calcola il prodotto secondo le regole:
        # 1. Riga senza valori → ignora (product = None)
        # 2. Riga con valori, alcuni sono 0 esplicito → prodotto = 0
        # 3. Riga con valori tutti non-zero → moltiplica tutti
        # NOTA: celle vuote vengono ignorate (non sono zeri espliciti)
        # NOTA: commenti senza valori vengono ignorati (non contribuiscono al calcolo)
        product: Decimal | None = None
        if grouped:
            has_zero = any(v == Decimal("0") for v in grouped.values())
            if has_zero:
                product = Decimal("0")
                logger.debug("Misura con zero esplicito: grouped=%s -> product=0", grouped)
            else:
                product = Decimal("1")
                for value in grouped.values():
                    product *= value
                logger.debug("Misura calcolata: grouped=%s -> product=%s", grouped, product)
            product = self._normalize_measure(product)
        # else: nessun valore numerico → product = None (ignorata)

        return _MisuraContext(product=product, references=references)

    def _collect_reference_entries(
        self,
        rilevazione: ET.Element,
        preventivo_id: str,
    ) -> list[tuple[tuple[str, int], Decimal]]:
        entries: list[tuple[int, Decimal]] = []
        current_sign = 1
        for misura in rilevazione.findall(f"{self.ns}prvMisura"):
            operation = (misura.attrib.get("operazione") or "").strip()
            if operation == "-":
                current_sign = -1
            elif operation == "+":
                current_sign = 1
            context = self._parse_misura_context(misura)
            if not context.references:
                continue
            multiplier = context.product if context.product is not None else Decimal("1")
            for ref_prog in context.references:
                entries.append(((preventivo_id, ref_prog), Decimal(str(current_sign)) * multiplier))
        return entries

    @staticmethod
    def _build_note(comments: list[str]) -> str | None:
        if not comments:
            return None
        seen: set[str] = set()
        ordered: list[str] = []
        for text in comments:
            if text not in seen:
                ordered.append(text)
                seen.add(text)
        return "\n".join(ordered) if ordered else None

    def _compute_quantity(self, rilevazione: ET.Element) -> Decimal | None:
        total = Decimal("0")
        current_sign = 1
        for misura in rilevazione.findall(f"{self.ns}prvMisura"):
            context = self._parse_misura_context(misura)
            if context.references:
                continue
            operation = (misura.attrib.get("operazione") or "").strip()
            if operation == "-":
                current_sign = -1
            elif operation == "+":
                current_sign = 1
            if context.product is None:
                continue
            total += current_sign * context.product
        return total if abs(total) > Decimal("1e-12") else None

    def _calculate_line_amount(
        self,
        quantita: Decimal,
        prezzo: float | None,
    ) -> tuple[Decimal, Decimal | None]:
        if prezzo is None:
            return quantita, None

        decimal_price = Decimal(str(prezzo))
        if quantita == Decimal("0"):
            return Decimal("0"), Decimal("0.00")

        # Mantieni la precisione completa, arrotonda solo l'importo
        line_amount = (quantita * decimal_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return quantita, line_amount

    def _parse_groups(self) -> None:
        for gruppo in self.root.findall(f".//{self.ns}gruppo"):
            tipo = (gruppo.attrib.get("tipo") or "").strip().lower()
            kind, level = self._classify_group(tipo)
            for valore in gruppo.findall(f"{self.ns}grpValore"):
                grp_id = valore.attrib.get("grpValoreId")
                if not grp_id:
                    continue
                code = (valore.attrib.get("vlrId") or "").strip()
                desc_node = valore.find(f"{self.ns}vlrDescrizione")
                description = None
                if desc_node is not None:
                    description = (
                        desc_node.attrib.get("breve")
                        or (desc_node.text or "").strip()
                    )
                self.group_values[grp_id] = _GroupValue(
                    grp_id=grp_id,
                    code=code,
                    description=description,
                    kind=kind,
                    level=level,
                )

    def _parse_price_lists(self) -> None:
        self.price_lists = {}
        self.preferred_price_lists = []
        self._price_list_aliases = {}
        self._price_list_alias_priorities = {}
        self.primary_price_list_id = None
        self._primary_price_list_priority = -1
        preferred_seen: set[str] = set()
        for lista in self.root.findall(f".//{self.ns}listaQuotazione"):
            lista_id = lista.attrib.get("listaQuotazioneId")
            if not lista_id:
                continue
            label = lista.attrib.get("lqtId") or ""
            desc_node = lista.find(f"{self.ns}lqtDescrizione")
            if desc_node is not None:
                label = desc_node.attrib.get("breve") or desc_node.text or label
            display_label = (label or "").strip() or lista_id
            canonical_id = self._canonicalize_price_list_id(
                display_label, lista_id
            )
            self._price_list_aliases[lista_id] = canonical_id
            priority = self._determine_price_list_priority(display_label, lista_id)
            self._price_list_alias_priorities[lista_id] = priority
            if priority > self._primary_price_list_priority:
                self.primary_price_list_id = canonical_id
                self._primary_price_list_priority = priority
            existing_label = self.price_lists.get(canonical_id)
            if not existing_label or (
                display_label and len(display_label) > len(existing_label)
            ):
                self.price_lists[canonical_id] = display_label
            lowered = display_label.lower()
            if any(keyword in lowered for keyword in ("progetto", "default")):
                if canonical_id not in preferred_seen:
                    self.preferred_price_lists.append(canonical_id)
                    preferred_seen.add(canonical_id)

        if self.primary_price_list_id and self.primary_price_list_id not in preferred_seen:
            self.preferred_price_lists.insert(0, self.primary_price_list_id)

    def _canonicalize_price_list_id(
        self,
        label: str | None,
        fallback: str | None = None,
    ) -> str:
        label_norm = self._normalize_price_list_token(label)
        fallback_norm = self._normalize_price_list_token(fallback)
        if self._is_prezzi_base_label(label_norm) or self._is_prezzi_base_label(
            fallback_norm
        ):
            return "prezzi_base"
        if self._is_plain_base_label(label_norm) or self._is_plain_base_label(
            fallback_norm
        ):
            return "prezzi_base"

        candidates: list[str] = []
        if label:
            candidates.append(label)
        if fallback and fallback not in candidates:
            candidates.append(fallback)
        for candidate in candidates:
            normalized = self._price_list_key_pattern.sub(
                "_", candidate.strip().lower()
            ).strip("_")
            if normalized:
                return normalized
        if fallback:
            fallback_clean = fallback.strip().lower()
            normalized = self._price_list_key_pattern.sub("_", fallback_clean).strip("_")
            if normalized:
                return normalized
        return "listino"

    def _determine_price_list_priority(
        self,
        label: str | None,
        fallback: str | None,
    ) -> int:
        label_norm = self._normalize_price_list_token(label)
        fallback_norm = self._normalize_price_list_token(fallback)
        if self._is_prezzi_base_label(label_norm) or self._is_prezzi_base_label(
            fallback_norm
        ):
            return 2
        if self._is_plain_base_label(label_norm) or self._is_plain_base_label(
            fallback_norm
        ):
            return 1
        return 0

    @staticmethod
    def _normalize_price_list_token(value: str | None) -> str:
        return (value or "").strip().lower()

    @staticmethod
    def _is_prezzi_base_label(normalized_value: str) -> bool:
        if not normalized_value:
            return False
        return "prezzi" in normalized_value and "base" in normalized_value

    @staticmethod
    def _is_plain_base_label(normalized_value: str) -> bool:
        if not normalized_value:
            return False
        return normalized_value == "base"

    def _map_price_list_id(self, lista_id: str | None) -> str | None:
        if not lista_id:
            return None
        mapped = self._price_list_aliases.get(lista_id)
        if mapped:
            return mapped
        canonical = self._canonicalize_price_list_id(lista_id, lista_id)
        self._price_list_aliases[lista_id] = canonical
        if canonical not in self.price_lists:
            self.price_lists[canonical] = lista_id.strip()
        return canonical

    def _build_price_preference(self, primary: str | None) -> list[str]:
        """Ordina le liste prezzi da provare: prima quella del preventivo, poi le preferite globali."""
        ordered: list[str] = []
        seen: set[str] = set()
        if primary:
            ordered.append(primary)
            seen.add(primary)
        for item in self.preferred_price_lists:
            if item and item not in seen:
                ordered.append(item)
                seen.add(item)
        return ordered

    def _parse_units(self) -> None:
        for unit in self.root.findall(f".//{self.ns}unitaDiMisura"):
            unit_id = unit.attrib.get("unitaDiMisuraId")
            if not unit_id:
                continue
            label = unit.attrib.get("simbolo") or unit.attrib.get("udmId")
            desc_node = unit.find(f"{self.ns}udmDescrizione")
            if not label and desc_node is not None:
                label = desc_node.attrib.get("breve") or desc_node.text
            if not label:
                label = unit_id
            self.units[unit_id] = label.strip()

    def _parse_products(self) -> None:
        for prodotto in self.root.findall(f".//{self.ns}prodotto"):
            prodotto_id = prodotto.attrib.get("prodottoId")
            if not prodotto_id:
                continue
            code = prodotto.attrib.get("prdId") or prodotto_id
            desc_node = prodotto.find(f"{self.ns}prdDescrizione")
            desc = ""
            if desc_node is not None:
                desc = desc_node.attrib.get("estesa") or desc_node.attrib.get("breve") or ""
            desc = desc.strip() or code
            unit_id = prodotto.attrib.get("unitaDiMisuraId")
            prices: dict[str, float] = {}
            price_priorities: dict[str, int] = {}
            for quot in prodotto.findall(f"{self.ns}prdQuotazione"):
                raw_lista_id = quot.attrib.get("listaQuotazioneId")
                lista_id = self._map_price_list_id(raw_lista_id)
                value = _to_float(quot.attrib.get("valore"))
                if not lista_id or value is None:
                    continue
                priority = self._price_list_alias_priorities.get(raw_lista_id, 0)
                existing_priority = price_priorities.get(lista_id, -1)
                existing_value = prices.get(lista_id)
                if existing_priority > priority:
                    if existing_value is not None and existing_value != value:
                        logger.debug(
                            "Lista %s per prodotto %s: ignoro nuovo valore %s (priorità %s < %s)",
                            lista_id,
                            code,
                            value,
                            priority,
                            existing_priority,
                        )
                    continue
                if (
                    existing_value is not None
                    and existing_value != value
                    and priority >= existing_priority >= 0
                ):
                    logger.debug(
                        "Lista %s per prodotto %s: sovrascrivo valore %s con %s (priorità %s >= %s)",
                        lista_id,
                        code,
                        existing_value,
                        value,
                        priority,
                        existing_priority,
                    )
                prices[lista_id] = value
                price_priorities[lista_id] = priority
            wbs6_code = None
            wbs6_desc = None
            wbs7_code = None
            wbs7_desc = None
            for grp in prodotto.findall(f"{self.ns}prdGrpValore"):
                grp_id = grp.attrib.get("grpValoreId")
                if not grp_id:
                    continue
                meta = self.group_values.get(grp_id)
                if not meta:
                    continue
                if meta.kind == "wbs6" and not wbs6_code:
                    wbs6_code = (meta.code or "").strip() or None
                    wbs6_desc = meta.description
                elif meta.kind == "wbs7" and not wbs7_code:
                    wbs7_code = (meta.code or "").strip() or None
                    wbs7_desc = meta.description
            entry = _ProductEntry(
                prodotto_id=prodotto_id,
                code=code.strip(),
                description=desc,
                unit_id=unit_id,
                unit_label=self.units.get(unit_id, unit_id),
                price_by_list=prices,
                price_priorities=price_priorities,
                wbs6_code=wbs6_code,
                wbs6_description=wbs6_desc,
                wbs7_code=wbs7_code,
                wbs7_description=wbs7_desc,
            )
            self.products[prodotto_id] = entry

    def _parse_preventivi_metadata(self) -> None:
        counter = 0
        # Extract metadata from intestazione if available
        intestazione = self.root.find(f".//{self.ns}intestazione")
        global_author = None
        global_version = None
        if intestazione is not None:
            global_author = intestazione.attrib.get("autore")
            global_version = intestazione.attrib.get("versione")

        for preventivo in self.root.findall(f".//{self.ns}preventivo"):
            internal_id = preventivo.attrib.get("preventivoId")
            code = preventivo.attrib.get("prvId")
            price_list_id = preventivo.attrib.get("prezzarioId")

            if not internal_id:
                counter += 1
                internal_id = f"preventivo-{counter}"

            desc_node = preventivo.find(f"{self.ns}prvDescrizione")
            description = None
            if desc_node is not None:
                description = desc_node.attrib.get("breve") or desc_node.text
                if description:
                    description = description.strip()

            # Extract date from datiGenerali if linked
            date_str = None
            dati_generali_id = preventivo.attrib.get("datiGeneraliId")
            if dati_generali_id:
                dati_generali = self.root.find(f".//{self.ns}datiGenerali[@datiGeneraliId='{dati_generali_id}']")
                if dati_generali is not None:
                    date_str = dati_generali.attrib.get("data")

            rilevazioni_nodes = preventivo.findall(f"{self.ns}prvRilevazione")
            rilevazioni_count = len(rilevazioni_nodes)
            items_count = 0
            total_importo = Decimal("0")
            if rilevazioni_nodes:
                product_ids = {
                    node.attrib.get("prodottoId")
                    for node in rilevazioni_nodes
                    if node.attrib.get("prodottoId")
                }
                items_count = len(product_ids)
                for rilevazione in rilevazioni_nodes:
                    prodotto_id = rilevazione.attrib.get("prodottoId")
                    if not prodotto_id:
                        continue
                    product = self.products.get(prodotto_id)
                    if not product:
                        continue
                    lista_id = self._map_price_list_id(
                        rilevazione.attrib.get("listaQuotazioneId")
                    )
                    prezzo: float | None = product.pick_price(
                        lista_id,
                        self._build_price_preference(self._map_price_list_id(price_list_id)),
                    )
                    if prezzo is None:
                        continue
                    # Allinea il totale preview con il calcolo principale: quantità dirette + riferimenti
                    quantita_dec: Decimal = self._compute_quantity(rilevazione) or Decimal("0")
                    for ref_prog_key, factor in self._collect_reference_entries(rilevazione, preventivo_id):
                        ref_val = self._resolved_progressivo_quantities.get(ref_prog_key)
                        if ref_val is None:
                            ref_val = self._raw_progressivo_quantities.get(ref_prog_key)
                        if ref_val is None:
                            continue
                        quantita_dec += factor * ref_val
                    total_importo += quantita_dec * Decimal(str(prezzo))

            mapped_price_list = self._map_price_list_id(price_list_id)
            price_list_label = None
            if mapped_price_list:
                price_list_label = self.price_lists.get(mapped_price_list, mapped_price_list)

            option = PreventivoOption(
                internal_id=internal_id,
                code=code,
                description=description,
                author=global_author,
                version=global_version,
                date=date_str,
                price_list_id=price_list_id,
                price_list_label=price_list_label,
                rilevazioni=rilevazioni_count,
                items=items_count,
                total_importo=float(
                    total_importo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )
                if total_importo
                else None,
            )
            self.preventivi[internal_id] = option
            self._preventivo_nodes[internal_id] = preventivo
            if code:
                self._preventivo_index_by_code[code] = internal_id

    def _resolve_preventivo_id(self, requested: str | None) -> str:
        if requested:
            if requested in self.preventivi:
                return requested
            mapped = self._preventivo_index_by_code.get(requested)
            if mapped:
                return mapped
            raise ValueError(f"Preventivo {requested} non trovato nel file STR Vision")
        if not self.preventivi:
            raise ValueError("Il file STR Vision non contiene preventivi importabili")
        if len(self.preventivi) == 1:
            return next(iter(self.preventivi))
        raise PreventivoSelectionError(self.list_preventivi())

    def _classify_group(self, tipo: str) -> tuple[str, int | None]:
        if tipo.startswith("wbs 01"):
            return "spatial", 1
        if tipo.startswith("wbs 02"):
            return "spatial", 2
        if tipo.startswith("wbs 03"):
            return "spatial", 3
        if tipo.startswith("wbs 04"):
            return "spatial", 4
        if tipo.startswith("wbs 05"):
            return "spatial", 5
        if "wbs 06" in tipo:
            return "wbs6", 6
        if "wbs 07" in tipo:
            return "wbs7", 7
        return "other", None

    def _precompute_raw_quantities(self) -> None:
        self._raw_progressivo_quantities.clear()
        self._progressivo_references.clear()
        progressivo_owner: dict[int, str] = {}

        for preventivo in self.root.findall(f".//{self.ns}preventivo"):
            preventivo_id = preventivo.attrib.get("preventivoId") or "unknown"
            
            for rilevazione in preventivo.findall(f"{self.ns}prvRilevazione"):
                progressivo = _to_int(rilevazione.attrib.get("progressivo"))
                if progressivo is None:
                    continue

                existing_owner = progressivo_owner.get(progressivo)
                if existing_owner and existing_owner != preventivo_id:
                    logger.warning(
                        "Progressivo %s presente in più preventivi (%s, %s): uso il primo.",
                        progressivo,
                        existing_owner,
                        preventivo_id,
                    )
                    continue
                progressivo_owner.setdefault(progressivo, preventivo_id)
                progressivo_key = (preventivo_id, progressivo)

                quantity = self._compute_quantity(rilevazione)
                self._raw_progressivo_quantities[progressivo_key] = quantity or Decimal("0")
                references = self._collect_reference_entries(rilevazione, preventivo_id)
                if references:
                    self._progressivo_references[progressivo_key] = references
        
        self._resolved_progressivo_quantities.clear()
        all_progressivi = set(self._raw_progressivo_quantities.keys()) | set(
            self._progressivo_references.keys()
        )
        for progressivo_key in all_progressivi:
            self._resolve_progressivo_quantity(progressivo_key, set())

    def _resolve_progressivo_quantity(
        self,
        progressivo_key: tuple[str, int],
        stack: set[tuple[str, int]],
    ) -> Decimal | None:
        cached = self._resolved_progressivo_quantities.get(progressivo_key)
        if cached is not None:
            return cached
        if progressivo_key in stack:
            message = f"Riferimento circolare tra progressivi: {progressivo_key} -> {sorted(stack)}"
            logger.error(message)
            raise ValueError(message)

        stack.add(progressivo_key)
        base_value = self._raw_progressivo_quantities.get(progressivo_key) or Decimal("0")
        total = base_value
        for ref_prog_key, factor in self._progressivo_references.get(progressivo_key, []):
            ref_value = self._resolve_progressivo_quantity(ref_prog_key, stack)
            if ref_value is None:
                continue
            total += factor * ref_value
        stack.remove(progressivo_key)

        resolved = total if abs(total) > Decimal("1e-12") else None
        self._resolved_progressivo_quantities[progressivo_key] = resolved
        return resolved

    def _parse_soa_categories(self) -> None:
        """Parse SOA categories from categoriaSOA elements."""
        for soa_elem in self.root.findall(f".//{self.ns}categoriaSOA"):
            soa_id = soa_elem.attrib.get("soaId")
            soa_code = soa_elem.attrib.get("soaCategoria")
            if not soa_id:
                continue

            desc_node = soa_elem.find(f"{self.ns}soaDescrizione")
            description = None
            if desc_node is not None:
                description = desc_node.attrib.get("breve") or desc_node.text
                if description:
                    description = description.strip()

            self.soa_categories[soa_id] = (soa_code or "", description or "")

    @staticmethod
    def _detect_namespace(root: ET.Element) -> str:
        if root.tag.startswith("{"):
            closing = root.tag.find("}")
            if closing != -1:
                return root.tag[: closing + 1]
        return ""


def _load_xml_bytes(file_path: Path) -> bytes:
    raw = file_path.read_bytes()
    return _normalize_xml_bytes(raw, file_path.suffix)


def _load_xml_from_upload(file_bytes: bytes, filename: str | None) -> bytes:
    suffix = Path(filename).suffix if filename else ""
    return _normalize_xml_bytes(file_bytes, suffix)


def _normalize_xml_bytes(data: bytes, suffix: str | None) -> bytes:
    normalized_suffix = (suffix or "").lower()
    if normalized_suffix == ".six":
        try:
            with ZipFile(io.BytesIO(data), "r") as archive:
                candidates = [
                    name for name in archive.namelist() if name.lower().endswith(".xml")
                ]
                if not candidates:
                    raise ValueError("Il file .six non contiene documenti XML")
                candidates.sort(
                    key=lambda name: (
                        0 if name.lower().endswith("documento.xml") else 1,
                        name,
                    )
                )
                with archive.open(candidates[0]) as member:
                    return member.read()
        except BadZipFile as exc:
            raise ValueError("File .six corrotto o non valido") from exc
    elif normalized_suffix == ".xml" or not normalized_suffix:
        return data
    raise ValueError("Sono supportati solo file .six o .xml")


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip().replace("\u00a0", "")
    if not text:
        return None
    text = text.replace("%", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        expr_candidate = text.replace(" ", "")
        if any(ch in expr_candidate for ch in "+-*/"):
            evaluated = _evaluate_numeric_expression(expr_candidate)
            if evaluated is not None:
                return evaluated
        return None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value.strip()))
    except ValueError:
        return None


def _evaluate_numeric_expression(text: str) -> float | None:
    try:
        node = ast.parse(text, mode="eval")
    except SyntaxError:
        return None

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError
        if isinstance(node, ast.Num):  # pragma: no cover (py<3.8 compatibility)
            return float(node.n)
        if isinstance(node, ast.BinOp):
            if type(node.op) not in _BIN_OPS:
                raise ValueError
            return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in _UNARY_OPS:
                raise ValueError
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        raise ValueError

    try:
        return float(_eval(node))
    except (ValueError, ZeroDivisionError):
        return None


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


six_import_service = SixImportService()
