"""Script di test per verificare diversità degli embedding."""
from __future__ import annotations

import logging
import numpy as np
from app.services.nlp import semantic_embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Test embedding diversità."""
    if not semantic_embedding_service.is_available():
        logger.error("Servizio embedding semantici non disponibile")
        return

    # Test con query molto diverse
    test_queries = [
        "cartongesso",
        "porta",
        "illuminazione LED",
        "test123xyz",
        "acqua potabile",
    ]

    logger.info("Generazione embeddings di test...")
    embeddings = semantic_embedding_service.embed_texts(test_queries)

    # Calcola similarità tra tutte le coppie
    logger.info("\nAnalisi similarità coseno tra query:")
    for i, query1 in enumerate(test_queries):
        for j, query2 in enumerate(test_queries):
            if i >= j:
                continue
            vec1 = np.array(embeddings[i])
            vec2 = np.array(embeddings[j])

            # Cosine similarity (vettori già normalizzati)
            similarity = float(np.dot(vec1, vec2))

            # Verifica normalizzazione
            norm1 = float(np.linalg.norm(vec1))
            norm2 = float(np.linalg.norm(vec2))

            logger.info(
                f"'{query1}' <-> '{query2}': {similarity:.6f} "
                f"(norm1={norm1:.6f}, norm2={norm2:.6f})"
            )

    # Analizza statistiche degli embeddings
    logger.info("\nStatistiche embeddings:")
    for i, query in enumerate(test_queries):
        vec = np.array(embeddings[i])
        mean = float(np.mean(vec))
        std = float(np.std(vec))
        min_val = float(np.min(vec))
        max_val = float(np.max(vec))
        logger.info(
            f"'{query}': mean={mean:.6f}, std={std:.6f}, "
            f"min={min_val:.6f}, max={max_val:.6f}"
        )


if __name__ == "__main__":
    main()
