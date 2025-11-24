from types import SimpleNamespace

from app.excel.parser import ParsedVoce
from app.services.importer import (
    _levenshtein_ratio,
    _match_by_description_similarity,
)


def _parsed_voce(description: str) -> ParsedVoce:
    return ParsedVoce(
        ordine=0,
        progressivo=None,
        codice=None,
        descrizione=description,
        wbs_levels=[],
        unita_misura=None,
        quantita=1.0,
        prezzo_unitario=100.0,
        importo=100.0,
        note=None,
        metadata=None,
    )


def test_levenshtein_ratio_identical_strings() -> None:
    assert _levenshtein_ratio("parete mobile vetro", "parete mobile vetro") == 1.0


def test_match_by_description_similarity_selects_closest_candidate() -> None:
    progetto = SimpleNamespace(
        descrizione="Fornitura e posa parete mobile in vetro altezza 270 cm"
    )
    candidate = _parsed_voce(
        "Fornitura e posa di parete mobile autoportante in vetro H.270 cm"
    )
    wrappers = [{"voce": candidate, "used": False, "matched": False, "tokens": set()}]
    matched = _match_by_description_similarity(progetto, wrappers, min_ratio=0.6)
    assert matched is wrappers[0]


def test_match_by_description_similarity_rejects_low_ratio() -> None:
    progetto = SimpleNamespace(
        descrizione="Fornitura e posa parete mobile in vetro altezza 270 cm"
    )
    candidate = _parsed_voce("Noleggio piattaforma e ponteggi")
    wrappers = [{"voce": candidate, "used": False, "matched": False, "tokens": set()}]
    assert _match_by_description_similarity(progetto, wrappers, min_ratio=0.8) is None
