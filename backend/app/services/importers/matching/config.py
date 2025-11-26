"""
Configurazione e costanti per il sistema di matching.
"""

# Semantic matching
SEMANTIC_MIN_SCORE = 0.58
"""Soglia minima di similarità semantica per considerare un match valido."""

SEMANTIC_DEFAULT_BUCKET = "__all__"
"""Bucket di default per embedding semantici."""

# Text processing
HEAD_TAIL_WORD_LIMIT = 30
"""Numero massimo di parole per le signature head/tail."""

# Jaccard similarity thresholds
JACCARD_MIN_THRESHOLD = 0.05
"""Soglia minima Jaccard per matching generico."""

JACCARD_PREFERENCE_THRESHOLD = 0.15
"""Soglia Jaccard per assegnare preferenze wrapper."""

JACCARD_PREFERENCE_DELTA = 0.01
"""Delta minimo tra best e second score per preferenze."""

# Description matching thresholds
DESCRIPTION_MIN_RATIO = 0.30
"""Soglia minima per matching basato su descrizione."""

# Token filtering
MIN_TOKEN_LENGTH = 4
"""Lunghezza minima token per indexing (esclusi progressivi)."""

MIN_TOKEN_LENGTH_DESCRIPTION = 6
"""Lunghezza minima token descrizione completa."""

MIN_WORD_TOKEN_LENGTH = 3
"""Lunghezza minima singola parola in descrizione."""

# Candidate limits
MAX_CANDIDATES_FILTER = 100
"""Numero massimo candidati da considerare nel pre-filtro."""

MAX_CANDIDATES_FINAL = 30
"""Numero massimo candidati per calcolo finale similarità."""

# Forced zero validation
FORCED_ZERO_CODE_PREFIXES = ("A004010",)
"""Prefissi codice che richiedono valori a zero."""

FORCED_ZERO_DESCRIPTION_KEYWORDS = (
    "mark up fee",
    "mark-up fee",
    "markup fee",
)
"""Keywords descrizione che richiedono valori a zero."""

# Stopwords (articoli, preposizioni, congiunzioni comuni)
STOPWORDS_IT = {
    "per", "con", "dei", "del", "dalla", "dallo", "dalle", "dagli",
    "alla", "allo", "alle", "agli", "nella", "nello", "nelle", "negli",
    "sulla", "sullo", "sulle", "sugli", "della", "dello", "delle", "degli",
    "una", "uno", "gli", "le", "il", "lo", "la", "di", "da", "in", "su",
    "a", "e", "o", "ma", "se", "che",
}
"""Stopwords italiane da ignorare nella tokenizzazione."""

STOPWORDS_EN = {
    "the", "of", "and", "or", "for", "with", "from", "to", "in", "on", "at", "by",
}
"""Stopwords inglesi da ignorare nella tokenizzazione."""

STOPWORDS = STOPWORDS_IT | STOPWORDS_EN
"""Set completo stopwords."""
