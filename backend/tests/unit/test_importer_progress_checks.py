from types import SimpleNamespace

from app.services.importers.matching.legacy import (
    _has_progressivi,
    _prices_match,
    _progress_price_key,
    _quantities_match,
)


def test_quantities_match_within_tolerance() -> None:
    assert _quantities_match(10.0, 10.00005)
    assert not _quantities_match(10.0, 10.1)


def test_prices_match_handles_small_deltas() -> None:
    assert _prices_match(55.0, 55.00005)
    assert not _prices_match(55.0, 55.5)


def test_progress_price_key_normalizes_code() -> None:
    voce = SimpleNamespace(progressivo=7, codice=" a001.02 ")
    # La funzione ora mantiene le lettere nella normalizzazione (A00102 invece di 00102)
    assert _progress_price_key(voce) == (7, "A00102")


def test_progress_price_key_requires_progressivo() -> None:
    voce = SimpleNamespace(progressivo=None, codice="B001")
    assert _progress_price_key(voce) is None


def test_has_progressivi_detects_entries() -> None:
    voci = [SimpleNamespace(progressivo=None), SimpleNamespace(progressivo=3)]
    assert _has_progressivi(voci)


def test_has_progressivi_returns_false_when_absent() -> None:
    voci = [SimpleNamespace(progressivo=None), SimpleNamespace(progressivo=None)]
    assert not _has_progressivi(voci)
