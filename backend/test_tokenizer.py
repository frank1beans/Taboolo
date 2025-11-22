"""Test tokenizer per verificare se funziona correttamente."""
from __future__ import annotations

import logging
from app.services.nlp import semantic_embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Test tokenizer."""
    if not semantic_embedding_service.is_available():
        logger.error("Servizio embedding semantici non disponibile")
        return

    # Ensure model is loaded
    semantic_embedding_service._ensure_model()
    model = semantic_embedding_service._model
    tokenizer = getattr(model, "tokenizer", None)
    if tokenizer is None:
        logger.error("Il modello corrente non espone un tokenizer compatibile.")
        return

    test_texts = [
        "cartongesso",
        "porta",
        "test123xyz",
    ]

    logger.info("Test tokenizzazione:")
    for text in test_texts:
        tokens = tokenizer.encode(text, add_special_tokens=True)
        decoded = tokenizer.decode(tokens)
        logger.info(f"\nText: '{text}'")
        logger.info(f"  Tokens: {tokens}")
        logger.info(f"  Decoded: '{decoded}'")
        logger.info(f"  Token count: {len(tokens)}")


if __name__ == "__main__":
    main()
