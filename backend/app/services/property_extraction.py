from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict
from datetime import datetime, timedelta

from sqlmodel import Session, select

try:  # Best-effort engine import; optional in tests
    from app.db.session import engine
    from app.db.models import PropertyLexicon, PropertyPattern, PropertyOverride
except Exception:  # pragma: no cover - optional import
    engine = None
    PropertyLexicon = None  # type: ignore
    PropertyPattern = None  # type: ignore
    PropertyOverride = None  # type: ignore

try:  # Lazy optional import: the app still works if the package is missing
    from sentence_transformers import SentenceTransformer, util
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore
    util = None  # type: ignore


Unit = Literal["mm", "cm", "m", "w_m2k", "db", "l_min"]


@dataclass
class NumberWithUnit:
    value: float
    unit: Unit
    raw: str
    context: str


@dataclass
class ClassMatch:
    kind: Literal["classe_ei", "reazione_fuoco", "pei", "r_scivolosita"]
    value: str
    raw: str
    context: str


@dataclass
class BrandMatch:
    value: str
    raw: str
    context: str


@dataclass
class NormativaMatch:
    value: str
    raw: str
    context: str


@dataclass
class MaterialKeyword:
    value: str
    raw: str
    context: str


@dataclass
class BaseFeatures:
    numbers: List[NumberWithUnit]
    classes: List[ClassMatch]
    brands: List[BrandMatch]
    normative: List[NormativaMatch]
    materials: List[MaterialKeyword]


class ExtractedProperties(TypedDict):
    category_id: str
    properties: Dict[str, Any]
    missing_required: List[str]


class CategorySchema(TypedDict, total=False):
    id: str
    name: str
    required: List[str]
    properties: List[Dict[str, Any]]


_THIS_FILE = Path(__file__).resolve()
ROOT_DIR = _THIS_FILE.parents[3]
SCHEMA_PATH = ROOT_DIR / "public" / "property-schemas.json"

MODEL_NAME = os.getenv(
    "PROPERTY_EMBEDDINGS_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDINGS_DISABLED = os.getenv("PROPERTY_EMBEDDINGS_DISABLE", "0") == "1"

st_model: SentenceTransformer | None = None


CATEGORY_REQUIRED: dict[str, list[str]] = {
    "opere_da_cartongessista": ["stratigrafia_lastre"],
    "opere_di_rivestimento": ["materiale", "spessore_mm", "posa"],
    "opere_di_pavimentazione": ["materiale", "formato", "spessore_mm"],
    "opere_da_serramentista": ["dimensione_larghezza", "dimensione_altezza", "trasmittanza_termica"],
    "controsoffitti": ["materiale", "spessore_pannello_mm", "coefficiente_fonoassorbimento"],
    "apparecchi_sanitari_accessori": ["materiale"],
    "opere_da_falegname": ["essenza", "dimensione_larghezza", "dimensione_altezza"],
}


# --------- Text helpers ---------


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text
    normalized = re.sub(r"(?<=\d),(?=\d)", ".", normalized)
    normalized = normalized.replace("mm.", "mm").replace("cm.", "cm").replace("m.", "m")
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def _normalize_for_match(value: str) -> str:
    value = _strip_accents(value.lower())
    return re.sub(r"[^a-z0-9]+", "", value)


def _context_window(text: str, start: int, end: int, radius: int = 50) -> str:
    left = max(start - radius, 0)
    right = min(end + radius, len(text))
    return text[left:right].strip()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache()
def load_category_schema() -> Dict[str, CategorySchema]:
    data = _load_json(SCHEMA_PATH)
    categories = data.get("categories") or []
    return {cat["id"]: cat for cat in categories if "id" in cat}


def _refresh_lexicon_cache(session: Session | None = None) -> None:
    global _LEXICON_CACHE
    if not engine or PropertyLexicon is None:
        _LEXICON_CACHE = {}
        return
    now = datetime.utcnow()
    sess = session or Session(engine)
    try:
        entries = sess.exec(select(PropertyLexicon).where(PropertyLexicon.active == True)).all()  # noqa: E712
        buckets: dict[str, list[dict[str, Any]]] = {}
        for e in entries:
            buckets.setdefault(e.type, []).append(
                {
                    "canonical": e.canonical,
                    "synonyms": e.synonyms or [],
                    "categories": e.categories or [],
                    "details": e.details or {},
                }
            )
        _LEXICON_CACHE = {k: (now, v) for k, v in buckets.items()}
    finally:
        if session is None:
            sess.close()


def _get_lexicon(type_name: str, session: Session | None = None) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    cache = _LEXICON_CACHE.get(type_name)
    if cache and now - cache[0] < _CACHE_TTL:
        return cache[1]
    _refresh_lexicon_cache(session)
    cache = _LEXICON_CACHE.get(type_name)
    return cache[1] if cache else []


def _dynamic_brand_synonyms(session: Session | None = None) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for entry in _get_lexicon("brand", session):
        canonical = entry["canonical"]
        variants = set(entry.get("synonyms") or [])
        variants.add(canonical)
        mapping[canonical] = list(variants)
    return mapping


def _dynamic_material_synonyms(session: Session | None = None) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for entry in _get_lexicon("material", session):
        canonical = entry["canonical"]
        variants = set(entry.get("synonyms") or [])
        variants.add(canonical)
        mapping[canonical] = list(variants)
    return mapping


def _refresh_pattern_cache(session: Session | None = None) -> None:
    global _PATTERN_CACHE
    if not engine or PropertyPattern is None:
        _PATTERN_CACHE = None
        return
    now = datetime.utcnow()
    sess = session or Session(engine)
    try:
        entries = sess.exec(select(PropertyPattern).where(PropertyPattern.active == True)).all()  # noqa: E712
        data = []
        for e in entries:
            data.append(
                {
                    "id": e.id,
                    "category_id": e.category_id,
                    "property_id": e.property_id,
                    "pattern": e.pattern,
                    "context_keywords": e.context_keywords or [],
                    "priority": e.priority,
                }
            )
        _PATTERN_CACHE = (now, data)
    finally:
        if session is None:
            sess.close()


def _get_patterns(session: Session | None = None) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    if _PATTERN_CACHE and now - _PATTERN_CACHE[0] < _CACHE_TTL:
        return _PATTERN_CACHE[1]
    _refresh_pattern_cache(session)
    return _PATTERN_CACHE[1] if _PATTERN_CACHE else []


# --------- Feature extraction ---------


BRAND_SYNONYMS: dict[str, list[str]] = {
    "knauf": ["knauf"],
    "gyproc": ["gyproc"],
    "siniat": ["siniat"],
    "fassa": ["fassa"],
    "schuco": ["schuco", "schüco", "schueco"],
    "geberit": ["geberit"],
    "ideal standard": ["ideal standard", "idealstandard"],
    "hilti": ["hilti"],
    "saint-gobain": ["saint-gobain", "saint gobain"],
}


MATERIAL_SYNONYMS: dict[str, list[str]] = {
    "cartongesso": ["cartongesso", "plasterboard", "drywall", "gypsum"],
    "lana_minerale": ["lana minerale", "rockwool", "lana di roccia", "lana di vetro", "mineral wool"],
    "fibra_minerale": ["fibra minerale", "mineral fiber"],
    "acciaio": ["acciaio", "steel"],
    "alluminio": ["alluminio", "aluminium", "alu"],
    "legno": ["legno", "wood", "parquet"],
    "pvc": ["pvc", "vinile", "vinyl"],
    "legno_alluminio": ["legno alluminio", "legno-alluminio", "wood aluminium", "wood-aluminium"],
    "gres": ["gres", "porcelain stoneware", "porcelain", "stoneware", "porcellanato"],
    "pietra": ["pietra", "marmo", "granito", "ardesia", "stone"],
    "ceramica": ["ceramica", "ceramic"],
    "resina": ["resina", "resin"],
    "intonaco": ["intonaco", "plaster"],
    "laminato": ["laminato", "laminate"],
    "metallo": ["metallo", "metal"],
    "pietra_naturale": ["pietra naturale", "natural stone"],
    "calcestruzzo": ["calcestruzzo", "cemento", "concrete"],
    "vinilico": ["vinilico", "vinyl"],
    "acciaio_inox": ["acciaio inox", "stainless steel", "inox"],
    "ghisa": ["ghisa", "cast iron"],
    "porcellana": ["porcellana", "porcelain"],
    "plastica": ["plastica", "plastic", "abs"],
    "vetro": ["vetro", "glass"],
    "rovere": ["rovere", "oak"],
    "faggio": ["faggio", "beech"],
    "pino": ["pino", "pine"],
    "abete": ["abete", "fir", "spruce"],
    "larice": ["larice", "larch"],
    "noce": ["noce", "walnut"],
    "castagno": ["castagno", "chestnut"],
}


INSULATION_KEYWORDS = [
    "isolante",
    "isolamento",
    "coibent",
    "lana di roccia",
    "lana di vetro",
    "lana minerale",
    "xps",
    "eps",
    "polistirene",
    "poliuretano",
    "fibra di legno",
]

# Cache dinamici (TTL 5 minuti) per dizionari e pattern da DB
_LEXICON_CACHE: dict[str, tuple[datetime, list[dict[str, Any]]]] = {}
_PATTERN_CACHE: tuple[datetime, list[dict[str, Any]]] | None = None
_CACHE_TTL = timedelta(minutes=5)


def _normalize_unit(unit_raw: str) -> Unit | None:
    token = unit_raw.lower().replace(" ", "")
    if token.startswith("mm"):
        return "mm"
    if token.startswith("cm"):
        return "cm"
    if token in {"m", "mt"}:
        return "m"
    if "w/m2k" in token or "w/m²k" in token or "w/mk" in token:
        return "w_m2k"
    if "db" in token:
        return "db"
    if token.replace(" ", "") in {"l/min", "l/ min", "l/"} or "l/min" in token:
        return "l_min"
    if "lmin" in token:
        return "l_min"
    return None


NUMBER_PATTERN = re.compile(
    r"(?P<value>\d+(?:[.,]\d+)?)(?:\s*(?P<unit>mm|cm|m|w\s*/?\s*m2k|w\s*/?\s*m²k|w\s*/?\s*mk|db|d\s*b|l\s*/\s*min|l/min|lmin))",
    flags=re.IGNORECASE,
)


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value.replace(",", "."))
    except Exception:
        return None


def extract_numbers(text: str) -> List[NumberWithUnit]:
    numbers: List[NumberWithUnit] = []
    for match in NUMBER_PATTERN.finditer(text):
        raw_value = match.group("value")
        unit_raw = match.group("unit") or ""
        value = _parse_float(raw_value)
        unit = _normalize_unit(unit_raw)
        if value is None or unit is None:
            continue
        ctx = _context_window(text, match.start(), match.end())
        numbers.append(NumberWithUnit(value=value, unit=unit, raw=match.group(0), context=ctx))
    return numbers


FIRE_CLASS_REGEX = re.compile(
    r"\b(a1|a2\s*[-/]?\s*s[12]\s*[,/ ]?\s*d0|b\s*[-/]?\s*s[12]\s*[,/ ]?\s*d0)\b",
    flags=re.IGNORECASE,
)
EI_REGEX = re.compile(r"\bei\s*-?\s*(30|45|60|90|120|180)\b", flags=re.IGNORECASE)
PEI_REGEX = re.compile(r"\bpei\s*(i{1,3}|iv|v|1|2|3|4|5)\b", flags=re.IGNORECASE)
R_SCIVOLOSITA_REGEX = re.compile(r"\br\s*(9|10|11|12|13)\b", flags=re.IGNORECASE)


def _canonical_fire(raw: str) -> Optional[str]:
    token = _normalize_for_match(raw)
    mapping = {
        "a1": "A1",
        "a2s1d0": "A2-s1,d0",
        "a2s2d0": "A2-s2,d0",
        "bs1d0": "B-s1,d0",
        "bs2d0": "B-s2,d0",
    }
    return mapping.get(token)


def extract_classes(text: str) -> List[ClassMatch]:
    classes: List[ClassMatch] = []
    for match in EI_REGEX.finditer(text):
        val = f"EI{match.group(1)}"
        classes.append(ClassMatch(kind="classe_ei", value=val, raw=match.group(0), context=_context_window(text, match.start(), match.end())))

    for match in FIRE_CLASS_REGEX.finditer(text):
        canonical = _canonical_fire(match.group(0))
        if canonical:
            classes.append(
                ClassMatch(
                    kind="reazione_fuoco",
                    value=canonical,
                    raw=match.group(0),
                    context=_context_window(text, match.start(), match.end()),
                )
            )

    for match in PEI_REGEX.finditer(text):
        val_raw = match.group(1).upper()
        roman = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
        val_norm = roman.get(val_raw, val_raw)
        classes.append(
            ClassMatch(
                kind="pei",
                value=f"PEI {val_norm}",
                raw=match.group(0),
                context=_context_window(text, match.start(), match.end()),
            )
        )

    for match in R_SCIVOLOSITA_REGEX.finditer(text):
        cls_val = f"R{match.group(1)}"
        classes.append(
            ClassMatch(
                kind="r_scivolosita",
                value=cls_val,
                raw=match.group(0),
                context=_context_window(text, match.start(), match.end()),
            )
        )
    return classes


def extract_brands(text: str) -> List[BrandMatch]:
    matches: List[BrandMatch] = []
    lowered = text.lower()
    mappings = [BRAND_SYNONYMS]
    dynamic = _dynamic_brand_synonyms()
    if dynamic:
        mappings.append(dynamic)

    for mapping in mappings:
        for canonical, variants in mapping.items():
            for variant in variants:
                for m in re.finditer(rf"\b{re.escape(variant.lower())}\b", lowered):
                    matches.append(
                        BrandMatch(
                            value=canonical,
                            raw=text[m.start() : m.end()],
                            context=_context_window(text, m.start(), m.end()),
                        )
                    )
    return matches


def extract_normative(text: str) -> List[NormativaMatch]:
    patterns = [
        r"\b(?:uni[\s-]*en|uni|en|din|iso)\s*[a-z]*\s*\d{3,5}(?:[-/]\d+)?(?:[:/]\d{2,4})?",
        r"\bregolamento\s+\d{3,4}/\d{4}\b",
        r"\bd\.?\s*lgs\.?\s*\d+[/-]?\d*\b",
        r"\bcp[rR]\b\s*\d{3,4}/\d{4}",
    ]
    matches: List[NormativaMatch] = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            raw = m.group(0)
            matches.append(
                NormativaMatch(value=raw.strip(), raw=raw, context=_context_window(text, m.start(), m.end()))
            )
    return matches


def extract_materials(text: str) -> List[MaterialKeyword]:
    matches: List[MaterialKeyword] = []
    lowered = text.lower()
    seen_positions: set[Tuple[int, int, str]] = set()

    def _scan(mapping: dict[str, list[str]]) -> None:
        for canonical, variants in mapping.items():
            for variant in variants:
                for m in re.finditer(re.escape(variant.lower()), lowered):
                    key = (m.start(), m.end(), canonical)
                    if key in seen_positions:
                        continue
                    seen_positions.add(key)
                    matches.append(
                        MaterialKeyword(
                            value=canonical,
                            raw=text[m.start() : m.end()],
                            context=_context_window(text, m.start(), m.end()),
                        )
                    )

    _scan(MATERIAL_SYNONYMS)
    dynamic = _dynamic_material_synonyms()
    if dynamic:
        _scan(dynamic)
    return matches


def extract_base_features(text: str) -> BaseFeatures:
    return BaseFeatures(
        numbers=extract_numbers(text),
        classes=extract_classes(text),
        brands=extract_brands(text),
        normative=extract_normative(text),
        materials=extract_materials(text),
    )


# --------- Embedding resolver ---------
PROPERTY_PROTOTYPES: dict[tuple[str, str], list[str]] = {
    ("controsoffitti", "materiale"): [
        "materiale del pannello del controsoffitto",
        "materiale delle lastre del controsoffitto",
    ],
    ("controsoffitti", "spessore_pannello_mm"): [
        "spessore in millimetri del pannello del controsoffitto",
        "spessore delle lastre del controsoffitto",
    ],
    ("opere_da_cartongessista", "stratigrafia_lastre"): [
        "stratigrafia delle lastre in cartongesso",
        "descrizione delle lastre che compongono la parete in cartongesso",
    ],
    ("opere_di_rivestimento", "materiale"): [
        "materiale del rivestimento",
        "materiale principale applicato come rivestimento",
    ],
    ("opere_di_rivestimento", "spessore_mm"): [
        "spessore in millimetri del rivestimento",
        "spessore delle piastrelle o pannelli di rivestimento",
    ],
    ("opere_di_pavimentazione", "materiale"): [
        "materiale principale della pavimentazione",
        "materiale del pavimento",
    ],
    ("opere_di_pavimentazione", "formato"): [
        "formato delle piastrelle o doghe del pavimento",
        "dimensioni nominali degli elementi del pavimento",
    ],
    ("opere_di_pavimentazione", "spessore_mm"): [
        "spessore in millimetri del pavimento o della piastrella",
        "spessore degli elementi della pavimentazione",
    ],
    ("opere_da_serramentista", "materiale_struttura"): [
        "materiale del telaio del serramento",
        "materiale della struttura del serramento",
    ],
    ("apparecchi_sanitari_accessori", "materiale"): [
        "materiale del sanitario o accessorio",
        "materiale principale dell'apparecchio sanitario",
    ],
    ("opere_da_falegname", "essenza"): [
        "essenza del legno utilizzata",
        "tipo di legno impiegato",
    ],
}

PROPERTY_PROTOTYPE_EMB: dict[tuple[str, str], Any] = {}


class EmbeddingResolver:
    def __init__(self, model: SentenceTransformer | None):
        self.model = model

    def is_enabled(self) -> bool:
        return self.model is not None and not EMBEDDINGS_DISABLED

    def resolve(
        self,
        category_id: str,
        property_id: str,
        candidates: List[Tuple[str, str]],
        threshold: float = 0.4,
    ) -> Optional[str]:
        if not candidates:
            return None
        if not self.is_enabled():
            return candidates[0][0]

        key = (category_id, property_id)
        proto_emb = PROPERTY_PROTOTYPE_EMB.get(key)
        if proto_emb is None:
            return candidates[0][0]

        candidate_texts = [f"Valore: {value}. Contesto: {ctx}" for value, ctx in candidates]
        cand_emb = self.model.encode(candidate_texts, normalize_embeddings=True)
        sims = util.cos_sim(cand_emb, proto_emb)
        best_scores = sims.max(dim=1).values
        best_idx = int(best_scores.argmax())
        best_score = float(best_scores[best_idx])
        if best_score < threshold:
            return None
        return candidates[best_idx][0]


def _build_resolver(model: SentenceTransformer | None) -> EmbeddingResolver:
    return EmbeddingResolver(model)


resolver = EmbeddingResolver(None)


def init_model() -> None:
    global st_model, resolver
    if EMBEDDINGS_DISABLED or SentenceTransformer is None:
        st_model = None
        resolver = _build_resolver(None)
        return
    if st_model is None:
        st_model = SentenceTransformer(MODEL_NAME)
    resolver = _build_resolver(st_model)


def init_property_prototypes() -> None:
    if EMBEDDINGS_DISABLED or st_model is None:
        return
    for key, texts in PROPERTY_PROTOTYPES.items():
        PROPERTY_PROTOTYPE_EMB[key] = st_model.encode(texts, normalize_embeddings=True)


# --------- Utility mappers ---------
def _to_mm(value: float, unit: Unit) -> float:
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10
    if unit == "m":
        return value * 1000
    return value


def _first_class_by_kind(classes: List[ClassMatch], kind: str) -> Optional[str]:
    for cls in classes:
        if cls.kind == kind:
            return cls.value
    return None


def _join_normative(feats: BaseFeatures) -> Optional[str]:
    if not feats.normative:
        return None
    values: list[str] = []
    seen: set[str] = set()
    for n in feats.normative:
        if n.value not in seen:
            values.append(n.value)
            seen.add(n.value)
    return "; ".join(values)


def _extract_stratigrafia(original_text: str) -> Optional[str]:
    """
    Estrae frasi che descrivono lastre/pannelli/orditura (cartongesso, controsoffitti).
    Split primario su ; / newline / bullet, fallback a punti e match inline.
    """
    if not original_text:
        return None
    key_re = re.compile(r"(lastr|pannell|cartongesso|plasterboard|orditura|isolant)", flags=re.IGNORECASE)
    max_len = 320  # evita di prendere l'intera descrizione

    def _add_unique(seq: list[str], value: str) -> None:
        if value not in seq:
            seq.append(value)

    hits: List[str] = []

    # Priorità: linee bullet/spacchettate che contengono keyword
    bullet_lines: list[str] = []
    for raw_line in re.split(r"[\n\r]+", original_text):
        line = raw_line.strip(" -•\t")
        if not line:
            continue
        if key_re.search(line):
            bullet_lines.append(line)

    # Se abbiamo linee bullet, usiamo solo quelle
    if bullet_lines:
        for line in bullet_lines:
            if len(line) <= max_len or line.lower().lstrip().startswith(
                ("lastra", "idrolastra", "pannello", "cartongesso", "orditura", "isolante")
            ):
                _add_unique(hits, line)
    else:
        # Split su vari separatori
        chunks = re.split(r"[;\n\r•]+", original_text)
        if len(chunks) <= 1:
            chunks = re.split(r"[.]", original_text)
        # supporto per bullet con trattino "- "
        for line in re.split(r"[\n\r]+", original_text):
            for part in re.split(r"^\s*-\s+", line.strip()):
                if part:
                    chunks.append(part)
        # split aggiuntivo su ":" per estrarre liste dopo descrizioni lunghe
        more_chunks: list[str] = []
        for c in chunks:
            more_chunks.extend(re.split(r":", c))
        if more_chunks:
            chunks.extend(more_chunks)

        for chunk in chunks:
            part = chunk.strip(" -•")
            if not part:
                continue
            if key_re.search(part):
                if len(part) <= max_len or part.lower().lstrip().startswith(
                    ("lastra", "idrolastra", "pannello", "cartongesso", "orditura", "isolante")
                ):
                    _add_unique(hits, part.strip())

    # Fallback: cattura span inline tra separatori se nulla trovato
    if not hits:
        for m in re.finditer(
            r"[^;.\n\r•]*?(lastr|pannell|cartongesso|plasterboard|orditura|isolant)[^;.\n\r•]*",
            original_text,
            flags=re.IGNORECASE,
        ):
            span = m.group(0).strip(" ;\n\r•-.")
            if span and len(span) <= max_len:
                _add_unique(hits, span)

    if not hits:
        return None
    return "; ".join(hits)


def _extract_ral(text: str) -> Optional[str]:
    m = re.search(r"\bral\s*([0-9]{3,4})\b", text, flags=re.IGNORECASE)
    if not m:
        return None
    return f"RAL {m.group(1)}"


def _extract_fonoassorbimento(text_norm: str) -> Optional[float]:
    m = re.search(
        r"(?:αw|aw|alpha w|fonoassorbimento|coefficiente)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)",
        text_norm,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return float(m.group(1))


def _dimension_pair_from_text(text: str) -> Tuple[Optional[float], Optional[float]]:
    norm = normalize_text(text)
    m = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(mm|cm|m))?",
        norm,
        flags=re.IGNORECASE,
    )
    if m:
        unit = m.group(3) or "mm"
        w = _to_mm(float(m.group(1)), _normalize_unit(unit) or "mm")
        h = _to_mm(float(m.group(2)), _normalize_unit(unit) or "mm")
        return w, h
    for label in ("larghezza", "luce", "l"):
        m_width = re.search(rf"{label}\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|m)", norm)
        if m_width:
            w = _to_mm(float(m_width.group(1)), _normalize_unit(m_width.group(2)) or "mm")
            break
    else:
        w = None
    for label in ("altezza", "h"):
        m_height = re.search(rf"{label}\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|m)", norm)
        if m_height:
            h = _to_mm(float(m_height.group(1)), _normalize_unit(m_height.group(2)) or "mm")
            break
    else:
        h = None
    return w, h


def _dimension_triplet_from_text(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    norm = normalize_text(text)
    m = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(mm|cm|m))?",
        norm,
        flags=re.IGNORECASE,
    )
    if m:
        unit = m.group(4) or "mm"
        l = _to_mm(float(m.group(1)), _normalize_unit(unit) or "mm")
        w = _to_mm(float(m.group(2)), _normalize_unit(unit) or "mm")
        h = _to_mm(float(m.group(3)), _normalize_unit(unit) or "mm")
        return l, w, h
    l = w = h = None
    for label, slot in (("lunghezza", "l"), ("larghezza", "w"), ("altezza", "h")):
        found = re.search(rf"{label}\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|m)", norm)
        if found:
            converted = _to_mm(float(found.group(1)), _normalize_unit(found.group(2)) or "mm")
            if slot == "l":
                l = converted
            elif slot == "w":
                w = converted
            else:
                h = converted
    return l, w, h


def _format_mm(value: float | None) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _material_candidates(feats: BaseFeatures, allowed: set[str]) -> List[Tuple[str, str]]:
    return [(m.value, m.context) for m in feats.materials if m.value in allowed]


def _brand_value(feats: BaseFeatures) -> Optional[str]:
    return feats.brands[0].value if feats.brands else None


def _match_property_patterns(text: str, category_id: str, property_id: str, session: Session | None = None) -> List[Tuple[str, str]]:
    """
    Applica pattern dinamici su testo grezzo e ritorna [(valore, contesto)].
    """
    matched: list[Tuple[str, str]] = []
    text_norm = normalize_text(text)
    for entry in _get_patterns(session):
        if entry["category_id"] and entry["category_id"] != category_id:
            continue
        if entry["property_id"] and entry["property_id"] != property_id:
            continue
        ctx_keywords = entry.get("context_keywords") or []
        if ctx_keywords and not all(kw.lower() in text_norm for kw in ctx_keywords):
            continue
        try:
            for m in re.finditer(entry["pattern"], text, flags=re.IGNORECASE):
                span = m.group(0).strip()
                if span:
                    matched.append((span, _context_window(text, m.start(), m.end())))
        except re.error:
            continue
    return matched


# --------- Category mapping ---------
def map_controsoffitti(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)

    mat_candidates = _material_candidates(
        feats,
        {"acciaio", "alluminio", "cartongesso", "lana_minerale", "fibra_minerale"},
    )
    mat_candidates.extend(_match_property_patterns(text, "controsoffitti", "materiale"))
    materiale = resolver.resolve(
        category_id="controsoffitti",
        property_id="materiale",
        candidates=mat_candidates,
        threshold=0.35,
    )
    props["materiale"] = materiale

    thickness_cands: list[tuple[str, str]] = []
    for n in feats.numbers:
        if n.unit not in {"mm", "cm", "m"}:
            continue
        if re.search(r"(controsoffitto|pannell|lastr)", n.context, flags=re.IGNORECASE):
            thickness_cands.append((str(_to_mm(n.value, n.unit)), n.context))
    thickness_cands.extend(_match_property_patterns(text, "controsoffitti", "spessore_pannello_mm"))
    spessore_raw = resolver.resolve(
        category_id="controsoffitti",
        property_id="spessore_pannello_mm",
        candidates=thickness_cands,
        threshold=0.3,
    )
    try:
        props["spessore_pannello_mm"] = float(spessore_raw) if spessore_raw else None
    except ValueError:
        props["spessore_pannello_mm"] = None

    props["classe_reazione_al_fuoco"] = _first_class_by_kind(feats.classes, "reazione_fuoco")
    props["colore_ral"] = _extract_ral(text)
    props["coefficiente_fonoassorbimento"] = _extract_fonoassorbimento(text_norm)
    props["stratigrafia_lastre"] = _extract_stratigrafia(text)
    props["normativa_riferimento"] = _join_normative(feats)
    return props


def map_opere_da_cartongessista(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    props["stratigrafia_lastre"] = _extract_stratigrafia(text)
    props["classe_ei"] = _first_class_by_kind(feats.classes, "classe_ei")
    props["classe_reazione_al_fuoco"] = _first_class_by_kind(feats.classes, "reazione_fuoco")
    has_insulation = any(m.value in {"lana_minerale", "fibra_minerale"} for m in feats.materials) or any(
        kw in text_norm for kw in INSULATION_KEYWORDS
    )
    props["presenza_isolante"] = "si" if has_insulation else "no"
    props["normativa_riferimento"] = _join_normative(feats)
    return props


def map_opere_di_rivestimento(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    mat_candidates = _material_candidates(
        feats, {"gres", "pietra", "ceramica", "legno", "resina", "intonaco", "laminato", "metallo"}
    )
    mat_candidates.extend(_match_property_patterns(text, "opere_di_rivestimento", "materiale"))
    materiale = resolver.resolve(
        category_id="opere_di_rivestimento",
        property_id="materiale",
        candidates=mat_candidates,
        threshold=0.35,
    )
    props["materiale"] = materiale

    finitura_match = re.search(r"(finitura|surface|finish)\s*[:=]?\s*([^\.;\n]+)", text, flags=re.IGNORECASE)
    if finitura_match:
        props["finitura"] = finitura_match.group(2).strip()

    thickness_cands: list[tuple[str, str]] = []
    for n in feats.numbers:
        if n.unit in {"mm", "cm", "m"} and re.search(r"spessore|rivest", n.context, flags=re.IGNORECASE):
            thickness_cands.append((str(_to_mm(n.value, n.unit)), n.context))
    thickness_cands.extend(_match_property_patterns(text, "opere_di_rivestimento", "spessore_mm"))
    spessore_raw = resolver.resolve(
        category_id="opere_di_rivestimento",
        property_id="spessore_mm",
        candidates=thickness_cands,
        threshold=0.3,
    )
    try:
        props["spessore_mm"] = float(spessore_raw) if spessore_raw else None
    except ValueError:
        props["spessore_mm"] = None

    posa_map = {
        "incollata": ["incollata", "colla", "glued"],
        "flottante": ["flottante", "galleggiante", "floating"],
        "a secco": ["a secco", "dry"],
        "meccanica": ["meccanica", "fissaggi meccanici", "mechanical"],
        "su struttura": ["su struttura", "struttura metallica", "frame"],
    }
    for target, kws in posa_map.items():
        if any(kw in text_norm for kw in kws):
            props["posa"] = target
            break

    props["classe_reazione_al_fuoco"] = _first_class_by_kind(feats.classes, "reazione_fuoco")
    props["normativa_riferimento"] = _join_normative(feats)
    return props


def map_opere_di_pavimentazione(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    mat_candidates = _material_candidates(
        feats,
        {"gres", "legno", "laminato", "resina", "pietra_naturale", "calcestruzzo", "vinilico"},
    )
    mat_candidates.extend(_match_property_patterns(text, "opere_di_pavimentazione", "materiale"))
    materiale = resolver.resolve(
        category_id="opere_di_pavimentazione",
        property_id="materiale",
        candidates=mat_candidates,
        threshold=0.35,
    )
    props["materiale"] = materiale

    formato_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(mm|cm|m))?", text_norm)
    if formato_match:
        unit = formato_match.group(3) or "mm"
        unit_norm = _normalize_unit(unit) or "mm"
        n1 = _to_mm(float(formato_match.group(1)), unit_norm)
        n2 = _to_mm(float(formato_match.group(2)), unit_norm)
        n1_str = f"{int(n1)}" if n1.is_integer() else f"{n1}"
        n2_str = f"{int(n2)}" if n2.is_integer() else f"{n2}"
        props["formato"] = f"{n1_str}x{n2_str} mm"
    else:
        fmt_patterns = _match_property_patterns(text, "opere_di_pavimentazione", "formato")
        if fmt_patterns:
            props["formato"] = fmt_patterns[0][0]

    thickness_cands: list[tuple[str, str]] = []
    for n in feats.numbers:
        if n.unit in {"mm", "cm", "m"} and re.search(r"(spessore|paviment|piastrella|mattonell)", n.context, flags=re.IGNORECASE):
            thickness_cands.append((str(_to_mm(n.value, n.unit)), n.context))
    thickness_cands.extend(_match_property_patterns(text, "opere_di_pavimentazione", "spessore_mm"))
    spessore_raw = resolver.resolve(
        category_id="opere_di_pavimentazione",
        property_id="spessore_mm",
        candidates=thickness_cands,
        threshold=0.3,
    )
    try:
        props["spessore_mm"] = float(spessore_raw) if spessore_raw else None
    except ValueError:
        props["spessore_mm"] = None
    props["classe_resistenza_usura"] = _first_class_by_kind(feats.classes, "pei")
    props["classe_scivolosita"] = _first_class_by_kind(feats.classes, "r_scivolosita")
    props["normativa_riferimento"] = _join_normative(feats)
    return props
def map_opere_da_serramentista(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    mat_candidates = _material_candidates(feats, {"alluminio", "acciaio", "legno", "pvc", "legno_alluminio"})
    mat_candidates.extend(_match_property_patterns(text, "opere_da_serramentista", "materiale_struttura"))
    materiale = resolver.resolve(
        category_id="opere_da_serramentista",
        property_id="materiale_struttura",
        candidates=mat_candidates,
        threshold=0.3,
    )
    props["materiale_struttura"] = materiale

    width, height = _dimension_pair_from_text(text)
    props["dimensione_larghezza"] = _format_mm(width)
    props["dimensione_altezza"] = _format_mm(height)

    uw_match = None
    for n in feats.numbers:
        if n.unit == "w_m2k":
            uw_match = n
            break
    if not uw_match:
        uw_search = re.search(r"\bu[w]?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", text_norm)
        if uw_search:
            props["trasmittanza_termica"] = float(uw_search.group(1))
    else:
        props["trasmittanza_termica"] = float(uw_match.value)

    for n in feats.numbers:
        if n.unit == "db" or re.search(r"(rw|acustico)", n.context, flags=re.IGNORECASE):
            props["isolamento_acustico_db"] = float(n.value)
            break

    props["normativa_riferimento"] = _join_normative(feats)
    return props


def map_apparecchi_sanitari_accessori(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    mat_candidates = _material_candidates(
        feats,
        {"ceramica", "acciaio_inox", "resina", "vetro", "ghisa", "porcellana", "metallo", "plastica", "legno"},
    )
    mat_candidates.extend(_match_property_patterns(text, "apparecchi_sanitari_accessori", "materiale"))
    materiale = resolver.resolve(
        category_id="apparecchi_sanitari_accessori",
        property_id="materiale",
        candidates=mat_candidates,
        threshold=0.35,
    )
    props["materiale"] = materiale

    l, w, h = _dimension_triplet_from_text(text)
    props["dimensione_lunghezza"] = _format_mm(l)
    props["dimensione_larghezza"] = _format_mm(w)
    props["dimensione_altezza"] = _format_mm(h)

    install_map = {
        "a_pavimento": ["a pavimento", "floor mounted"],
        "a_parete": ["a parete", "a muro", "wall hung", "wall-hung"],
        "sospesa": ["sospeso", "sospesa", "suspended"],
        "incasso": ["incasso", "recessed", "da incasso"],
    }
    for target, kws in install_map.items():
        if any(kw in text_norm for kw in kws):
            props["tipologia_installazione"] = target
            break

    for n in feats.numbers:
        if n.unit == "l_min":
            props["portata_l_min"] = float(n.value)
            break
    if "portata_l_min" not in props:
        flow = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*l/?\s*min", text_norm)
        if flow:
            props["portata_l_min"] = float(flow.group(1))

    props["normativa_riferimento"] = _join_normative(feats)
    return props


def map_opere_da_falegname(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver) -> dict:
    props: dict[str, Any] = {}
    props["marchio"] = _brand_value(feats)
    essenza_candidates = _material_candidates(
        feats, {"rovere", "faggio", "pino", "abete", "larice", "noce", "castagno"}
    )
    essenza_candidates.extend(_match_property_patterns(text, "opere_da_falegname", "essenza"))
    essenza = resolver.resolve(
        category_id="opere_da_falegname",
        property_id="essenza",
        candidates=essenza_candidates,
        threshold=0.3,
    )
    props["essenza"] = essenza

    width, height = _dimension_pair_from_text(text)
    props["dimensione_larghezza"] = _format_mm(width)
    props["dimensione_altezza"] = _format_mm(height)

    apertura_map = {
        "battente": ["battente", "hinged"],
        "scorrevole": ["scorrevole", "sliding"],
        "a_ribalta": ["a ribalta", "tilt"],
        "a_scomparsa": ["a scomparsa", "pocket"],
        "anta_ribalta": ["anta ribalta", "tilt&turn", "tilt and turn"],
    }
    for target, kws in apertura_map.items():
        if any(kw in text_norm for kw in kws):
            props["tipologia_apertura"] = target
            break

    props["normativa_riferimento"] = _join_normative(feats)
    return props


# --------- Public API ---------


def extract_properties_from_text(text: str, category_id: str) -> ExtractedProperties:
    schemas = load_category_schema()
    if category_id not in schemas:
        raise ValueError(f"Categoria non supportata: {category_id}")

    if resolver.model is None and not EMBEDDINGS_DISABLED:
        init_model()
        init_property_prototypes()

    text_norm = normalize_text(text)
    feats = extract_base_features(text)
    if category_id == "controsoffitti":
        props = map_controsoffitti(text, text_norm, feats, resolver)
    elif category_id == "opere_da_cartongessista":
        props = map_opere_da_cartongessista(text, text_norm, feats, resolver)
    elif category_id == "opere_di_rivestimento":
        props = map_opere_di_rivestimento(text, text_norm, feats, resolver)
    elif category_id == "opere_di_pavimentazione":
        props = map_opere_di_pavimentazione(text, text_norm, feats, resolver)
    elif category_id == "opere_da_serramentista":
        props = map_opere_da_serramentista(text, text_norm, feats, resolver)
    elif category_id == "apparecchi_sanitari_accessori":
        props = map_apparecchi_sanitari_accessori(text, text_norm, feats, resolver)
    elif category_id == "opere_da_falegname":
        props = map_opere_da_falegname(text, text_norm, feats, resolver)
    else:
        props = {}

    required = CATEGORY_REQUIRED.get(category_id, [])
    missing: List[str] = [p for p in required if not props.get(p)]

    return {
        "category_id": category_id,
        "properties": props,
        "missing_required": missing,
    }


def extract_properties(text: str, category_id: str) -> ExtractedProperties:
    # Backward compatible alias
    return extract_properties_from_text(text, category_id)


def list_categories() -> List[CategorySchema]:
    return list(load_category_schema().values())


def guess_category_id(entry: dict[str, Any]) -> Optional[str]:
    """
    Best-effort heuristics to infer category from WBS/description when not provided explicitly.
    """
    text_parts: List[str] = []
    for key in ("category_id", "wbs6_description", "wbs7_description", "wbs6_code", "description", "item_description"):
        val = entry.get(key)
        if isinstance(val, str):
            text_parts.append(val.lower())
    haystack = " ".join(text_parts)
    if not haystack:
        return None

    keyword_map: list[tuple[str, list[str]]] = [
        ("controsoffitti", ["controsoffit", "controsoffitto", "soffitto"]),
        ("opere_di_pavimentazione", ["paviment", "pavimento", "piastrella", "mattonella", "gres"]),
        ("opere_di_rivestimento", ["rivest", "cladding", "facciata ventilata", "parete ventilata"]),
        ("opere_da_cartongessista", ["cartongess", "plasterboard", "lastra", "parete in gesso"]),
        ("opere_da_serramentista", ["serrament", "infiss", "vetrocamera", "profilo", "uw"]),
        ("apparecchi_sanitari_accessori", ["sanitari", "wc", "lavabo", "bidet", "rubinet", "doccia"]),
        ("opere_da_falegname", ["falegn", "porta in legno", "serramento in legno", "infisso in legno"]),
    ]
    for cat_id, keywords in keyword_map:
        if any(kw in haystack for kw in keywords):
            return cat_id
    return None


def _apply_override(
    result: ExtractedProperties, price_list_item_id: Optional[int], session: Session | None = None
) -> ExtractedProperties:
    if not price_list_item_id or not engine or PropertyOverride is None:
        return result
    sess = session or Session(engine)
    override = None
    try:
        override = sess.exec(
            select(PropertyOverride).where(PropertyOverride.price_list_item_id == price_list_item_id)
        ).first()
    finally:
        if session is None:
            sess.close()
    if not override:
        return result
    merged_props = dict(result["properties"])
    merged_props.update(override.properties or {})
    required = CATEGORY_REQUIRED.get(result["category_id"], [])
    missing: List[str] = [p for p in required if not merged_props.get(p)]
    return {
        "category_id": result["category_id"],
        "properties": merged_props,
        "missing_required": missing,
    }


def extract_properties_auto(entry: dict[str, Any], session: Session | None = None, apply_override: bool = True) -> Optional[ExtractedProperties]:
    """
    Convenience wrapper che prova a inferire la categoria e applica override da DB se presenti.
    """
    text = entry.get("description") or entry.get("item_description") or ""
    if not text:
        return None
    category_id = entry.get("category_id") or guess_category_id(entry)
    if not category_id:
        return None
    result = extract_properties_from_text(text=text, category_id=category_id)
    if apply_override:
        price_item_id = entry.get("id")
        result = _apply_override(result, price_item_id, session=session)
    return result
