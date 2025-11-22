from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unittest

from openpyxl import Workbook
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.db.models import Commessa, CommessaStato
from app.db.models_wbs import Wbs6, Wbs7, WbsSpaziale
from app.services.wbs_import import WbsImportService


def _build_sample_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    headers = [
        "WBS 1 - Lotto/Edificio",
        "Descrizione",
        "WBS 2 - Livelli",
        "Descrizione",
        "WBS 3 - Ambiti omogenei",
        "Descrizione",
        "WBS 4 - Appalto",
        "Descrizione",
        "WBS 5 - Elementi Funzionali",
        "Descrizione",
        "WBS 6 - Categorie merceologiche",
        "Descrizione",
        "Raggruppatore EPU",
        "Descrizione",
    ]
    sheet.append(headers)
    sheet.append(["Codice", "Descrizione"] * 7)
    sheet.append(
        [
            "A",
            "Edificio A",
            "P00",
            "Piano Terra",
            "UFF",
            "Uffici",
            "01",
            "Demolizioni",
            "1.1.1",
            "Struttura di fondazione",
            "A001",
            "Cantierizzazioni",
            "A001.010",
            "Noli",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class WbsImportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            commessa = Commessa(
                nome="Test",
                codice="TST01",
                stato=CommessaStato.setup,
            )
            session.add(commessa)
            session.commit()
            session.refresh(commessa)
            self.commessa_id = commessa.id

    def _run_import(self, mode: str):
        payload = _build_sample_workbook()
        with Session(self.engine) as session:
            commessa = SimpleNamespace(id=self.commessa_id)
            stats = WbsImportService.import_from_upload(
                session,
                commessa,
                file_bytes=payload,
                mode=mode,
            )
            spaziali = session.exec(select(WbsSpaziale)).all()
            wbs6_nodes = session.exec(select(Wbs6)).all()
            wbs7_nodes = session.exec(select(Wbs7)).all()
            snapshot = {
                "spaziali": len(spaziali),
                "wbs6": len(wbs6_nodes),
                "wbs7": len(wbs7_nodes),
            }
            return stats, snapshot

    def test_import_creates_wbs_nodes(self) -> None:
        stats, snapshot = self._run_import("create")
        self.assertEqual(stats.rows_total, 1)
        self.assertGreater(stats.spaziali_inserted + stats.spaziali_updated, 0)
        self.assertEqual(snapshot["spaziali"], 5)
        self.assertEqual(snapshot["wbs6"], 1)
        self.assertEqual(snapshot["wbs7"], 1)

    def test_update_mode_is_idempotent(self) -> None:
        stats_create, snapshot_create = self._run_import("create")
        self.assertEqual(stats_create.rows_total, 1)
        self.assertEqual(snapshot_create["spaziali"], 5)
        stats_update, snapshot_update = self._run_import("update")
        self.assertEqual(stats_update.rows_total, 1)
        self.assertEqual(snapshot_update["spaziali"], 5)
        self.assertEqual(snapshot_update["wbs6"], 1)
        self.assertEqual(snapshot_update["wbs7"], 1)


if __name__ == "__main__":
    unittest.main()
