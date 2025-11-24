"""Canonicalise measurement units used in property extraction."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

__all__ = ["UnitMatch", "normalize_unit", "scan_units"]

_CANONICAL_UNITS = {
    "mm": {
        "mm",
        "millimetro",
        "millimetri",
        "millimeter",
        "millimeters",
        "㎜",
    },
    "cm": {
        "cm",
        "centimetro",
        "centimetri",
        "㎝",
    },
    "m": {
        "m",
        "metro",
        "metri",
    },
    "kg/m": {
        "kg/m",
        "kgm",
        "kg / m",
    },
    "m2": {
        "m2",
        "m^2",
        "m²",
        "mq",
        "metroquadro",
        "metriquadrati",
        "metri_quadrati",
        "metri quadrati",
        "metri quadri",
        "metri quad.",
    },
    "m3": {
        "m3",
        "m^3",
        "m³",
        "mc",
        "metricubi",
        "metri_cubi",
        "metri cubi",
    },
    "kn/m2": {
        "kn/m2",
        "kn/mq",
        "knm2",
        "knmq",
        "knm^2",
        "kn/m²",
        "kilonewton/m2",
        "kilonewton/mq",
    },
    "kg/m3": {
        "kg/m3",
        "kg/m^3",
        "kg/m³",
        "kgm3",
        "kgm^3",
        "kgm³",
        "kg/mc",
        "kgmc",
    },
    "kg/m2": {
        "kg/m2",
        "kg/mq",
        "kgm2",
        "kgmq",
        "kg/m²",
    },
    "w/m2k": {
        "w/m2k",
        "w/m²k",
        "w / m2k",
        "w / m²k",
        "w m2 k",
        "w m² k",
    },
    "w/mk": {
        "w/mk",
        "w / mk",
        "w m k",
        "lambda",
        "λ",
    },
    "l/min": {
        "l/min",
        "l / min",
        "lmin",
        "litri/min",
        "litro/min",
    },
    "%": {
        "%",
        "percento",
        "percentuale",
    },
    "db": {
        "db",
        "dB",
        "decibel",
    },
}

_SUPERSCRIPTS = str.maketrans({"²": "2", "³": "3", "㎜": "mm", "㎝": "cm"})


def _normalize_token(token: str) -> str:
    """Lowercase token and strip spaces/underscores/dots after unrolling superscripts."""
    cleaned = token.translate(_SUPERSCRIPTS).lower()
    cleaned = cleaned.replace("/ ", "/").replace(" /", "/")
    cleaned = re.sub(r"[\s_.]+", "", cleaned)
    return cleaned


_NORMALIZED_ALIASES = {
    canonical: {_normalize_token(alias) for alias in aliases}
    for canonical, aliases in _CANONICAL_UNITS.items()
}


def _alias_to_regex(alias: str) -> str:
    """
    Build a regex that matches the alias allowing optional whitespace around slashes
    and treating underscores as optional separators.
    """
    escaped = re.escape(alias.strip())
    escaped = escaped.replace(r"\ ", r"\s*")
    escaped = escaped.replace(r"\_", r"[_\s]*")
    escaped = re.sub(r"\\/", r"\\s*/\\s*", escaped)
    return escaped


def _build_unit_pattern() -> re.Pattern[str]:
    variants: set[str] = set()
    for aliases in _CANONICAL_UNITS.values():
        for alias in aliases:
            variants.add(_alias_to_regex(alias))
    pattern_body = "|".join(sorted(variants, key=len, reverse=True))
    # Avoid matching inside longer alphabetic/numeric tokens but allow adjacency to numbers on the left.
    return re.compile(rf"(?<![A-Za-z])(?:{pattern_body})(?![A-Za-z0-9^])", flags=re.IGNORECASE)


_UNIT_PATTERN = _build_unit_pattern()


def normalize_unit(token: Optional[str]) -> Optional[str]:
    """Return the canonical representation of ``token`` if recognised."""

    if token is None:
        return None
    cleaned = _normalize_token(token)
    for canonical, aliases in _NORMALIZED_ALIASES.items():
        if cleaned in aliases:
            return canonical
    return None


@dataclass(frozen=True)
class UnitMatch:
    """Unit mention located in text."""

    unit: str
    raw: str
    start: int
    end: int


def _iter_unit_tokens(text: str) -> Iterator[re.Match[str]]:
    for match in _UNIT_PATTERN.finditer(text):
        yield match


def scan_units(text: str) -> Iterable[UnitMatch]:
    """Find and normalise measurement units inside ``text``."""

    for match in _iter_unit_tokens(text):
        raw = match.group(0)
        unit = normalize_unit(raw)
        if unit:
            yield UnitMatch(unit=unit, raw=raw, start=match.start(), end=match.end())
