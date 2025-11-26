from __future__ import annotations

from app.services.importers.mc import McImportService
from app.services.importers.lc import LcImportService


class ImportService(McImportService, LcImportService):
    """Facade che espone le funzionalità di import MC e LC."""

    pass


import_service = ImportService()

__all__ = [
    "ImportService",
    "LcImportService",
    "McImportService",
    "import_service",
]
