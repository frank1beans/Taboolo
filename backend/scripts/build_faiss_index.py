from __future__ import annotations

"""Script per costruire l'indice FAISS dei documenti PostgreSQL."""

import sys
from pathlib import Path

import faiss  # type: ignore

CURRENT_DIR = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_DIR.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.services.nlp import DocumentFaissPipeline  # noqa: E402


pipeline = DocumentFaissPipeline()


def main() -> int:
    try:
        documents = pipeline.load_documents()
    except Exception as exc:  # pragma: no cover - runtime diagnostics
        print(f"[ERRORE] Impossibile leggere i documenti: {exc}")
        return 1

    print(f"Documenti letti: {len(documents)}")

    try:
        model = pipeline.load_model()
        embeddings, ids = pipeline.generate_embeddings(documents, model)
        index = pipeline.build_index(embeddings, ids)
        pipeline.save_index(index)
    except Exception as exc:  # pragma: no cover - runtime diagnostics
        print(f"[ERRORE] Impossibile costruire l'indice: {exc}")
        return 1

    print(f"Vettori indicizzati: {index.ntotal}")
    print(f"Indice salvato in: {pipeline.index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
