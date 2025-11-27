import logging
import re
from typing import Any, Sequence

import numpy as np
from sqlalchemy import func, or_
from app.api.deps import DBSession
from app.db.models import Commessa, PriceListItem
from app.services.nlp import (
    extract_construction_attributes,
    price_list_faiss_service,
    semantic_embedding_service,
)
from app.services.serialization_service import (
    collect_price_list_offers,
    collect_project_quantities,
    serialize_price_list_item,
)

logger = logging.getLogger(__name__)


def tokenize_query(text: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", text.lower())
        if len(token) >= 4
    }


def lexical_boost(tokens: set[str], item: PriceListItem) -> float:
    if not tokens:
        return 0.0

    def _count_hits(value: str | None) -> int:
        if not value:
            return 0
        normalized = value.lower()
        return sum(1 for token in tokens if token in normalized)

    desc_hits = _count_hits(item.item_description) + _count_hits(item.item_code)
    wbs_hits = _count_hits(item.wbs6_description) + _count_hits(item.wbs7_description)
    bonus = 0.0
    if desc_hits:
        bonus += min(0.08, desc_hits * 0.02)
    if wbs_hits:
        bonus += min(0.05, wbs_hits * 0.02)
    return min(bonus, 0.12)


def attribute_boost(item_attrs: dict, query_attrs: dict) -> float:
    """Calcola boost per match attributi strutturati."""
    if not query_attrs or not item_attrs:
        return 0.0

    boost = 0.0
    # Match esatto su numero lastre
    if "num_lastre" in query_attrs and "num_lastre" in item_attrs:
        if query_attrs["num_lastre"] == item_attrs["num_lastre"]:
            boost += 0.15
        else:
            boost -= 0.1  # Penalità per mismatch

    # Match su tipo rivestimento
    if "tipo_rivestimento" in query_attrs and "tipo_rivestimento" in item_attrs:
        if query_attrs["tipo_rivestimento"] == item_attrs["tipo_rivestimento"]:
            boost += 0.1

    # Match su tipo lastra
    if "tipo_lastra" in query_attrs and "tipo_lastra" in item_attrs:
        if query_attrs["tipo_lastra"] == item_attrs["tipo_lastra"]:
            boost += 0.1

    # Match su spessore (con tolleranza)
    if "spessore_mm" in query_attrs and "spessore_mm" in item_attrs:
        diff = abs(query_attrs["spessore_mm"] - item_attrs["spessore_mm"])
        if diff == 0:
            boost += 0.1
        elif diff <= 5:
            boost += 0.05

    # Match su isolamento
    if "isolamento" in query_attrs and "isolamento" in item_attrs:
        if query_attrs["isolamento"] == item_attrs["isolamento"]:
            boost += 0.08

    return boost


def search_catalog(
    session: DBSession,
    query: str,
    commessa_id: int | None = None,
    top_k: int = 50,
    min_score: float = 0.2,
) -> list[dict[str, Any]]:
    trimmed_query = query.strip()
    if not trimmed_query:
        raise ValueError("La query di ricerca non può essere vuota.")
    
    lexical_tokens = tokenize_query(trimmed_query)
    query_attributes = extract_construction_attributes(trimmed_query)

    try:
        query_vector = semantic_embedding_service.embed_text(trimmed_query)
    except RuntimeError as exc:
        raise RuntimeError(f"Ricerca semantica non disponibile: {exc}") from exc

    if not query_vector:
        raise RuntimeError("Ricerca semantica non disponibile: embedding non valido.")

    results: list[tuple[float, PriceListItem, Commessa, dict[str, Any]]] = []

    # Prova ricerca FAISS (molto più veloce)
    faiss_results = []
    use_faiss = price_list_faiss_service.index_exists(commessa_id)

    if not use_faiss:
        # Costruisci indice FAISS al volo se non esiste
        logger.info("Costruzione indice FAISS per commessa_id=%s", commessa_id)
        db_query = (
            session.query(PriceListItem)
            .filter(PriceListItem.extra_metadata.isnot(None))
        )
        if commessa_id is not None:
            db_query = db_query.filter(PriceListItem.commessa_id == commessa_id)

        items_to_index: list[tuple[int, list[float]]] = []
        for item in db_query.all():
            metadata = item.extra_metadata or {}
            if not isinstance(metadata, dict):
                continue
            nlp_payload = metadata.get("nlp")
            if not isinstance(nlp_payload, dict):
                continue
            embedding_info = semantic_embedding_service.extract_embedding_payload(nlp_payload)
            if not isinstance(embedding_info, dict):
                continue
            vector = embedding_info.get("vector")
            if not isinstance(vector, list) or len(vector) != len(query_vector):
                continue
            model_id = embedding_info.get("model_id")
            if model_id and model_id != semantic_embedding_service.model_id:
                continue
            items_to_index.append((item.id, vector))

        if items_to_index:
            try:
                price_list_faiss_service.build_index(items_to_index, commessa_id)
                use_faiss = True
            except Exception as exc:
                logger.warning("Errore costruzione indice FAISS: %s", exc)

    if use_faiss:
        # Cerca con FAISS (O(log n) invece di O(n))
        faiss_results = price_list_faiss_service.search(
            query_vector,
            k=top_k * 2,  # Margine per filtraggio successivo
            commessa_id=commessa_id,
        )
        logger.info("FAISS search: %d risultati", len(faiss_results))

    if faiss_results:
        # Carica solo gli item trovati da FAISS
        item_ids = [item_id for item_id, _ in faiss_results]
        score_map = {item_id: score for item_id, score in faiss_results}

        items_query = (
            session.query(PriceListItem, Commessa)
            .join(Commessa, PriceListItem.commessa_id == Commessa.id)
            .filter(PriceListItem.id.in_(item_ids))
        )
        rows = items_query.all()

        for item, commessa in rows:
            score = score_map.get(item.id, 0.0)
            score += lexical_boost(lexical_tokens, item)

            # Boost per attributi strutturati (lastre, rivestimenti, ecc.)
            if query_attributes:
                metadata = item.extra_metadata or {}
                nlp_payload = metadata.get("nlp", {})
                embedding_info = semantic_embedding_service.extract_embedding_payload(nlp_payload) if isinstance(nlp_payload, dict) else {}
                item_attrs = embedding_info.get("attributes", {}) if isinstance(embedding_info, dict) else {}
                score += attribute_boost(item_attrs, query_attributes)

            if score < min_score:
                continue
            results.append((score, item, commessa, {"match_reason": "semantic"}))
    else:
        # Fallback: ricerca lineare (se FAISS fallisce)
        db_query = (
            session.query(PriceListItem, Commessa)
            .join(Commessa, PriceListItem.commessa_id == Commessa.id)
            .filter(PriceListItem.extra_metadata.isnot(None))
        )
        if commessa_id is not None:
            db_query = db_query.filter(PriceListItem.commessa_id == commessa_id)
        rows = db_query.all()

        valid_items: list[tuple[PriceListItem, Commessa, dict[str, Any], list[float]]] = []
        for item, commessa in rows:
            metadata = item.extra_metadata or {}
            if not isinstance(metadata, dict):
                continue
            nlp_payload = metadata.get("nlp")
            if not isinstance(nlp_payload, dict):
                continue
            embedding_info = semantic_embedding_service.extract_embedding_payload(nlp_payload)
            if not isinstance(embedding_info, dict):
                continue
            vector = embedding_info.get("vector")
            if not isinstance(vector, list) or len(vector) != len(query_vector):
                continue
            model_id = embedding_info.get("model_id")
            if model_id and model_id != semantic_embedding_service.model_id:
                continue
            valid_items.append((item, commessa, embedding_info, vector))

        if valid_items:
            query_np = np.array(query_vector, dtype=np.float32)
            vectors_np = np.array([v[3] for v in valid_items], dtype=np.float32)
            query_norm = query_np / (np.linalg.norm(query_np) + 1e-9)
            vectors_norms = np.linalg.norm(vectors_np, axis=1, keepdims=True) + 1e-9
            vectors_normalized = vectors_np / vectors_norms
            scores = np.dot(vectors_normalized, query_norm)
            scores = np.clip(scores, -1.0, 1.0)

            for i, (item, commessa, embedding_info, _) in enumerate(valid_items):
                score = float(scores[i])
                score += lexical_boost(lexical_tokens, item)

                # Boost per attributi strutturati
                if query_attributes:
                    item_attrs = embedding_info.get("attributes", {}) if isinstance(embedding_info, dict) else {}
                    score += attribute_boost(item_attrs, query_attributes)

                if score < min_score:
                    continue
                results.append((score, item, commessa, embedding_info))

    results.sort(key=lambda entry: entry[0], reverse=True)
    limited = results[:top_k]
    
    # Fallback lessicale se pochi risultati
    if not limited and lexical_tokens:
        normalized_text_cache: dict[int, str] = {}

        def _text_for_item(item: PriceListItem) -> str:
            cached = normalized_text_cache.get(item.id)
            if cached is not None:
                return cached
            parts = [
                (item.item_code or "").lower(),
                (item.item_description or "").lower(),
                (item.wbs6_code or "").lower(),
                (item.wbs6_description or "").lower(),
                (item.wbs7_code or "").lower(),
                (item.wbs7_description or "").lower(),
            ]
            text = " ".join(part for part in parts if part)
            normalized_text_cache[item.id] = text
            return text

        fallback_matches: list[tuple[float, PriceListItem, Commessa, dict[str, Any]]] = []
        # Nota: qui stiamo iterando su 'rows' che potrebbe essere vuoto se siamo entrati nel ramo FAISS
        # e FAISS non ha trovato nulla. Se siamo nel ramo FAISS, 'rows' contiene solo gli item trovati.
        # Se vogliamo fare fallback su tutto il DB, dovremmo rifare la query.
        # Per semplicità e performance, facciamo fallback solo se eravamo in modalità lineare
        # OPPURE se decidiamo di caricare tutto (costoso).
        # L'implementazione originale usava 'rows' che nel ramo FAISS era limitato.
        # Se FAISS fallisce, 'rows' è vuoto.
        # Se siamo qui e 'limited' è vuoto, significa che FAISS non ha trovato nulla sopra soglia.
        
        # Se use_faiss è True, 'rows' contiene solo i candidati FAISS.
        # Se vogliamo cercare su tutto, dobbiamo fare una nuova query.
        if use_faiss:
             # Ricarichiamo tutto per la ricerca lessicale (potrebbe essere pesante, ma è un fallback)
             # O forse meglio evitare se il DB è grande.
             # Manteniamo il comportamento "best effort" sui dati caricati se presenti,
             # altrimenti facciamo una query testuale standard su DB?
             # Per ora replichiamo la logica originale che usava 'rows'.
             pass
        
        # Se 'rows' è disponibile (ramo lineare o FAISS con risultati)
        if 'rows' in locals():
            for item, commessa in rows:
                haystack = _text_for_item(item)
                if not haystack:
                    continue
                if not all(token in haystack for token in lexical_tokens):
                    continue
                fallback_matches.append(
                    (
                        0.0,
                        item,
                        commessa,
                        {"match_reason": "lexical"},
                    )
                )
                if len(fallback_matches) >= top_k:
                    break
            if fallback_matches:
                limited = fallback_matches

    project_quantity_map = collect_project_quantities(session, commessa_id)
    offers_map = collect_price_list_offers(
        session, [item.id for _, item, _, _ in limited]
    )

    output = []
    for score, item, commessa, embedding_info in limited:
        serialized = serialize_price_list_item(
            item,
            commessa,
            offers_map.get(item.id),
            project_quantity_map,
        )
        serialized["score"] = round(score, 6)
        serialized["match_reason"] = (
            embedding_info.get("match_reason")
            if isinstance(embedding_info.get("match_reason"), str)
            else "semantic"
        )
        output.append(serialized)
    
    return output
