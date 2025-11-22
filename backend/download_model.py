"""Script per scaricare completamente un modello SentenceTransformer."""
from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from transformers import AutoModel, AutoTokenizer
except ImportError:  # pragma: no cover - utility script
    logger.error("transformers non disponibile. Installa 'transformers' per eseguire questo script.")
    raise SystemExit(1) from None


MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CACHE_DIR = Path(__file__).parent / "storage" / "models" / "semantic"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    logger.info("Download modello %s", MODEL_ID)
    logger.info("Cache dir: %s", CACHE_DIR)

    logger.info("Scarico il tokenizer...")
    AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=str(CACHE_DIR))
    logger.info("Tokenizer scaricato.")

    logger.info("Scarico i pesi del modello...")
    AutoModel.from_pretrained(MODEL_ID, cache_dir=str(CACHE_DIR))
    logger.info("Modello scaricato.")

    logger.info("Download completato!")


if __name__ == "__main__":
    main()
