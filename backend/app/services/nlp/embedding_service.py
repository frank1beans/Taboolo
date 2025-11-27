from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Mapping, Sequence

import faiss  # type: ignore
import numpy as np
import psycopg2
from psycopg2.extensions import connection as PGConnection

try:  # pragma: no cover - optional dependency is validated at runtime
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled at runtime
    SentenceTransformer = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from huggingface_hub import snapshot_download
except ImportError:  # pragma: no cover - handled at runtime
    snapshot_download = None  # type: ignore[assignment]

from app.core.config import settings
import re


logger = logging.getLogger(__name__)


def extract_construction_attributes(text: str) -> dict[str, Any]:
    """Estrae attributi strutturati da descrizioni di voci edilizie.

    Utile per ricerca ibrida semantica + attributi specifici.
    """
    if not text:
        return {}

    text_lower = text.lower()
    attributes: dict[str, Any] = {}

    # Numero lastre cartongesso
    lastre_patterns = [
        r"(\d+)\s*lastr[ae]",
        r"lastr[ae]\s*[xX×]\s*(\d+)",
        r"(\d+)\s*x\s*lastr",
        r"doppia\s+lastra",
        r"singola\s+lastra",
        r"tripla\s+lastra",
    ]
    for pattern in lastre_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if "doppia" in pattern:
                attributes["num_lastre"] = 2
            elif "singola" in pattern:
                attributes["num_lastre"] = 1
            elif "tripla" in pattern:
                attributes["num_lastre"] = 3
            else:
                attributes["num_lastre"] = int(match.group(1))
            break

    # Spessore (mm o cm)
    spessore_patterns = [
        r"spessore\s*(?:di|:)?\s*(\d+(?:[.,]\d+)?)\s*(?:mm|cm)",
        r"(\d+(?:[.,]\d+)?)\s*(?:mm|cm)\s*(?:di\s+)?spessore",
        r"sp\.?\s*(\d+(?:[.,]\d+)?)\s*(?:mm|cm)",
        r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)",  # es: 13/50/13
    ]
    for pattern in spessore_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if "/" in pattern:
                # Formato tipo 13/50/13 - somma spessori
                parts = [int(g) for g in match.groups() if g]
                attributes["spessore_mm"] = sum(parts)
                attributes["spessore_dettaglio"] = "/".join(map(str, parts))
            else:
                value = float(match.group(1).replace(",", "."))
                if "cm" in text_lower[match.start():match.end() + 5]:
                    value *= 10
                attributes["spessore_mm"] = int(value)
            break

    # Tipo rivestimento
    rivestimenti = {
        "ceramica": ["ceramic", "piastrelle", "gres", "porcellanato"],
        "legno": ["legno", "parquet", "laminato", "listone"],
        "pietra": ["pietra", "marmo", "granito", "travertino", "ardesia"],
        "resina": ["resina", "epossidic"],
        "pvc": ["pvc", "vinilico", "lvt"],
        "moquette": ["moquette", "tappeto"],
        "intonaco": ["intonaco", "rasatura", "stucco"],
        "pittura": ["pittura", "tinteggiatura", "verniciatura"],
        "carta_parati": ["carta da parati", "wallpaper", "tappezzeria"],
    }
    for tipo, keywords in rivestimenti.items():
        if any(kw in text_lower for kw in keywords):
            attributes["tipo_rivestimento"] = tipo
            break

    # Tipo lastra cartongesso
    tipi_lastra = {
        "standard": ["standard", "normale", "ba13"],
        "idrofuga": ["idrofug", "resistente all'acqua", "h1", "verde"],
        "ignifuga": ["ignifug", "resistente al fuoco", "ei", "rosa", "df"],
        "acustica": ["acustic", "fonoassorbente", "fonoisolante"],
        "alta_densita": ["alta densità", "hd", "durlock"],
    }
    for tipo, keywords in tipi_lastra.items():
        if any(kw in text_lower for kw in keywords):
            attributes["tipo_lastra"] = tipo
            break

    # Struttura metallica
    if any(kw in text_lower for kw in ["montante", "guida", "profilo", "orditura"]):
        montante_match = re.search(r"c\s*(\d+)", text_lower)
        if montante_match:
            attributes["montante_mm"] = int(montante_match.group(1))

    # Isolamento
    isolamenti = {
        "lana_roccia": ["lana di roccia", "lana roccia", "rockwool"],
        "lana_vetro": ["lana di vetro", "lana vetro"],
        "polistirene": ["polistirene", "eps", "xps", "polistirolo"],
        "fibra_legno": ["fibra di legno", "fibra legno"],
        "sughero": ["sughero"],
    }
    for tipo, keywords in isolamenti.items():
        if any(kw in text_lower for kw in keywords):
            attributes["isolamento"] = tipo
            break

    return attributes

AVAILABLE_SEMANTIC_MODELS: list[dict[str, Any]] = [
    {
        "id": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "label": "MPNet Base",
        "description": "Bilanciato, preciso e multilingua (50+ lingue).",
        "dimension": 768,
        "languages": "Multilingua (50+ lingue)",
        "speed": "Bilanciato",
    },
    {
        "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "label": "MiniLM L12",
        "description": "Molto veloce, ideale su macchine leggere.",
        "dimension": 384,
        "languages": "Multilingua (50+ lingue)",
        "speed": "Veloce",
    },
    {
        "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2",
        "label": "MiniLM L6",
        "description": "Compromesso prestazioni/risorse, 384 dimensioni.",
        "dimension": 384,
        "languages": "Multilingua (50+ lingue)",
        "speed": "Molto veloce",
    },
    {
        "id": "intfloat/multilingual-e5-large",
        "label": "E5 Large",
        "description": "Modello large ottimizzato per ricerche semantiche complesse in italiano e lingue europee.",
        "dimension": 1024,
        "languages": "Italiano + Multilingua avanzato",
        "speed": "Accurato (richiede GPU/tempo)",
    },
    {
        "id": "intfloat/multilingual-e5-large-instruct",
        "label": "E5 Large Instruct",
        "description": "Versione instruction-tuned ad alta fedeltà, ideale per embedding di documenti tecnici italiani.",
        "dimension": 1024,
        "languages": "Italiano + Multilingua avanzato",
        "speed": "Più lento, massima precisione",
    },
]

DEFAULT_SEMANTIC_MODEL_ID = AVAILABLE_SEMANTIC_MODELS[0]["id"]


class SemanticEmbeddingService:
    """
    Gestisce il calcolo degli embedding semantici.

    ATTENZIONE:
    - Questa versione NON usa più RoBERTino / ONNX come feature extractor.
    - Usa un modello SentenceTransformer pensato per semantic search con cosine similarity.
    - L'API pubblica è compatibile con la versione precedente (metodi e payload).
    """

    def __init__(
        self,
        *,
        model_id: str | None = None,
        model_revision: str | None = None,   # tenuti per compatibilità, non usati
        model_subfolder: str | None = None,  # tenuti per compatibilità, non usati
        execution_providers: Sequence[str] | None = None,  # compatibilità, ignorato
        cache_dir: Path | None = None,
        max_length: int | None = None,
        batch_size: int | None = None,
    ) -> None:
        # Scegli il modello di default:
        # 1) settings.nlp_semantic_model_id (se esiste)
        # 2) settings.nlp_model_id
        # 3) fallback hardcoded
        default_model_id = (
            getattr(settings, "nlp_semantic_model_id", None)
            or getattr(settings, "nlp_model_id", None)
            or DEFAULT_SEMANTIC_MODEL_ID
        )
        self.model_id = model_id or default_model_id

        # Questi campi restano per non rompere altra logica che li legge
        self.model_revision = model_revision or getattr(settings, "nlp_model_revision", None)
        self.model_subfolder = model_subfolder or getattr(settings, "nlp_model_subfolder", None)
        self.execution_providers: tuple[str, ...] = tuple(execution_providers or ())

        resolved_cache_dir = cache_dir or (settings.storage_root / "models" / "semantic")
        self.cache_dir = resolved_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_length = max_length or getattr(settings, "nlp_max_length", 256)
        self.batch_size = batch_size or getattr(settings, "nlp_batch_size", 32)

        self.metadata_slot = "semantic_embedding_v1"
        self.legacy_metadata_slots: tuple[str, ...] = ("robertino_semantic_v1",)

        self._model: SentenceTransformer | None = None
        self._lock = Lock()
        self._disabled = False
        self._load_error: str | None = None
        self._embedding_dimension: int | None = None

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def configure(
        self,
        *,
        model_id: str | None = None,
        max_length: int | None = None,
        batch_size: int | None = None,
    ) -> None:
        """
        Aggiorna la configurazione del modello.
        Se cambia qualcosa, il modello viene ricaricato al prossimo utilizzo.
        """
        changed = False
        with self._lock:
            if model_id and model_id != self.model_id:
                self.model_id = model_id
                changed = True
            if max_length and max_length != self.max_length:
                self.max_length = max_length
                changed = True
            if batch_size and batch_size != self.batch_size:
                self.batch_size = batch_size
                changed = True

            if changed:
                self._model = None
                self._embedding_dimension = None
                self._disabled = False
                self._load_error = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_dependencies(self) -> None:
        if SentenceTransformer is None:
            raise RuntimeError(
                "Dipendenze NLP mancanti. Installa 'sentence-transformers' "
                "per abilitare gli embedding semantici."
            )
        if snapshot_download is None:
            raise RuntimeError(
                "huggingface-hub non disponibile. Installa 'huggingface-hub' per scaricare i modelli."
            )

    def download_model(self) -> None:
        """Scarica il modello configurato, se non già presente."""
        self._ensure_dependencies()
        assert snapshot_download is not None  # per mypy
        snapshot_download(
            repo_id=self.model_id,
            cache_dir=str(self.cache_dir),
            local_files_only=False,
        )

    def iter_metadata_slots(self) -> list[str]:
        return [self.metadata_slot, *self.legacy_metadata_slots]

    def extract_embedding_payload(self, payload: Mapping[str, Any]) -> dict[str, Any] | None:
        for slot in self.iter_metadata_slots():
            candidate = payload.get(slot)
            if isinstance(candidate, dict):
                return candidate
        return None

    def _ensure_model(self) -> None:
        """
        Carica il modello SentenceTransformer usato per gli embedding.
        """
        if self._disabled:
            raise RuntimeError(self._load_error or "Servizio di embedding semantici disabilitato")

        self._ensure_dependencies()

        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            try:
                self.download_model()
                logger.info("Carico modello di embedding semantici: %s", self.model_id)
                model = SentenceTransformer(
                    self.model_id,
                    cache_folder=str(self.cache_dir),
                )
                # Imposto la lunghezza massima se possibile
                try:
                    model.max_seq_length = int(self.max_length)
                except Exception:  # pragma: no cover - best effort
                    logger.warning(
                        "Impossibile impostare max_seq_length=%s per il modello %s",
                        self.max_length,
                        self.model_id,
                    )
            except Exception as exc:  # pragma: no cover - defensive guard
                self._disabled = True
                self._load_error = str(exc)
                logger.error("Impossibile caricare il modello di embedding semantici: %s", exc)
                raise RuntimeError(str(exc)) from exc
            else:
                self._model = model
                self._disabled = False
                self._load_error = None

    def _compose_entry_text(self, entry: Mapping[str, Any]) -> str:
        """
        Costruisce il testo "pulito" da usare per la semantic search.

        Scelte precise:
        - TENGO: codice, descrizione, descrizioni WBS, eventuali label testuali.
        - ESCLUDO: prezzi, listini numerici, "Preferiti", ecc.
          perché appiattiscono la similarità senza aggiungere informazione semantica.
        """
        parts: list[str] = []

        code = entry.get("item_code") or entry.get("code") or entry.get("product_id")
        description = entry.get("item_description") or entry.get("description")

        if code:
            parts.append(str(code))
        if description:
            parts.append(str(description))

        wbs6_description = entry.get("wbs6_description")
        wbs7_description = entry.get("wbs7_description")

        if wbs6_description:
            parts.append(str(wbs6_description))
        if wbs7_description:
            parts.append(str(wbs7_description))

        price_list_labels = entry.get("price_list_labels")
        if isinstance(price_list_labels, Mapping):
            label_tokens = {
                str(label).strip()
                for label in price_list_labels.values()
                if isinstance(label, str) and label.strip()
            }
            if label_tokens:
                parts.append(" ".join(sorted(label_tokens)))

        text = " • ".join(part.strip() for part in parts if str(part).strip())
        return text.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        if self._disabled:
            return False
        try:
            self._ensure_model()
        except RuntimeError:
            return False
        return True

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Calcola gli embedding normalizzati per una lista di testi.

        - Restituisce una lista di liste di float (compatibile con versione precedente).
        - I vettori sono già L2-normalizzati (pronti per cosine/dot product).
        """
        if not texts:
            return []

        self._ensure_model()
        assert self._model is not None  # nosec: B101 - guarded by _ensure_model

        vectors = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine = dot product
            batch_size=int(self.batch_size),
            show_progress_bar=False,
        )

        if not isinstance(vectors, np.ndarray):
            vectors = np.asarray(vectors, dtype=np.float32)

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        self._embedding_dimension = int(vectors.shape[1])
        return vectors.astype(np.float32).tolist()

    def embed_text(self, text: str) -> list[float]:
        """
        Shortcut per un singolo testo.
        """
        vectors = self.embed_texts([text])
        return vectors[0] if vectors else []

    def warmup(self) -> None:
        """Scarica e prepara il modello configurato se non è già caricato."""
        self._ensure_model()

    def prepare_price_list_metadata(self, entry: Mapping[str, Any]) -> dict[str, Any] | None:
        """
        Prepara il payload da salvare come metadato vettoriale per una voce di prezzario.

        Struttura di ritorno:
        {
            "model_id": ...,
            "model_revision": ... (se configurato),
            "vector": [...],
            "dimension": int,
            "match_reason": "semantic",
            "attributes": {...}  # attributi strutturati estratti
        }
        """
        text = self._compose_entry_text(entry)
        if not text:
            return None

        vector = self.embed_text(text)
        if not vector:
            return None

        # Estrai attributi strutturati per ricerca ibrida
        description = entry.get("item_description") or entry.get("description") or ""
        attributes = extract_construction_attributes(description)

        payload: dict[str, Any] = {
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "vector": [float(value) for value in vector],
            "dimension": len(vector),
            "match_reason": "semantic",
        }

        if attributes:
            payload["attributes"] = attributes

        if self._embedding_dimension:
            payload["dimension"] = self._embedding_dimension

        return payload


semantic_embedding_service = SemanticEmbeddingService()


def get_available_semantic_models() -> list[dict[str, Any]]:
    """Ritorna la lista dei modelli configurabili per la ricerca semantica."""
    return AVAILABLE_SEMANTIC_MODELS.copy()


class DocumentFaissPipeline:
    """Pipeline per indicizzare e cercare documenti con FAISS e SentenceTransformer."""

    DIM = 384
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    INDEX_FILENAME = "index_documenti.faiss"

    def __init__(
        self,
        *,
        index_path: Path | None = None,
        model_name: str | None = None,
        embedding_dim: int | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        resolved_model = (
            model_name
            or getattr(settings, "nlp_model_id", None)
            or self.MODEL_NAME
        )
        self.model_name = resolved_model
        self.embedding_dim: int | None = (
            int(embedding_dim) if embedding_dim is not None else None
        )
        resolved_cache_dir = cache_dir or (settings.storage_root / "models" / "semantic")
        self.cache_dir = Path(resolved_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        default_index_path = settings.storage_root / "nlp" / self.INDEX_FILENAME
        self.index_path = Path(index_path or default_index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self._model: SentenceTransformer | None = None
        self._index: faiss.IndexIDMap | None = None
        self._model_lock = Lock()
        self._index_lock = Lock()

    def get_db_connection(self) -> PGConnection:
        try:
            return psycopg2.connect(
                host=os.environ["DB_HOST"],
                port=os.environ.get("DB_PORT", "5432"),
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
            )
        except KeyError as exc:  # pragma: no cover - runtime safety
            missing = exc.args[0]
            raise RuntimeError(f"Variabile d'ambiente mancante: {missing}") from exc
        except psycopg2.Error as exc:  # pragma: no cover - runtime safety
            raise RuntimeError(f"Errore di connessione al database: {exc}") from exc

    def load_documents(self, conn: PGConnection | None = None) -> list[tuple[int, str, str]]:
        if conn is None:
            with self.get_db_connection() as owned_conn:
                return self.load_documents(owned_conn)

        with conn.cursor() as cur:
            cur.execute("SELECT id, titolo, contenuto FROM documenti")
            rows: list[tuple[int, str, str]] = cur.fetchall()
        return rows

    def _ensure_model(self) -> SentenceTransformer:
        if SentenceTransformer is None:  # pragma: no cover - optional dependency guard
            raise RuntimeError(
                "Dipendenze NLP mancanti. Installa 'sentence-transformers' per abilitare gli embedding."
            )
        if self._model is not None:
            return self._model
        with self._model_lock:
            if self._model is None:
                logger.info("Carico modello FAISS pipeline: %s", self.model_name)
                model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(self.cache_dir),
                )
                self._model = model
                if self.embedding_dim is None:
                    try:
                        dim = model.get_sentence_embedding_dimension()
                    except AttributeError:
                        dim = model.get_sentence_embedding_dimension()
                    self.embedding_dim = int(dim)
        return self._model

    def load_model(self) -> SentenceTransformer:
        return self._ensure_model()

    def configure(
        self,
        *,
        model_name: str | None = None,
        embedding_dim: int | None = None,
    ) -> None:
        """Aggiorna il modello utilizzato per la pipeline FAISS."""
        desired_model = (
            model_name
            or getattr(settings, "nlp_model_id", None)
            or self.MODEL_NAME
        )
        changed = False
        if desired_model != self.model_name:
            self.model_name = desired_model
            if embedding_dim is None:
                self.embedding_dim = None
            changed = True
        if embedding_dim is not None:
            new_dim = int(embedding_dim)
            if self.embedding_dim != new_dim:
                self.embedding_dim = new_dim
                changed = True
        if changed:
            self._model = None
            self._index = None

    def _ensure_dimension(self) -> int:
        if self.embedding_dim is not None:
            return self.embedding_dim
        model = self._ensure_model()
        try:
            dim = model.get_sentence_embedding_dimension()
        except AttributeError:
            dim = model.get_sentence_embedding_dimension()
        self.embedding_dim = int(dim)
        return self.embedding_dim

    def generate_embeddings(
        self,
        documents: Iterable[tuple[int, str, str]],
        model: SentenceTransformer | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        document_list = list(documents)
        if not document_list:
            raise ValueError("Nessun documento da indicizzare.")

        model = model or self._ensure_model()
        ids = np.asarray([doc[0] for doc in document_list], dtype=np.int64)
        texts = [f"{doc[1]}\n{doc[2]}" for doc in document_list]

        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        embeddings = np.asarray(embeddings, dtype=np.float32)

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        expected_dim = self._ensure_dimension()
        if embeddings.shape[1] != expected_dim:
            raise ValueError(
                f"Dimensione embedding inattesa: {embeddings.shape[1]} (attesa {expected_dim})"
            )

        faiss.normalize_L2(embeddings)
        return embeddings, ids

    def _new_index(self) -> faiss.IndexIDMap:
        dim = self._ensure_dimension()
        index_flat = faiss.IndexFlatIP(dim)
        return faiss.IndexIDMap(index_flat)

    def build_index(self, embeddings: np.ndarray, ids: np.ndarray) -> faiss.IndexIDMap:
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        if ids.dtype != np.int64:
            ids = ids.astype(np.int64)
        index = self._new_index()
        index.add_with_ids(embeddings, ids)
        self._index = index
        return index

    def save_index(self, index: faiss.Index) -> Path:
        faiss.write_index(index, str(self.index_path))
        return self.index_path

    def load_index(self) -> faiss.IndexIDMap:
        if self._index is not None:
            return self._index

        with self._index_lock:
            if self._index is None:
                loaded = faiss.read_index(str(self.index_path))
                if not isinstance(loaded, faiss.IndexIDMap):
                    loaded = faiss.IndexIDMap(loaded)
                expected_dim = self._ensure_dimension()
                if loaded.d != expected_dim:
                    raise ValueError(
                        f"Dimensione indice ({loaded.d}) non corrisponde a quella attesa ({expected_dim})."
                    )
                self._index = loaded
        assert self._index is not None
        return self._index

    def build_index_from_db(self) -> tuple[faiss.IndexIDMap, np.ndarray, np.ndarray]:
        documents = self.load_documents()
        embeddings, ids = self.generate_embeddings(documents)
        index = self.build_index(embeddings, ids)
        self.save_index(index)
        return index, embeddings, ids

    def semantic_search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        trimmed = query.strip()
        if not trimmed:
            return []

        model = self._ensure_model()
        query_vec = model.encode(trimmed, convert_to_numpy=True, normalize_embeddings=False)
        query_vec = np.asarray(query_vec, dtype=np.float32)
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        expected_dim = self._ensure_dimension()
        if query_vec.shape[1] != expected_dim:
            raise ValueError(
                f"Dimensione embedding della query ({query_vec.shape[1]}) inattesa (attesa {expected_dim})."
            )
        faiss.normalize_L2(query_vec)

        index = self.load_index()
        scores, ids = index.search(query_vec, k)

        valid_pairs = [
            (int(doc_id), float(score))
            for doc_id, score in zip(ids[0], scores[0])
            if doc_id != -1
        ]

        if not valid_pairs:
            return []

        id_list = [doc_id for doc_id, _ in valid_pairs]

        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, titolo, contenuto FROM documenti WHERE id = ANY(%s)",
                    (id_list,),
                )
                rows = cur.fetchall()

        row_map: dict[int, dict[str, Any]] = {
            int(row[0]): {"id": int(row[0]), "titolo": row[1], "contenuto": row[2]}
            for row in rows
        }

        results: list[dict[str, Any]] = []
        for doc_id, score in valid_pairs:
            if doc_id in row_map:
                entry = row_map[doc_id].copy()
                entry["similarity"] = score
                results.append(entry)

        results.sort(key=lambda item: item["similarity"], reverse=True)
        return results


document_faiss_pipeline = DocumentFaissPipeline()


class PriceListFaissService:
    """Servizio FAISS per ricerca semantica veloce su PriceListItem.

    Costruisce e gestisce indici FAISS usando gli embedding già salvati
    in extra_metadata.nlp.vector. Supporta indici per commessa o globali.
    """

    INDEX_FILENAME = "price_list_index.faiss"
    IDS_FILENAME = "price_list_ids.npy"

    def __init__(self, *, cache_dir: Path | None = None) -> None:
        resolved_cache_dir = cache_dir or (settings.storage_root / "nlp" / "price_list")
        self.cache_dir = Path(resolved_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._index: faiss.IndexIDMap | None = None
        self._id_to_item: dict[int, int] = {}  # FAISS ID -> PriceListItem ID
        self._index_lock = Lock()
        self._embedding_dim: int | None = None
        self._index_version: str | None = None

    def _get_index_path(self, commessa_id: int | None = None) -> Path:
        if commessa_id:
            return self.cache_dir / f"commessa_{commessa_id}_{self.INDEX_FILENAME}"
        return self.cache_dir / self.INDEX_FILENAME

    def _get_ids_path(self, commessa_id: int | None = None) -> Path:
        if commessa_id:
            return self.cache_dir / f"commessa_{commessa_id}_{self.IDS_FILENAME}"
        return self.cache_dir / self.IDS_FILENAME

    def build_index(
        self,
        items: list[tuple[int, list[float]]],  # (item_id, embedding)
        commessa_id: int | None = None,
    ) -> faiss.IndexIDMap:
        """Costruisce indice FAISS dagli item con embedding."""
        if not items:
            raise ValueError("Nessun item da indicizzare")

        # Estrai embeddings e ID
        ids = np.array([item[0] for item in items], dtype=np.int64)
        embeddings = np.array([item[1] for item in items], dtype=np.float32)

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        self._embedding_dim = embeddings.shape[1]

        # Normalizza per cosine similarity
        faiss.normalize_L2(embeddings)

        # Crea indice con Inner Product (= cosine similarity per vettori normalizzati)
        index_flat = faiss.IndexFlatIP(self._embedding_dim)
        index = faiss.IndexIDMap(index_flat)
        index.add_with_ids(embeddings, ids)

        # Salva indice
        index_path = self._get_index_path(commessa_id)
        faiss.write_index(index, str(index_path))

        # Salva mapping IDs
        ids_path = self._get_ids_path(commessa_id)
        np.save(str(ids_path), ids)

        self._index = index
        self._id_to_item = {int(id_): int(id_) for id_ in ids}

        logger.info(
            "Indice FAISS costruito: %d items, dim=%d, path=%s",
            len(items),
            self._embedding_dim,
            index_path,
        )

        return index

    def load_index(self, commessa_id: int | None = None) -> faiss.IndexIDMap | None:
        """Carica indice da disco se esiste."""
        index_path = self._get_index_path(commessa_id)
        ids_path = self._get_ids_path(commessa_id)

        if not index_path.exists():
            return None

        with self._index_lock:
            try:
                loaded = faiss.read_index(str(index_path))
                if not isinstance(loaded, faiss.IndexIDMap):
                    loaded = faiss.IndexIDMap(loaded)
                self._index = loaded
                self._embedding_dim = loaded.d

                # Carica mapping IDs
                if ids_path.exists():
                    ids = np.load(str(ids_path))
                    self._id_to_item = {int(id_): int(id_) for id_ in ids}

                logger.info("Indice FAISS caricato: %d items", loaded.ntotal)
                return self._index
            except Exception as exc:
                logger.warning("Errore caricamento indice FAISS: %s", exc)
                return None

    def search(
        self,
        query_vector: list[float] | np.ndarray,
        k: int = 50,
        commessa_id: int | None = None,
    ) -> list[tuple[int, float]]:
        """Cerca i k item più simili al vettore query.

        Returns:
            Lista di tuple (item_id, score) ordinate per score decrescente.
        """
        # Carica o usa indice esistente
        if self._index is None:
            self.load_index(commessa_id)

        if self._index is None:
            return []

        # Prepara query vector
        query_np = np.array(query_vector, dtype=np.float32)
        if query_np.ndim == 1:
            query_np = query_np.reshape(1, -1)

        # Verifica dimensione
        if query_np.shape[1] != self._embedding_dim:
            logger.warning(
                "Dimensione query (%d) != dimensione indice (%d)",
                query_np.shape[1],
                self._embedding_dim,
            )
            return []

        # Normalizza
        faiss.normalize_L2(query_np)

        # Cerca
        scores, ids = self._index.search(query_np, k)

        # Filtra risultati validi (ID != -1)
        results = [
            (int(item_id), float(score))
            for item_id, score in zip(ids[0], scores[0])
            if item_id != -1
        ]

        return results

    def index_exists(self, commessa_id: int | None = None) -> bool:
        """Verifica se esiste un indice salvato."""
        return self._get_index_path(commessa_id).exists()

    def delete_index(self, commessa_id: int | None = None) -> None:
        """Elimina indice salvato."""
        index_path = self._get_index_path(commessa_id)
        ids_path = self._get_ids_path(commessa_id)

        if index_path.exists():
            index_path.unlink()
        if ids_path.exists():
            ids_path.unlink()

        self._index = None
        self._id_to_item = {}


# Istanza globale del servizio
price_list_faiss_service = PriceListFaissService()


__all__ = [
    "SemanticEmbeddingService",
    "semantic_embedding_service",
    "DocumentFaissPipeline",
    "document_faiss_pipeline",
    "PriceListFaissService",
    "price_list_faiss_service",
]
