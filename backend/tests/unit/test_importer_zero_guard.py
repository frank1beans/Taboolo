from __future__ import annotations

import unittest

from app.excel.parser import ParsedVoce
from app.services.importers.matching.legacy import _detect_forced_zero_violations


class ZeroGuardDetectionTestCase(unittest.TestCase):
    def _build_voce(
        self,
        *,
        codice: str | None,
        descrizione: str | None,
        quantita: float | None,
        prezzo: float | None,
        importo: float | None,
    ) -> ParsedVoce:
        return ParsedVoce(
            ordine=0,
            progressivo=None,
            codice=codice,
            descrizione=descrizione,
            wbs_levels=[],
            unita_misura="a corpo",
            quantita=quantita,
            prezzo_unitario=prezzo,
            importo=importo,
            note=None,
            metadata=None,
        )

    def test_detects_assistenze_quantity_mismatch(self) -> None:
        voce = self._build_voce(
            codice="A004.010.02",
            descrizione="Assistenze murarie alla posa impianti",
            quantita=1.0,
            prezzo=0.0,
            importo=0.0,
        )
        warnings = _detect_forced_zero_violations([voce])
        self.assertEqual(len(warnings), 1)
        self.assertIn("A004.010.02", warnings[0])
        self.assertIn("Q=1", warnings[0])

    def test_detects_mark_up_price(self) -> None:
        voce = self._build_voce(
            codice=None,
            descrizione="Mark up fee per le attività di coordinamento",
            quantita=0.0,
            prezzo=15.5,
            importo=15.5,
        )
        warnings = _detect_forced_zero_violations([voce])
        self.assertEqual(len(warnings), 1)
        self.assertIn("Mark up fee", warnings[0])
        self.assertIn("P=15.50", warnings[0])
        self.assertIn("I=15.50", warnings[0])

    def test_ignores_unrelated_voce(self) -> None:
        voce = self._build_voce(
            codice="B001.020.01",
            descrizione="Demolizione non protetta",
            quantita=2.5,
            prezzo=30.0,
            importo=75.0,
        )
        warnings = _detect_forced_zero_violations([voce])
        self.assertFalse(warnings)
