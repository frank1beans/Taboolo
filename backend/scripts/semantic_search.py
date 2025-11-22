from __future__ import annotations

"""Utility CLI per interrogare l'indice FAISS dei documenti."""

import sys
from pathlib import Path

import faiss

CURRENT_DIR = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_DIR.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.services.nlp import DocumentFaissPipeline  # noqa: E402


pipeline = DocumentFaissPipeline()


def semantic_search(query: str, k: int = 10) -> list[dict[str, object]]:
    trimmed = query.strip()
    if not trimmed:
        return []
    return pipeline.semantic_search(trimmed, k)


def main() -> None:
    try:
        query = input("Query: ").strip()
    except EOFError:  # pragma: no cover - interactive only
        print("Nessuna query fornita.")
        return

    try:
        results = semantic_search(query)
    except Exception as exc:  # pragma: no cover - runtime diagnostics
        print(f"Errore nella ricerca semantica: {exc}")
        return

    if not results:
        print("Nessun risultato trovato.")
        return

    for item in results:
        similarity = item.get("similarity")
        similarity_str = f"{similarity:.4f}" if isinstance(similarity, float) else str(similarity)
        print(f"ID: {item['id']} | Similarity: {similarity_str} | Titolo: {item['titolo']}")


if __name__ == "__main__":
    main()
