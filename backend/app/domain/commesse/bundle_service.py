from __future__ import annotations

import json
import logging
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Iterable

from fastapi import UploadFile
from sqlmodel import Session, select

from app.core import settings
from app.db.models import (
    Commessa,
    CommessaPreferences,
    Computo,
    ImportConfig,
    PriceListItem,
    PriceListOffer,
    VoceComputo,
)
from app.db.models_wbs import (
    Impresa,
    Voce as VoceNorm,
    VoceOfferta,
    VoceProgetto,
    Wbs6,
    Wbs7,
    WbsSpaziale,
    WbsVisibility,
)
from app.services.price_catalog import PriceCatalogService
from .storage import storage_service


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class CommessaBundleService:
    """Gestione esportazione/importazione bundle commessa."""

    BUNDLE_EXTENSION = ".mmcomm"
    BUNDLE_VERSION = "1.0"
    METADATA_FILE = "metadata.json"
    DATA_FILE = "data.json"
    FILES_ROOT = "files"

    def __init__(self, export_root: Path | None = None) -> None:
        self.export_root = export_root or settings.storage_root / "exports"
        self.export_root.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def is_bundle_file(self, filename: str | None) -> bool:
        if not filename:
            return False
        return Path(filename).suffix.lower() == self.BUNDLE_EXTENSION

    def export_commessa(self, session: Session, commessa_id: int) -> Path:
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            raise ValueError("Commessa non trovata")

        commessa_dir = storage_service.commessa_dir(commessa.id)
        payload = self._collect_commessa_data(session, commessa, commessa_dir)
        metadata = {
            "version": self.BUNDLE_VERSION,
            "generated_at": datetime.utcnow().isoformat(),
            "commessa_id": commessa.id,
            "commessa_codice": commessa.codice,
            "commessa_nome": commessa.nome,
        }

        safe_code = re.sub(r"[^A-Za-z0-9_-]+", "_", commessa.codice or "commessa")
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        bundle_path = self.export_root / (
            f"{safe_code}_{commessa.id}_{timestamp}{self.BUNDLE_EXTENSION}"
        )

        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(self.METADATA_FILE, json.dumps(metadata, ensure_ascii=False))
            zf.writestr(self.DATA_FILE, json.dumps(payload, ensure_ascii=False))
            self._add_commessa_files(zf, commessa_dir)

        return bundle_path

    def import_bundle_from_upload(
        self, session: Session, upload: UploadFile, *, overwrite: bool = False
    ) -> Commessa:
        if not self.is_bundle_file(upload.filename):
            raise ValueError(
                "Formato file non valido. Atteso un pacchetto .mmcomm compresso."
            )

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        with NamedTemporaryFile(delete=False, suffix=self.BUNDLE_EXTENSION) as tmp:
            total = 0
            while True:
                chunk = upload.file.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_size_bytes:
                    tmp_path = Path(tmp.name)
                    tmp_path.unlink(missing_ok=True)
                    raise ValueError(
                        "File troppo grande. Ridurre le dimensioni del pacchetto."
                    )
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
            commessa = self.import_bundle(session, tmp_path, overwrite=overwrite)
        finally:
            tmp_path.unlink(missing_ok=True)
        return commessa

    def import_bundle(
        self, session: Session, bundle_path: Path, *, overwrite: bool = False
    ) -> Commessa:
        if not bundle_path.exists():
            raise ValueError("Pacchetto di commessa non trovato")

        with zipfile.ZipFile(bundle_path, "r") as zf:
            if self.METADATA_FILE not in zf.namelist() or self.DATA_FILE not in zf.namelist():
                raise ValueError("Pacchetto non valido: metadati o dati mancanti")
            metadata = json.loads(zf.read(self.METADATA_FILE))
            data = json.loads(zf.read(self.DATA_FILE))
            self._validate_metadata(metadata)

            with TemporaryDirectory() as tmpdir:
                extracted_files = self._extract_files(zf, Path(tmpdir))
                commessa = self._rebuild_commessa(
                    session, data, extracted_files, overwrite=overwrite
                )
        return commessa

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        version = metadata.get("version")
        if version != self.BUNDLE_VERSION:
            raise ValueError(
                "Versione pacchetto non supportata. Rigenera l'esportazione aggiornata."
            )

    def _collect_commessa_data(
        self, session: Session, commessa: Commessa, commessa_dir: Path
    ) -> dict[str, Any]:
        computi = session.exec(
            select(Computo).where(Computo.commessa_id == commessa.id)
        ).all()
        computo_ids = [item.id for item in computi if item.id is not None]
        voci_computo = (
            session.exec(
                select(VoceComputo).where(VoceComputo.computo_id.in_(computo_ids))
            ).all()
            if computo_ids
            else []
        )
        price_list_items = session.exec(
            select(PriceListItem).where(PriceListItem.commessa_id == commessa.id)
        ).all()
        price_list_offers = session.exec(
            select(PriceListOffer).where(PriceListOffer.commessa_id == commessa.id)
        ).all()
        wbs_spaziale = session.exec(
            select(WbsSpaziale).where(WbsSpaziale.commessa_id == commessa.id)
        ).all()
        wbs6 = session.exec(select(Wbs6).where(Wbs6.commessa_id == commessa.id)).all()
        wbs7 = session.exec(select(Wbs7).where(Wbs7.commessa_id == commessa.id)).all()
        wbs_visibility = session.exec(
            select(WbsVisibility).where(WbsVisibility.commessa_id == commessa.id)
        ).all()
        voci = session.exec(
            select(VoceNorm).where(VoceNorm.commessa_id == commessa.id)
        ).all()
        voce_progetto = session.exec(
            select(VoceProgetto)
            .join(VoceNorm, VoceNorm.id == VoceProgetto.voce_id)
            .where(VoceNorm.commessa_id == commessa.id)
        ).all()
        voce_offerta = session.exec(
            select(VoceOfferta)
            .join(VoceNorm, VoceNorm.id == VoceOfferta.voce_id)
            .where(VoceNorm.commessa_id == commessa.id)
        ).all()
        import_configs = session.exec(
            select(ImportConfig).where(ImportConfig.commessa_id == commessa.id)
        ).all()
        prefs = session.exec(
            select(CommessaPreferences).where(
                CommessaPreferences.commessa_id == commessa.id
            )
        ).first()

        impresa_ids: set[int] = set()
        for offer in price_list_offers:
            if offer.impresa_id:
                impresa_ids.add(offer.impresa_id)
        for offerta in voce_offerta:
            if offerta.impresa_id:
                impresa_ids.add(offerta.impresa_id)
        imprese = (
            session.exec(select(Impresa).where(Impresa.id.in_(impresa_ids))).all()
            if impresa_ids
            else []
        )

        payload = {
            "commessa": self._serialize_model(commessa),
            "computi": self._serialize_models(computi, commessa_dir),
            "voci_computo": self._serialize_models(voci_computo, commessa_dir),
            "price_list_items": self._serialize_models(price_list_items, commessa_dir),
            "price_list_offers": self._serialize_models(price_list_offers, commessa_dir),
            "wbs_spaziale": self._serialize_models(wbs_spaziale, commessa_dir),
            "wbs6": self._serialize_models(wbs6, commessa_dir),
            "wbs7": self._serialize_models(wbs7, commessa_dir),
            "wbs_visibility": self._serialize_models(wbs_visibility, commessa_dir),
            "voci": self._serialize_models(voci, commessa_dir),
            "voce_progetto": self._serialize_models(voce_progetto, commessa_dir),
            "voce_offerta": self._serialize_models(voce_offerta, commessa_dir),
            "import_configs": self._serialize_models(import_configs, commessa_dir),
            "preferences": self._serialize_model(prefs) if prefs else None,
            "imprese": self._serialize_models(imprese, commessa_dir),
        }
        return payload

    def _serialize_models(
        self, items: Iterable[Any], commessa_dir: Path | None = None
    ) -> list[dict[str, Any]]:
        return [self._serialize_model(item, commessa_dir) for item in items]

    def _serialize_model(
        self, item: Any, commessa_dir: Path | None = None
    ) -> dict[str, Any]:
        if item is None:
            return {}
        payload = item.model_dump(mode="json")
        if commessa_dir and "file_percorso" in payload and payload["file_percorso"]:
            payload["file_percorso"] = self._relative_commessa_path(
                commessa_dir, payload["file_percorso"]
            )
        return payload

    def _relative_commessa_path(self, commessa_dir: Path, path_value: str) -> str:
        try:
            resolved = Path(path_value).resolve()
            if commessa_dir.exists():
                try:
                    return str(resolved.relative_to(commessa_dir))
                except ValueError:
                    pass
            storage_root = storage_service.root.resolve()
            if storage_root in resolved.parents:
                try:
                    relative_root = resolved.relative_to(storage_root)
                    parts = relative_root.parts
                    if parts and parts[0].startswith("commessa_"):
                        return str(Path(*parts[1:]))
                    return str(relative_root)
                except ValueError:
                    return str(path_value)
        except OSError:
            return str(path_value)
        return str(path_value)

    def _add_commessa_files(self, zf: zipfile.ZipFile, commessa_dir: Path) -> None:
        if not commessa_dir.exists():
            return
        for path in commessa_dir.rglob("*"):
            if path.is_file():
                arcname = Path(self.FILES_ROOT) / path.relative_to(commessa_dir)
                zf.write(path, arcname)

    def _extract_files(self, zf: zipfile.ZipFile, target_dir: Path) -> Path:
        extracted_root = target_dir / self.FILES_ROOT
        for member in zf.infolist():
            if not member.filename.startswith(f"{self.FILES_ROOT}/"):
                continue
            relative = PurePosixPath(member.filename).relative_to(self.FILES_ROOT)
            if ".." in relative.parts:
                raise ValueError("Percorso file non valido nel pacchetto")
            target_path = extracted_root / Path(*relative.parts)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, target_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        return extracted_root

    def _rebuild_commessa(
        self,
        session: Session,
        data: dict[str, Any],
        extracted_files: Path,
        *,
        overwrite: bool,
    ) -> Commessa:
        commessa_payload = data.get("commessa")
        if not commessa_payload:
            raise ValueError("Dati commessa mancanti nel pacchetto")

        existing = session.exec(
            select(Commessa).where(Commessa.codice == commessa_payload.get("codice"))
        ).first()
        if existing:
            if not overwrite:
                raise ValueError("Commessa già presente. Abilitare sovrascrittura per importare.")
            CommesseService.delete_commessa(session, existing.id)

        commessa = Commessa(
            nome=commessa_payload.get("nome"),
            codice=commessa_payload.get("codice"),
            descrizione=commessa_payload.get("descrizione"),
            note=commessa_payload.get("note"),
            business_unit=commessa_payload.get("business_unit"),
            revisione=commessa_payload.get("revisione"),
            stato=commessa_payload.get("stato"),
            created_at=_parse_datetime(commessa_payload.get("created_at"))
            or datetime.utcnow(),
            updated_at=_parse_datetime(commessa_payload.get("updated_at"))
            or datetime.utcnow(),
        )
        session.add(commessa)
        session.commit()
        session.refresh(commessa)

        mappings: dict[str, dict[int, int]] = {
            "wbs_spaziale": {},
            "wbs6": {},
            "wbs7": {},
            "computo": {},
            "price_list_item": {},
            "voce": {},
            "impresa": {},
        }

        imprese_data = data.get("imprese") or []
        for entry in imprese_data:
            normalized = entry.get("normalized_label")
            impresa = session.exec(
                select(Impresa).where(Impresa.normalized_label == normalized)
            ).first()
            if not impresa:
                impresa = Impresa(
                    label=entry.get("label"),
                    normalized_label=normalized,
                    note=entry.get("note"),
                    created_at=_parse_datetime(entry.get("created_at"))
                    or datetime.utcnow(),
                    updated_at=_parse_datetime(entry.get("updated_at"))
                    or datetime.utcnow(),
                )
                session.add(impresa)
                session.flush()
            mappings["impresa"][entry.get("id") or 0] = impresa.id

        self._restore_wbs(session, commessa, data, mappings)
        self._restore_computi(session, commessa, data, mappings, extracted_files)
        self._restore_price_list(session, commessa, data, mappings)
        self._restore_voci(session, commessa, data, mappings)
        self._restore_offers(session, commessa, data, mappings)
        self._restore_import_configs(session, commessa, data)
        self._restore_preferences(session, commessa, data)

        session.commit()
        return commessa

    def _restore_wbs(
        self,
        session: Session,
        commessa: Commessa,
        data: dict[str, Any],
        mappings: dict[str, dict[int, int]],
    ) -> None:
        commessa_id = commessa.id
        wbs_spaziale_data = data.get("wbs_spaziale") or []
        for entry in sorted(wbs_spaziale_data, key=lambda item: item.get("level", 0)):
            parent_id = entry.get("parent_id")
            new_parent = mappings["wbs_spaziale"].get(parent_id) if parent_id else None
            record = WbsSpaziale(
                commessa_id=commessa_id,
                parent_id=new_parent,
                level=entry.get("level"),
                code=entry.get("code"),
                description=entry.get("description"),
                importo_totale=entry.get("importo_totale"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)
            session.flush()
            if entry.get("id") is not None:
                mappings["wbs_spaziale"][entry["id"]] = record.id

        wbs6_data = data.get("wbs6") or []
        for entry in wbs6_data:
            new_spaziale = mappings["wbs_spaziale"].get(entry.get("wbs_spaziale_id"))
            record = Wbs6(
                commessa_id=commessa_id,
                wbs_spaziale_id=new_spaziale,
                code=entry.get("code"),
                description=entry.get("description"),
                label=entry.get("label"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)
            session.flush()
            if entry.get("id") is not None:
                mappings["wbs6"][entry["id"]] = record.id

        wbs7_data = data.get("wbs7") or []
        for entry in wbs7_data:
            new_wbs6 = mappings["wbs6"].get(entry.get("wbs6_id"))
            record = Wbs7(
                commessa_id=commessa_id,
                wbs6_id=new_wbs6,
                code=entry.get("code"),
                description=entry.get("description"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)
            session.flush()
            if entry.get("id") is not None:
                mappings["wbs7"][entry["id"]] = record.id

        visibility_data = data.get("wbs_visibility") or []
        for entry in visibility_data:
            node_id = entry.get("node_id")
            kind = entry.get("kind")
            mapped_id = None
            if kind == "spaziale":
                mapped_id = mappings["wbs_spaziale"].get(node_id)
            elif kind == "wbs6":
                mapped_id = mappings["wbs6"].get(node_id)
            elif kind == "wbs7":
                mapped_id = mappings["wbs7"].get(node_id)
            record = WbsVisibility(
                commessa_id=commessa_id,
                kind=kind,
                node_id=mapped_id or node_id,
                hidden=bool(entry.get("hidden")),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)

    def _restore_computi(
        self,
        session: Session,
        commessa: Commessa,
        data: dict[str, Any],
        mappings: dict[str, dict[int, int]],
        extracted_files: Path,
    ) -> None:
        computi_data = data.get("computi") or []
        commessa_dir = storage_service.commessa_dir(commessa.id)
        if commessa_dir.exists():
            shutil.rmtree(commessa_dir, ignore_errors=True)
        commessa_dir.mkdir(parents=True, exist_ok=True)

        for entry in computi_data:
            file_rel = entry.get("file_percorso")
            restored_path = (
                str((commessa_dir / file_rel).resolve()) if file_rel else None
            )
            record = Computo(
                commessa_id=commessa.id,
                commessa_code=commessa.codice,
                nome=entry.get("nome"),
                tipo=entry.get("tipo"),
                impresa=entry.get("impresa"),
                round_number=entry.get("round_number"),
                file_nome=entry.get("file_nome"),
                file_percorso=restored_path,
                importo_totale=entry.get("importo_totale"),
                delta_vs_progetto=entry.get("delta_vs_progetto"),
                percentuale_delta=entry.get("percentuale_delta"),
                note=entry.get("note"),
                matching_report=entry.get("matching_report"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)
            session.flush()
            original_id = entry.get("id")
            if original_id is not None:
                mappings["computo"][original_id] = record.id

        voci_computo_data = data.get("voci_computo") or []
        for entry in voci_computo_data:
            computo_id = mappings["computo"].get(entry.get("computo_id"))
            record = VoceComputo(
                commessa_id=commessa.id,
                commessa_code=commessa.codice,
                computo_id=computo_id,
                progressivo=entry.get("progressivo"),
                codice=entry.get("codice"),
                descrizione=entry.get("descrizione"),
                unita_misura=entry.get("unita_misura"),
                quantita=entry.get("quantita"),
                prezzo_unitario=entry.get("prezzo_unitario"),
                importo=entry.get("importo"),
                note=entry.get("note"),
                ordine=entry.get("ordine", 0),
                wbs_1_code=entry.get("wbs_1_code"),
                wbs_1_description=entry.get("wbs_1_description"),
                wbs_2_code=entry.get("wbs_2_code"),
                wbs_2_description=entry.get("wbs_2_description"),
                wbs_3_code=entry.get("wbs_3_code"),
                wbs_3_description=entry.get("wbs_3_description"),
                wbs_4_code=entry.get("wbs_4_code"),
                wbs_4_description=entry.get("wbs_4_description"),
                wbs_5_code=entry.get("wbs_5_code"),
                wbs_5_description=entry.get("wbs_5_description"),
                wbs_6_code=entry.get("wbs_6_code"),
                wbs_6_description=entry.get("wbs_6_description"),
                wbs_7_code=entry.get("wbs_7_code"),
                wbs_7_description=entry.get("wbs_7_description"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
                extra_metadata=entry.get("extra_metadata"),
                global_code=entry.get("global_code"),
            )
            session.add(record)

        if extracted_files.exists():
            for path in extracted_files.rglob("*"):
                if path.is_file():
                    dest = commessa_dir / path.relative_to(extracted_files)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, dest)

    def _restore_price_list(
        self,
        session: Session,
        commessa: Commessa,
        data: dict[str, Any],
        mappings: dict[str, dict[int, int]],
    ) -> None:
        items_data = data.get("price_list_items") or []
        commessa_tag = PriceCatalogService._build_commessa_tag(
            commessa.id,
            commessa.codice or "commessa",
        )
        for entry in items_data:
            saved_global_code = entry.get("global_code")
            if saved_global_code:
                global_code = saved_global_code
            else:
                global_code = PriceCatalogService._build_global_code(
                    commessa_tag,
                    entry.get("item_code", ""),
                    entry.get("product_id", ""),
                )
            record = PriceListItem(
                commessa_id=commessa.id,
                commessa_code=commessa.codice,
                product_id=entry.get("product_id"),
                global_code=global_code,
                item_code=entry.get("item_code"),
                item_description=entry.get("item_description"),
                unit_id=entry.get("unit_id"),
                unit_label=entry.get("unit_label"),
                wbs6_code=entry.get("wbs6_code"),
                wbs6_description=entry.get("wbs6_description"),
                wbs7_code=entry.get("wbs7_code"),
                wbs7_description=entry.get("wbs7_description"),
                price_lists=entry.get("price_lists"),
                extra_metadata=entry.get("extra_metadata"),
                source_file=entry.get("source_file"),
                preventivo_id=entry.get("preventivo_id"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)
            session.flush()
            if entry.get("id") is not None:
                mappings["price_list_item"][entry["id"]] = record.id

    def _restore_voci(
        self,
        session: Session,
        commessa: Commessa,
        data: dict[str, Any],
        mappings: dict[str, dict[int, int]],
    ) -> None:
        voci_data = data.get("voci") or []
        for entry in voci_data:
            wbs6_id = mappings["wbs6"].get(entry.get("wbs6_id"))
            wbs7_id = mappings["wbs7"].get(entry.get("wbs7_id"))
            price_list_item_id = mappings["price_list_item"].get(
                entry.get("price_list_item_id")
            )
            voce = VoceNorm(
                commessa_id=commessa.id,
                wbs6_id=wbs6_id,
                wbs7_id=wbs7_id,
                legacy_vocecomputo_id=None,
                codice=entry.get("codice"),
                descrizione=entry.get("descrizione"),
                unita_misura=entry.get("unita_misura"),
                note=entry.get("note"),
                ordine=entry.get("ordine", 0),
                price_list_item_id=price_list_item_id,
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(voce)
            session.flush()
            if entry.get("id") is not None:
                mappings["voce"][entry["id"]] = voce.id

        voce_progetto_data = data.get("voce_progetto") or []
        for entry in voce_progetto_data:
            voce_id = mappings["voce"].get(entry.get("voce_id"))
            computo_id = mappings["computo"].get(entry.get("computo_id"))
            record = VoceProgetto(
                voce_id=voce_id,
                computo_id=computo_id,
                quantita=entry.get("quantita"),
                prezzo_unitario=entry.get("prezzo_unitario"),
                importo=entry.get("importo"),
                note=entry.get("note"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)

    def _restore_offers(
        self,
        session: Session,
        commessa: Commessa,
        data: dict[str, Any],
        mappings: dict[str, dict[int, int]],
    ) -> None:
        offers_data = data.get("price_list_offers") or []
        for entry in offers_data:
            price_list_item_id = mappings["price_list_item"].get(entry.get("price_list_item_id"))
            computo_id = mappings["computo"].get(entry.get("computo_id"))
            impresa_id = mappings["impresa"].get(entry.get("impresa_id"))
            record = PriceListOffer(
                price_list_item_id=price_list_item_id,
                commessa_id=commessa.id,
                computo_id=computo_id,
                impresa_id=impresa_id,
                impresa_label=entry.get("impresa_label"),
                round_number=entry.get("round_number"),
                prezzo_unitario=entry.get("prezzo_unitario"),
                quantita=entry.get("quantita"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)

        voce_offerta_data = data.get("voce_offerta") or []
        for entry in voce_offerta_data:
            voce_id = mappings["voce"].get(entry.get("voce_id"))
            computo_id = mappings["computo"].get(entry.get("computo_id"))
            impresa_id = mappings["impresa"].get(entry.get("impresa_id"))
            record = VoceOfferta(
                voce_id=voce_id,
                computo_id=computo_id,
                impresa_id=impresa_id,
                round_number=entry.get("round_number"),
                quantita=entry.get("quantita"),
                prezzo_unitario=entry.get("prezzo_unitario"),
                importo=entry.get("importo"),
                note=entry.get("note"),
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)

    def _restore_import_configs(
        self, session: Session, commessa: Commessa, data: dict[str, Any]
    ) -> None:
        configs_data = data.get("import_configs") or []
        for entry in configs_data:
            record = ImportConfig(
                nome=entry.get("nome"),
                impresa=entry.get("impresa"),
                sheet_name=entry.get("sheet_name"),
                code_columns=entry.get("code_columns"),
                description_columns=entry.get("description_columns"),
                price_column=entry.get("price_column"),
                quantity_column=entry.get("quantity_column"),
                note=entry.get("note"),
                commessa_id=commessa.id,
                created_at=_parse_datetime(entry.get("created_at")),
                updated_at=_parse_datetime(entry.get("updated_at")),
            )
            session.add(record)

    def _restore_preferences(
        self, session: Session, commessa: Commessa, data: dict[str, Any]
    ) -> None:
        prefs = data.get("preferences")
        if not prefs:
            return
        record = CommessaPreferences(
            commessa_id=commessa.id,
            selected_preventivo_id=prefs.get("selected_preventivo_id"),
            selected_price_list_id=prefs.get("selected_price_list_id"),
            default_wbs_view=prefs.get("default_wbs_view"),
            custom_settings=prefs.get("custom_settings"),
            created_at=_parse_datetime(prefs.get("created_at")),
            updated_at=_parse_datetime(prefs.get("updated_at")),
        )
        session.add(record)


from .commesse import CommesseService


commessa_bundle_service = CommessaBundleService()

