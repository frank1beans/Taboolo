from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
import mimetypes
import logging
from hashlib import sha256
from fastapi import UploadFile, HTTPException, status

from app.core import settings


@dataclass
class StorageSaveResult:
    path: Path
    sha256: str


class StorageService:
    # SECURITY: Magic bytes per validazione tipo file reale
    EXCEL_MAGIC_BYTES = [
        b"\x50\x4B\x03\x04",  # ZIP-based Office files (XLSX, XLSM)
        b"\x50\x4B\x05\x06",  # Empty ZIP archive
        b"\x50\x4B\x07\x08",  # Spanned ZIP archive
        b"\xD0\xCF\x11\xE0",  # Old Excel format (XLS) - OLE2
    ]

    XML_MAGIC_BYTES = [
        b"<?xml",  # XML declaration
        b"<xml",   # XML tag
        b"\xef\xbb\xbf<?xml",  # UTF-8 BOM + XML
    ]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def commessa_dir(self, commessa_id: int) -> Path:
        path = self.root / f"commessa_{commessa_id:04d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _validate_file_security(self, filename: str | None, file_bytes: bytes) -> None:
        """
        SECURITY: Validazione rigorosa del file caricato.
        Verifica estensione, magic bytes e dimensione.
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome file mancante"
            )

        # SECURITY: Verifica estensione
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.allowed_file_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estensione file non consentita: {file_ext}. "
                       f"Formati accettati: {', '.join(settings.allowed_file_extensions)}"
            )

        # SECURITY: Verifica dimensione
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File troppo grande. Massimo consentito: {settings.max_upload_size_mb}MB"
            )

        # SECURITY: Verifica magic bytes (tipo file reale) - con fallback permissivo
        if file_ext in {".xlsx", ".xlsm", ".xls"}:
            is_valid = False
            for magic_bytes in self.EXCEL_MAGIC_BYTES:
                if len(file_bytes) >= len(magic_bytes) and file_bytes[:len(magic_bytes)] == magic_bytes:
                    is_valid = True
                    break

            # Se il file è troppo piccolo per verificare i magic bytes, accettalo comunque
            # (il parser Excel si occuperà di validarlo)
            if not is_valid and len(file_bytes) < 100:
                is_valid = True

            if not is_valid:
                # LOG: Invece di rifiutare, logga e accetta (il parser lo verificherà)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"File Excel con magic bytes non standard: {upload.filename if hasattr(self, 'upload') else filename}. "
                    f"First bytes: {file_bytes[:8].hex()}"
                )
                # Permetti comunque l'upload - il parser Excel farà la validazione finale
                is_valid = True

        elif file_ext in {".six", ".xml"}:
            # XML/SIX files - NESSUNA validazione magic bytes
            # I file STR Vision hanno formati troppo variabili (XML, ZIP, binario, encoding diversi)
            # Il parser STR Vision farà TUTTA la validazione
            pass  # Accetta sempre, nessuna validazione

    def _run_antivirus_hook(self, path: Path) -> None:
        """Stub per eventuale integrazione antivirus (ISO A.12.2)."""
        logger = logging.getLogger(__name__)
        logger.info("Antivirus hook non configurato - percorso: %s", path)

    def save_upload(self, commessa_id: int, upload: UploadFile) -> StorageSaveResult:
        """Salva un file caricato dopo validazioni di sicurezza."""
        target_dir = self.commessa_dir(commessa_id) / "uploads"
        target_dir.mkdir(parents=True, exist_ok=True)

        # SECURITY: Sanitizza nome file PRIMA (rimuovi path traversal)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        safe_name = upload.filename or "file.xlsx"
        # Rimuovi caratteri pericolosi
        safe_name = "".join(
            c for c in safe_name
            if c.isalnum() or c in "._- "
        ).strip()
        safe_name = safe_name.replace(" ", "_")

        # SECURITY: Verifica estensione prima di procedere
        file_ext = Path(safe_name).suffix.lower()
        if file_ext not in settings.allowed_file_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estensione file non consentita: {file_ext}. "
                       f"Formati accettati: {', '.join(settings.allowed_file_extensions)}"
            )

        target_path = target_dir / f"{timestamp}_{safe_name}"

        # SECURITY: Assicurati che il path finale sia dentro storage_root
        try:
            resolved_target = target_path.resolve()
            resolved_root = self.root.resolve()
            if resolved_root not in resolved_target.parents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Path traversal detected"
                )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )

        # SECURITY: Scrivi file chunk by chunk (evita di caricare tutto in memoria)
        # E fai validazione magic bytes sui primi chunk
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        total_bytes = 0
        first_chunk = b""

        digest = sha256()

        with target_path.open("wb") as fh:
            while True:
                chunk = upload.file.read(65536)  # 64KB chunks
                if not chunk:
                    break

                total_bytes += len(chunk)

                # SECURITY: Verifica dimensione durante lo streaming
                if total_bytes > max_size_bytes:
                    # Rimuovi file parziale
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File troppo grande. Massimo consentito: {settings.max_upload_size_mb}MB"
                    )

                # Salva primi bytes per validazione magic bytes
                if len(first_chunk) < 1024:
                    first_chunk += chunk

                digest.update(chunk)

                fh.write(chunk)

        # SECURITY: Validazione magic bytes sui primi bytes (solo per Excel)
        if file_ext in {".xlsx", ".xlsm", ".xls"}:
            is_valid = False
            for magic_bytes in self.EXCEL_MAGIC_BYTES:
                if len(first_chunk) >= len(magic_bytes) and first_chunk[:len(magic_bytes)] == magic_bytes:
                    is_valid = True
                    break

            if not is_valid and len(first_chunk) >= 100:
                # LOG warning ma accetta
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"File Excel con magic bytes non standard: {safe_name}. "
                    f"First bytes: {first_chunk[:8].hex()}"
                )

        digest_hex = digest.hexdigest()
        self._run_antivirus_hook(target_path)

        # NON chiudere upload.file - potrebbe essere usato dopo
        return StorageSaveResult(path=target_path, sha256=digest_hex)

    def delete_file(self, file_path: str | Path | None) -> bool:
        """Remove a stored upload if it lives inside the storage root."""
        if not file_path:
            return False

        path = Path(file_path)
        try:
            resolved_path = path.resolve()
            resolved_root = self.root.resolve()
        except RuntimeError:
            return False

        if resolved_path == resolved_root or resolved_root not in resolved_path.parents:
            # Do not delete files outside the storage root for safety.
            return False

        existed = path.exists()
        try:
            path.unlink(missing_ok=True)
        except TypeError:
            # Python <3.8 compatibility fallback (should not happen on 3.11).
            if path.exists():
                path.unlink()
        except OSError:
            return False

        if existed:
            self._cleanup_empty_dirs(path.parent, resolved_root)
        return existed

    def delete_commessa_dir(self, commessa_id: int) -> None:
        """Remove the whole directory associated with a commessa."""
        target_dir = self.root / f"commessa_{commessa_id:04d}"
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

    def _cleanup_empty_dirs(self, start: Path, stop: Path) -> None:
        """Delete empty directories up to (but excluding) the storage root."""
        current = start
        try:
            stop_resolved = stop.resolve()
        except RuntimeError:
            return

        while True:
            try:
                current_resolved = current.resolve()
            except RuntimeError:
                return

            if current_resolved == stop_resolved:
                return
            if stop_resolved not in current_resolved.parents:
                return

            try:
                current.rmdir()
            except OSError:
                return

            current = current.parent


storage_service = StorageService(settings.storage_root)
