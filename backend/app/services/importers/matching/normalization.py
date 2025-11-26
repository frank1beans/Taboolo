"""
Utilità di normalizzazione token e text processing per il matching.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Sequence

from app.db.models import VoceComputo
from app.excel import ParsedVoce, ParsedWbsLevel

from .config import (
    HEAD_TAIL_WORD_LIMIT,
    MIN_TOKEN_LENGTH_DESCRIPTION,
    MIN_WORD_TOKEN_LENGTH,
    STOPWORDS,
)


_WORD_TOKENIZER = re.compile(r"[A-Za-z0-9]+")


def normalize_token(value: str | None) -> str | None:
    """Normalizza un token generico rimuovendo accenti e caratteri non alfanumerici."""
    if not value:
        return None
    normalized = unicodedata.normalize("NFKD", str(value))
    cleaned = "".join(ch.lower() for ch in normalized if ch.isalnum())
    return cleaned or None


def normalize_code_token(code: str | None) -> str:
    """Normalizza un codice (solo maiuscole, no separatori)."""
    if not code:
        return ""
    normalized = str(code).upper()
    return re.sub(r"[^A-Z0-9]", "", normalized)


def normalize_description_token(text: str | None) -> str:
    """Normalizza una descrizione (lowercase, no accenti, spazi normalizzati)."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize_words(text: str) -> list[str]:
    """Tokenizza il testo in parole (solo alfanumerici)."""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    return _WORD_TOKENIZER.findall(normalized)


def extract_description_tokens(text: str | None) -> set[str]:
    """
    Estrae token da descrizione:
    - Testo completo normalizzato (se >= MIN_TOKEN_LENGTH_DESCRIPTION)
    - Righe separate normalizzate
    - Singole parole (escludendo stopwords)
    """
    if not text:
        return set()

    tokens: set[str] = set()
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Token intera descrizione + righe
    for segment in [normalized_text, *[part.strip() for part in normalized_text.split("\n") if part.strip()]]:
        token = normalize_token(segment)
        if token and len(token) >= MIN_TOKEN_LENGTH_DESCRIPTION:
            tokens.add(token)

    # Token singole parole (escl. stopwords)
    for word_token in re.split(r"[^A-Za-z0-9]+", text):
        if len(word_token) >= MIN_WORD_TOKEN_LENGTH and word_token.lower() not in STOPWORDS:
            tokens.add(word_token.lower())

    return tokens


def collect_code_tokens(code: str | None) -> set[str]:
    """
    Estrae token progressivi da codice:
    - Codice completo normalizzato
    - Prefissi progressivi (es: "ABC123" -> {"ABC123", "ABC", "ABCABC123"})
    """
    if not code:
        return set()

    normalized = normalize_token(code)
    tokens = set()
    if not normalized:
        return tokens

    tokens.add(normalized)

    # Genera prefissi progressivi
    segments = [segment for segment in re.split(r"[^A-Za-z0-9]+", code) if segment]
    builder = ""
    for segment in segments:
        cleaned = normalize_token(segment)
        if not cleaned:
            continue
        builder += cleaned
        tokens.add(builder)

    return tokens


def collect_description_tokens(text: str | None) -> set[str]:
    """
    Raccoglie token da descrizione per indexing:
    - Testo completo (se abbastanza lungo)
    - Singoli segmenti >= 4 caratteri
    """
    if not text:
        return set()

    tokens: set[str] = set()
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Token testo completo + righe
    for segment in [normalized_text, *[part.strip() for part in normalized_text.split("\n") if part.strip()]]:
        token = normalize_token(segment)
        if token and len(token) >= MIN_TOKEN_LENGTH_DESCRIPTION:
            tokens.add(token)

    # Token segmenti individuali
    for segment in re.split(r"[^A-Za-z0-9]+", text):
        token = normalize_token(segment)
        if token and len(token) >= 4:
            tokens.add(token)

    return tokens


def build_head_tail_signatures(
    description: str | None,
    limit: int = HEAD_TAIL_WORD_LIMIT,
) -> tuple[str, str]:
    """
    Costruisce signature head e tail dalla descrizione.
    Usate per matching fuzzy quando non c'è match esatto.
    """
    if not description:
        return "", ""

    tokens = tokenize_words(description)
    if not tokens:
        return "", ""

    head_tokens = tokens[:limit]
    tail_tokens = tokens[-limit:] if len(tokens) > limit else tokens
    return " ".join(head_tokens), " ".join(tail_tokens)


def build_description_signature(
    description: str | None,
    unit: str | None = None,
    wbs6_code: str | None = None,
) -> str | None:
    """
    Costruisce signature univoca da descrizione.
    Nota: unit e wbs6_code sono opzionali per retrocompatibilità,
    ma attualmente ci si basa solo sulla descrizione normalizzata.
    """
    token = normalize_description_token(description)
    if not token:
        return None
    return token


def build_description_signature_from_parsed(voce: ParsedVoce) -> str | None:
    """Costruisce signature da ParsedVoce."""
    wbs6_code = None
    for level in voce.wbs_levels:
        if level.level == 6:
            wbs6_code = level.code or level.description
            break
    return build_description_signature(voce.descrizione, voce.unita_misura, wbs6_code)


def build_description_signature_from_model(voce: VoceComputo) -> str | None:
    """Costruisce signature da VoceComputo."""
    return build_description_signature(voce.descrizione, voce.unita_misura, voce.wbs_6_code)


def build_wbs_key_from_model(voce: VoceComputo) -> str | None:
    """
    Costruisce chiave WBS da VoceComputo.
    Formato: "primary|secondary" dove:
    - primary: wbs_6 o wbs_5
    - secondary: wbs_7 o descrizione
    """
    primary = None
    for value in (
        voce.wbs_6_code,
        voce.wbs_6_description,
        voce.wbs_5_code,
        voce.wbs_5_description,
    ):
        token = normalize_token(value)
        if token:
            primary = token
            break

    secondary = None
    for value in (
        voce.wbs_7_code,
        voce.wbs_7_description,
        voce.descrizione,
    ):
        token = normalize_token(value)
        if token:
            secondary = token
            break

    if primary and secondary:
        return f"{primary}|{secondary}"
    return secondary or primary


def build_wbs_key_from_parsed(voce: ParsedVoce) -> str | None:
    """
    Costruisce chiave WBS completa da ParsedVoce.
    Formato: "primary|secondary|description"
    """
    primary = None
    secondary = None
    description_token = normalize_token(voce.descrizione)

    for livello in voce.wbs_levels:
        if livello.level == 6 and primary is None:
            primary = normalize_token(livello.code) or normalize_token(livello.description)
        if livello.level == 7 and secondary is None:
            secondary = normalize_token(livello.code) or normalize_token(livello.description)

    if secondary is None:
        secondary = normalize_token(voce.codice) or normalize_token(voce.descrizione)

    if primary and secondary:
        if description_token:
            return f"{primary}|{secondary}|{description_token}"
        return f"{primary}|{secondary}"

    if secondary and description_token and secondary != description_token:
        return f"{secondary}|{description_token}"

    return description_token or secondary or primary


def build_wbs_base_key_from_parsed(voce: ParsedVoce) -> str | None:
    """
    Costruisce chiave WBS base (senza descrizione) da ParsedVoce.
    Formato: "primary|secondary"
    """
    primary = None
    secondary = None

    for livello in voce.wbs_levels:
        if livello.level == 6 and primary is None:
            primary = normalize_token(livello.code) or normalize_token(livello.description)
        if livello.level == 7 and secondary is None:
            secondary = normalize_token(livello.code) or normalize_token(livello.description)

    if secondary is None:
        secondary = normalize_token(voce.codice) or normalize_token(voce.descrizione)

    if primary and secondary:
        return f"{primary}|{secondary}"
    return secondary or primary


def split_wbs_key(key: str | None) -> tuple[str | None, str | None]:
    """Splitta chiave WBS in (primary, secondary)."""
    if not key:
        return None, None
    if "|" in key:
        primary, secondary = key.split("|", 1)
        return (primary or None), (secondary or None)
    return None, key


def build_base_wbs_key_from_key(key: str | None) -> str | None:
    """
    Estrae la parte "base" di una chiave WBS (primary|secondary, senza description).
    """
    primary, secondary = split_wbs_key(key)
    if primary and secondary:
        if "|" in secondary:
            secondary = secondary.split("|", 1)[0]
        return f"{primary}|{secondary}"
    if primary:
        return primary
    return secondary


def append_token_to_list(target: list[str], value: str | None) -> None:
    """Aggiunge un token normalizzato alla lista (no duplicati)."""
    token = normalize_token(value)
    if token and token not in target:
        target.append(token)


def append_description_tokens_to_list(target: list[str], value: str | None) -> None:
    """
    Tokenizza descrizione e aggiunge alla lista:
    - Testo completo / righe
    - Singole parole (escl. stopwords)
    """
    if not value:
        return

    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    segments = [text]
    segments.extend(part.strip() for part in text.split("\n") if part.strip())

    for segment in segments:
        if not segment:
            continue
        # Token intera frase
        append_token_to_list(target, segment)

        # Token parola singola (escl. stopwords)
        words = [
            w for w in re.split(r"[^A-Za-z0-9]+", segment)
            if len(w) >= MIN_WORD_TOKEN_LENGTH and w.lower() not in STOPWORDS
        ]
        for word in words:
            append_token_to_list(target, word)


def build_keys_from_voce_progetto(voce: VoceComputo) -> list[str]:
    """
    Costruisce lista di chiavi di ricerca da VoceComputo per matching.
    Include: descrizioni, progressivo, codici WBS, codice voce.
    """
    keys: list[str] = []
    append_description_tokens_to_list(keys, voce.descrizione)

    if voce.progressivo is not None:
        append_token_to_list(keys, f"progressivo-{voce.progressivo}")

    # WBS descriptions (7 -> 1)
    for level in range(7, 0, -1):
        append_token_to_list(keys, getattr(voce, f"wbs_{level}_description", None))

    # WBS codes (7 -> 1)
    for level in range(7, 0, -1):
        append_token_to_list(keys, getattr(voce, f"wbs_{level}_code", None))

    append_token_to_list(keys, voce.codice)

    if voce.progressivo is not None:
        append_token_to_list(keys, f"progressivo-{voce.progressivo}")

    return keys


def build_keys_from_parsed_voce(voce: ParsedVoce) -> list[str]:
    """
    Costruisce lista di chiavi di ricerca da ParsedVoce per matching.
    Include: descrizioni, codice, livelli WBS, progressivo.
    """
    keys: list[str] = []
    append_description_tokens_to_list(keys, voce.descrizione)
    append_token_to_list(keys, voce.codice)

    for livello in voce.wbs_levels:
        append_token_to_list(keys, livello.description)
        append_token_to_list(keys, livello.code)

    if voce.progressivo is not None:
        append_token_to_list(keys, f"progressivo-{voce.progressivo}")

    return keys
