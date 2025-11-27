from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.config import settings


def _lazy_import_category_inference():
    from robimb.inference.category import CategoryInference  # type: ignore

    return CategoryInference


@lru_cache(maxsize=1)
def _load_predictor(model_path: str | None):
    if not model_path:
        return None
    CategoryInference = _lazy_import_category_inference()
    try:
        predictor = CategoryInference(
            model_path,
            backend="auto",
            label_map_path=settings.wbs_label_map_path,
        )
        return predictor
    except Exception:  # pragma: no cover - robustezza
        return None


def predict_wbs(
    text: str,
    *,
    level: int = 6,
    top_k: int = 3,
    max_length: int = 320,
    return_scores: bool = True,
) -> List[Dict[str, Any]]:
    """
    Predice etichette WBS6/WBS7 usando il modello roBERTino configurato.

    Args:
        text: descrizione da classificare
        level: 6 o 7
        top_k: numero di predizioni da restituire
        max_length: lunghezza massima tokenizzata
        return_scores: include i punteggi

    Returns:
        Lista di dict {"label": ..., "score": ...}
    """
    model_path = settings.wbs6_model_path if level == 6 else settings.wbs7_model_path
    predictor = _load_predictor(str(model_path) if model_path else None)
    if predictor is None:
        return []
    try:
        results = predictor.predict(
            text,
            top_k=top_k,
            max_length=max_length,
            return_scores=return_scores,
        )
    except Exception:  # pragma: no cover
        return []
    return [result.to_dict() for result in results]


__all__ = ["predict_wbs"]
