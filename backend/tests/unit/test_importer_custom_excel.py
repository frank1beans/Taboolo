from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl import Workbook

from app.services.importer import _parse_custom_return_excel


def test_parse_custom_return_excel_builds_parsed_voci() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Offerta"
    sheet.append(["Codice", "Descrizione", "Prezzo"])
    sheet.append(["A001", "Voce A", 12.5])
    sheet.append(["A002", "Voce B", "13,00"])

    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        temp_path = Path(tmp.name)
    try:
        workbook.save(temp_path)
        workbook.close()
        result = _parse_custom_return_excel(
            temp_path,
            "Offerta",
            ["A"],
            ["B"],
            "C",
        )

        computo = result.computo
        assert len(computo.voci) == 2
        first, second = computo.voci
        assert first.codice == "A001"
        assert first.descrizione == "Voce A"
        assert first.prezzo_unitario == 12.5
        assert second.codice == "A002"
        assert second.prezzo_unitario == 13.0
    finally:
        if temp_path.exists():
            temp_path.unlink()
