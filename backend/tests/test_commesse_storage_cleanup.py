from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import Commessa, CommessaStato, Computo, ComputoTipo
from app.services.commesse import CommesseService
from app.services.storage import storage_service


class CommesseStorageCleanupTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # Point the storage service to a temporary directory for each test.
        self._original_root = storage_service.root
        self._temp_dir = tempfile.TemporaryDirectory()
        storage_service.root = Path(self._temp_dir.name)
        storage_service.root.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)

        with Session(self.engine) as session:
            commessa = Commessa(
                nome="Test",
                codice="TEST",
                stato=CommessaStato.setup,
            )
            session.add(commessa)
            session.commit()
            session.refresh(commessa)
            self.commessa_id = commessa.id

    def tearDown(self) -> None:
        storage_service.root = self._original_root
        storage_service.root.mkdir(parents=True, exist_ok=True)
        self._temp_dir.cleanup()

    def _create_computo_with_file(self, session: Session, filename: str) -> tuple[Computo, Path]:
        uploads_dir = storage_service.commessa_dir(self.commessa_id) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        file_path = uploads_dir / filename
        file_path.write_text("dummy data", encoding="utf-8")

        computo = Computo(
            commessa_id=self.commessa_id,
            nome=filename,
            tipo=ComputoTipo.progetto,
            file_nome=filename,
            file_percorso=str(file_path),
        )
        session.add(computo)
        session.commit()
        session.refresh(computo)
        return computo, file_path

    def test_delete_computo_removes_uploaded_file(self) -> None:
        with Session(self.engine) as session:
            computo, file_path = self._create_computo_with_file(session, "computo.xlsx")

            deleted = CommesseService.delete_computo(session, self.commessa_id, computo.id)
            self.assertIsNotNone(deleted)
            self.assertFalse(file_path.exists(), "Uploaded file should be removed")
            self.assertIsNone(session.get(Computo, computo.id))

    def test_delete_commessa_clears_entire_commessa_folder(self) -> None:
        with Session(self.engine) as session:
            self._create_computo_with_file(session, "computo1.xlsx")
            self._create_computo_with_file(session, "computo2.xlsx")

            deleted = CommesseService.delete_commessa(session, self.commessa_id)
            self.assertIsNotNone(deleted)

            commessa_dir = storage_service.root / f"commessa_{self.commessa_id:04d}"
            self.assertFalse(commessa_dir.exists(), "Commessa storage directory should be deleted")


if __name__ == "__main__":
    unittest.main()
