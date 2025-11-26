import json
import math
import re
from typing import Any, List, Sequence

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from sqlalchemy import func, or_

from app.api.deps import DBSession, get_current_user, require_role, UserRole
from app.core import settings
from app.core.security import SlidingWindowRateLimiter, enforce_rate_limit
from app.db.models import (
    Commessa,
    CommessaPreferences,
    CommessaPreferencesBase,
    CommessaPreferencesRead,
    Computo,
    ComputoTipo,
    PriceListItem,
    PriceListOffer,
    User,
)
from app.db.models_wbs import Voce as VoceNorm, VoceProgetto
from app.schemas import (
    AnalisiCommessaSchema,
    AnalisiWBS6TrendSchema,
    CommessaCreate,
    CommessaDetailSchema,
    CommessaWbsSchema,
    CommessaSchema,
    ComputoSchema,
    ImportBatchSingleFileResultSchema,
    ConfrontoOfferteSchema,
    HeatmapCompetitivitaSchema,
    ManualPriceUpdateRequest,
    ManualPriceUpdateResponse,
    PriceListItemSchema,
    PriceListOfferSchema,
    PriceListItemSearchResultSchema,
    PriceCatalogSummarySchema,
    SixImportReportSchema,
    SixInspectionSchema,
    SixPreventiviPreviewSchema,
    SixPreventivoOptionSchema,
    TrendEvoluzioneSchema,
    Wbs6NodeSchema,
    Wbs7NodeSchema,
    WbsImportStatsSchema,
    WbsSpazialeSchema,
    WbsVisibilitySchema,
    WbsVisibilityUpdateSchema,
)
from app.services import (
    CommesseService,
    InsightsService,
    PreventivoSelectionError,
    semantic_embedding_service,
    price_list_faiss_service,
    WbsImportService,
    WbsVisibilityService,
    import_service,
    six_import_service,
    storage_service,
    record_audit_log,
    commessa_bundle_service,
)
from app.services.nlp import extract_construction_attributes

router = APIRouter(
    dependencies=[
        require_role(
            [UserRole.viewer, UserRole.computista, UserRole.project_manager, UserRole.admin]
        )
    ]
)
write_guard = require_role([UserRole.computista, UserRole.project_manager, UserRole.admin])
admin_guard = require_role([UserRole.project_manager, UserRole.admin])
admin_only_guard = require_role([UserRole.admin])
import_rate_limiter = SlidingWindowRateLimiter(
    settings.import_rate_limit_per_minute, 60
)


def _serialize_price_list_item(
    item: PriceListItem,
    commessa: Commessa,
    offers: Sequence[PriceListOffer] | None = None,
    project_quantities: dict[int, float] | None = None,
) -> dict[str, Any]:
    wbs6_code = item.wbs6_code
    wbs6_description = item.wbs6_description
    wbs7_code = item.wbs7_code
    wbs7_description = item.wbs7_description

    if not wbs6_code:
        try:
            from app.services.wbs_predictor import predict_wbs

            base_text = item.item_description or item.item_code or item.product_id or ""
            preds6 = predict_wbs(base_text, level=6, top_k=1)
            if preds6:
                wbs6_code = preds6[0].get("label")
                wbs6_description = wbs6_description or wbs6_code
            preds7 = predict_wbs(base_text, level=7, top_k=1)
            if preds7:
                wbs7_code = preds7[0].get("label")
                wbs7_description = wbs7_description or wbs7_code
        except Exception:
            pass

    payload = {
        "id": item.id,
        "commessa_id": commessa.id,
        "commessa_nome": commessa.nome,
        "commessa_codice": commessa.codice,
        "business_unit": commessa.business_unit,
        "product_id": item.product_id,
        "item_code": item.item_code,
        "item_description": item.item_description,
        "unit_id": item.unit_id,
        "unit_label": item.unit_label,
        "wbs6_code": wbs6_code,
        "wbs6_description": wbs6_description,
        "wbs7_code": wbs7_code,
        "wbs7_description": wbs7_description,
        "price_lists": item.price_lists,
        "extra_metadata": item.extra_metadata,
        "source_file": item.source_file,
        "preventivo_id": item.preventivo_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
    project_price = None
    project_quantity = (
        project_quantities.get(item.id) if project_quantities else None
    )
    offer_prices: dict[str, dict[str, Any]] = {}
    serialized_offers: list[dict[str, Any]] = []
    if offers:
        for offer in offers:
            serialized = _serialize_price_list_offer(offer)
            serialized_offers.append(serialized)
            label = (offer.impresa_label or "").strip() or "Offerta"
            key = label if offer.round_number in (None, 0) else f"{label} (Round {offer.round_number})"
            if label.lower() == "progetto":
                project_price = offer.prezzo_unitario
                project_quantity = offer.quantita
            else:
                offer_prices[key] = {
                    "price": offer.prezzo_unitario,
                    "quantity": offer.quantita,
                    "round_number": offer.round_number,
                    "computo_id": offer.computo_id,
                }
    payload["offers"] = serialized_offers
    if (
        project_quantities
        and project_quantities.get(item.id) is not None
    ):
        project_quantity = project_quantities[item.id]
    if project_price is None:
        price_lists = item.price_lists or {}
        if price_lists:
            try:
                project_price = next(iter(price_lists.values()))
            except StopIteration:
                project_price = None
    payload["project_price"] = project_price
    payload["project_quantity"] = project_quantity
    payload["offer_prices"] = offer_prices
    return payload


def _serialize_price_list_offer(offer: PriceListOffer) -> dict[str, Any]:
    return {
        "id": offer.id,
        "price_list_item_id": offer.price_list_item_id,
        "computo_id": offer.computo_id,
        "impresa_id": offer.impresa_id,
        "impresa_label": offer.impresa_label,
        "round_number": offer.round_number,
        "prezzo_unitario": offer.prezzo_unitario,
        "quantita": offer.quantita,
        "created_at": offer.created_at,
        "updated_at": offer.updated_at,
    }


def _collect_price_list_offers(
    session: DBSession, item_ids: Sequence[int]
) -> dict[int, list[PriceListOffer]]:
    if not item_ids:
        return {}
    rows = (
        session.query(PriceListOffer)
        .filter(PriceListOffer.price_list_item_id.in_(item_ids))
        .order_by(
            PriceListOffer.round_number.asc(),
            PriceListOffer.impresa_label.asc(),
            PriceListOffer.updated_at.desc(),
        )
        .all()
    )
    offers_map: dict[int, list[PriceListOffer]] = {}
    for offer in rows:
        offers_map.setdefault(offer.price_list_item_id, []).append(offer)
    return offers_map


def _collect_project_quantities(
    session: DBSession, commessa_id: int | None = None
) -> dict[int, float]:
    rows = (
        session.query(
            VoceNorm.price_list_item_id,
            func.sum(VoceProgetto.quantita),
        )
        .join(VoceProgetto, VoceProgetto.voce_id == VoceNorm.id)
        .join(Computo, VoceProgetto.computo_id == Computo.id)
        .filter(
            VoceNorm.price_list_item_id.isnot(None),
            Computo.tipo == ComputoTipo.progetto,
        )
    )
    if commessa_id is not None:
        rows = rows.filter(Computo.commessa_id == commessa_id)
    rows = rows.group_by(VoceNorm.price_list_item_id).all()
    quantities: dict[int, float] = {}
    for item_id, quantity in rows:
        if item_id is None:
            continue
        quantities[item_id] = float(quantity or 0.0)
    return quantities


def _tokenize_query(text: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", text.lower())
        if len(token) >= 4
    }


def _lexical_boost(tokens: set[str], item: PriceListItem) -> float:
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


def _parse_column_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    text = raw_value.strip()
    if not text:
        return []
    values: list[str] = []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, list):
        source = payload
    else:
        source = text.split(",")
    for item in source:
        if item is None:
            continue
        normalized = str(item).strip().lstrip("$").upper()
        if normalized and normalized not in values:
            values.append(normalized)
    return values


def _get_commessa_or_404(session: DBSession, commessa_id: int):
    commessa = CommesseService.get_commessa(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )
    return commessa


def _ensure_excel_file(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Usa un file Excel (.xlsx, .xlsm, .xls)",
        )


def _ensure_six_or_xml_file(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith((".six", ".xml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Fornisci un file STR Vision (.six o .xml)",
        )


@router.get("/", response_model=List[CommessaSchema])
def list_commesse(session: DBSession) -> List[CommessaSchema]:
    commesse = CommesseService.list_commesse(session)
    return commesse


@router.post(
    "/",
    response_model=CommessaSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_guard],
)
def create_commessa(payload: CommessaCreate, session: DBSession) -> CommessaSchema:
    return CommesseService.create_commessa(session, payload)


@router.post(
    "/import-bundle",
    response_model=CommessaSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[admin_only_guard],
)
async def import_commessa_bundle(
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
    overwrite: bool = Query(
        False,
        description="Sovrascrive la commessa esistente con lo stesso codice, se presente.",
    ),
    current_user: User = Depends(get_current_user),
) -> CommessaSchema:
    if not commessa_bundle_service.is_bundle_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato pacchetto non supportato. Carica un file .mmcomm.",
        )
    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    try:
        commessa = commessa_bundle_service.import_bundle_from_upload(
            session, file, overwrite=overwrite
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    record_audit_log(
        session,
        user_id=current_user.id,
        action="IMPORT_COMMESSA_BUNDLE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        payload=file.filename,
        outcome="success",
    )
    return CommessaSchema.model_validate(commessa)


# ============================================================================
# GLOBAL PRICE CATALOG ROUTES
# IMPORTANT: These routes MUST be defined BEFORE any route with {commessa_id}
# to avoid FastAPI matching "price-catalog" as a commessa_id parameter
# ============================================================================

@router.get("/price-catalog", response_model=list[PriceListItemSchema])
def list_price_catalog(
    session: DBSession,
    search: str | None = Query(
        default=None,
        description="Filtro testuale su codice, descrizione e WBS.",
        min_length=1,
    ),
    commessa_id: int | None = Query(
        default=None, description="Limita i risultati alla commessa indicata."
    ),
    business_unit: str | None = Query(
        default=None, description="Filtra per Business Unit esatta."
    ),
) -> list[PriceListItemSchema]:
    """Elenco prezzi aggregato di tutte le commesse."""
    from app.db.models import PriceListItem, Commessa

    query = (
        session.query(PriceListItem, Commessa)
        .join(Commessa, PriceListItem.commessa_id == Commessa.id)
        .order_by(
            Commessa.business_unit.nulls_last(),
            Commessa.codice,
            PriceListItem.wbs6_code,
            PriceListItem.item_code,
        )
    )

    if commessa_id is not None:
        query = query.filter(PriceListItem.commessa_id == commessa_id)

    if business_unit:
        normalized_bu = business_unit.strip().lower()
        if normalized_bu:
            query = query.filter(
                func.lower(func.coalesce(Commessa.business_unit, "")) == normalized_bu
            )

    if search:
        normalized = f"%{search.strip().lower()}%"
        if normalized.strip("%"):
            query = query.filter(
                or_(
                    func.lower(PriceListItem.item_code).like(normalized),
                    func.lower(func.coalesce(PriceListItem.item_description, "")).like(
                        normalized
                    ),
                    func.lower(func.coalesce(PriceListItem.wbs6_code, "")).like(
                        normalized
                    ),
                    func.lower(func.coalesce(PriceListItem.wbs6_description, "")).like(
                        normalized
                    ),
                    func.lower(func.coalesce(PriceListItem.wbs7_code, "")).like(
                        normalized
                    ),
                    func.lower(func.coalesce(PriceListItem.wbs7_description, "")).like(
                        normalized
                    ),
                )
            )
    rows = query.all()
    project_quantity_map = _collect_project_quantities(session, commessa_id)
    offers_map = _collect_price_list_offers(session, [item.id for item, _ in rows])

    return [
        PriceListItemSchema(
            **_serialize_price_list_item(
                item,
                commessa,
                offers_map.get(item.id),
                project_quantity_map,
            )
        )
        for item, commessa in rows
    ]


@router.get(
    "/price-catalog/semantic-search",
    response_model=list[PriceListItemSearchResultSchema],
)
def semantic_search_price_catalog(
    session: DBSession,
    query: str = Query(
        ..., description="Testo da cercare nel catalogo prezzi", min_length=2
    ),
    commessa_id: int | None = Query(
        default=None,
        description="Limita la ricerca alla commessa indicata.",
    ),
    top_k: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Numero massimo di risultati da restituire.",
    ),
    min_score: float = Query(
        default=0.2,
        ge=-1.0,
        le=1.0,
        description="Soglia minima di similarità coseno per mostrare una voce.",
    ),
) -> list[PriceListItemSearchResultSchema]:
    trimmed_query = query.strip()
    if not trimmed_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La query di ricerca non può essere vuota.",
        )
    lexical_tokens = _tokenize_query(trimmed_query)

    # Estrai attributi strutturati dalla query per ricerca ibrida
    query_attributes = extract_construction_attributes(trimmed_query)

    try:
        query_vector = semantic_embedding_service.embed_text(trimmed_query)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ricerca semantica non disponibile: {exc}",
        ) from exc

    if not query_vector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ricerca semantica non disponibile: embedding non valido.",
        )

    import logging
    logger = logging.getLogger(__name__)

    def _attribute_boost(item_attrs: dict, query_attrs: dict) -> float:
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

    results: list[
        tuple[float, PriceListItem, Commessa, dict[str, Any]]
    ] = []

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
            score += _lexical_boost(lexical_tokens, item)

            # Boost per attributi strutturati (lastre, rivestimenti, ecc.)
            if query_attributes:
                metadata = item.extra_metadata or {}
                nlp_payload = metadata.get("nlp", {})
                embedding_info = semantic_embedding_service.extract_embedding_payload(nlp_payload) if isinstance(nlp_payload, dict) else {}
                item_attrs = embedding_info.get("attributes", {}) if isinstance(embedding_info, dict) else {}
                score += _attribute_boost(item_attrs, query_attributes)

            if score < min_score:
                continue
            results.append((score, item, commessa, {"match_reason": "semantic"}))
    else:
        # Fallback: ricerca lineare (se FAISS fallisce)
        import numpy as np

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
                score += _lexical_boost(lexical_tokens, item)

                # Boost per attributi strutturati
                if query_attributes:
                    item_attrs = embedding_info.get("attributes", {}) if isinstance(embedding_info, dict) else {}
                    score += _attribute_boost(item_attrs, query_attributes)

                if score < min_score:
                    continue
                results.append((score, item, commessa, embedding_info))

    results.sort(key=lambda entry: entry[0], reverse=True)
    limited = results[:top_k]
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

    project_quantity_map = _collect_project_quantities(session, commessa_id)
    offers_map = _collect_price_list_offers(
        session, [item.id for _, item, _, _ in limited]
    )

    return [
        PriceListItemSearchResultSchema(
            **_serialize_price_list_item(
                item,
                commessa,
                offers_map.get(item.id),
                project_quantity_map,
            ),
            score=round(score, 6),
            match_reason=embedding_info.get("match_reason")
            if isinstance(embedding_info.get("match_reason"), str)
            else "semantic",
        )
        for score, item, commessa, embedding_info in limited
    ]


@router.get("/price-catalog/summary", response_model=PriceCatalogSummarySchema)
def list_price_catalog_summary(session: DBSession) -> PriceCatalogSummarySchema:
    """Riepilogo del catalogo prezzi raggruppato per business unit e commessa."""
    from app.db.models import PriceListItem, Commessa

    rows = (
        session.query(
            Commessa.id,
            Commessa.nome,
            Commessa.codice,
            Commessa.business_unit,
            func.count(PriceListItem.id),
            func.max(PriceListItem.updated_at),
        )
        .join(PriceListItem, PriceListItem.commessa_id == Commessa.id)
        .group_by(Commessa.id)
        .all()
    )

    business_units: dict[str, dict] = {}
    total_items = 0

    for (
        commessa_id,
        nome,
        codice,
        business_unit,
        items_count,
        last_updated,
    ) in rows:
        key = (business_unit or "").strip() or "__none__"
        if key not in business_units:
            business_units[key] = {
                "label": business_unit or "Senza Business Unit",
                "value": business_unit or None,
                "items_count": 0,
                "commesse": [],
            }
        business_units[key]["items_count"] += items_count
        total_items += items_count
        business_units[key]["commesse"].append(
            {
                "commessa_id": commessa_id,
                "commessa_nome": nome,
                "commessa_codice": codice,
                "business_unit": business_unit or None,
                "items_count": items_count,
                "last_updated": last_updated,
            }
        )

    business_unit_list = []
    for entry in sorted(
        business_units.values(),
        key=lambda item: (item["value"] or "").lower(),
    ):
        commesse = sorted(
            entry["commesse"],
            key=lambda comm: comm["commessa_nome"].lower(),
        )
        business_unit_list.append(
            {
                "label": entry["label"],
                "value": entry["value"],
                "items_count": entry["items_count"],
                "commesse": commesse,
            }
        )

    return PriceCatalogSummarySchema(
        total_items=total_items,
        total_commesse=len(rows),
        business_units=business_unit_list,
    )


# ============================================================================
# COMMESSA-SPECIFIC ROUTES
# Routes below use {commessa_id} parameter
# ============================================================================

@router.delete("/{commessa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commessa(commessa_id: int, session: DBSession):
    deleted = CommesseService.delete_commessa(session, commessa_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )


@router.put("/{commessa_id}", response_model=CommessaSchema)
def update_commessa(commessa_id: int, payload: CommessaCreate, session: DBSession) -> CommessaSchema:
    updated = CommesseService.update_commessa(session, commessa_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )
    return updated

@router.get("/{commessa_id}", response_model=CommessaDetailSchema)
def get_commessa(commessa_id: int, session: DBSession) -> CommessaDetailSchema:
    commessa, computi = CommesseService.get_commessa_with_computi(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )
    return CommessaDetailSchema(
        id=commessa.id,
        nome=commessa.nome,
        codice=commessa.codice,
        descrizione=commessa.descrizione,
        note=commessa.note,
        business_unit=commessa.business_unit,
        revisione=commessa.revisione,
        stato=commessa.stato,
        created_at=commessa.created_at,
        updated_at=commessa.updated_at,
        computi=[ComputoSchema.model_validate(c) for c in computi],
    )


@router.get(
    "/{commessa_id}/bundle",
    response_class=FileResponse,
    dependencies=[admin_only_guard],
)
def export_commessa_bundle(
    commessa_id: int,
    session: DBSession,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    try:
        bundle_path = commessa_bundle_service.export_commessa(session, commessa_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    client_ip = request.client.host if request.client else "anonymous"
    record_audit_log(
        session,
        user_id=current_user.id,
        action="EXPORT_COMMESSA_BUNDLE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="GET",
        payload=bundle_path.name,
        outcome="success",
    )
    return FileResponse(
        bundle_path,
        media_type="application/octet-stream",
        filename=bundle_path.name,
    )


@router.get("/{commessa_id}/wbs", response_model=CommessaWbsSchema)
def get_commessa_wbs(commessa_id: int, session: DBSession) -> CommessaWbsSchema:
    commessa = _get_commessa_or_404(session, commessa_id)
    spaziali, wbs6_nodes, wbs7_nodes = WbsImportService.fetch_commessa_wbs(
        session, commessa.id
    )
    return CommessaWbsSchema(
        commessa_id=commessa.id,
        spaziali=[WbsSpazialeSchema.model_validate(node) for node in spaziali],
        wbs6=[Wbs6NodeSchema.model_validate(node) for node in wbs6_nodes],
        wbs7=[Wbs7NodeSchema.model_validate(node) for node in wbs7_nodes],
    )


@router.post(
    "/{commessa_id}/wbs/upload",
    response_model=WbsImportStatsSchema,
    status_code=status.HTTP_201_CREATED,
)
async def upload_wbs_structure(
    commessa_id: int,
    session: DBSession,
    file: UploadFile = File(...),
) -> WbsImportStatsSchema:
    commessa = _get_commessa_or_404(session, commessa_id)
    _ensure_excel_file(file)
    payload = await file.read()
    try:
        stats = WbsImportService.import_from_upload(
            session,
            commessa,
            file_bytes=payload,
            mode="create",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return WbsImportStatsSchema(**stats.__dict__)


@router.put(
    "/{commessa_id}/wbs/upload",
    response_model=WbsImportStatsSchema,
)
async def update_wbs_structure(
    commessa_id: int,
    session: DBSession,
    file: UploadFile = File(...),
) -> WbsImportStatsSchema:
    commessa = _get_commessa_or_404(session, commessa_id)
    _ensure_excel_file(file)
    payload = await file.read()
    try:
        stats = WbsImportService.import_from_upload(
            session,
            commessa,
            file_bytes=payload,
            mode="update",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return WbsImportStatsSchema(**stats.__dict__)


@router.get(
    "/{commessa_id}/wbs/visibility",
    response_model=List[WbsVisibilitySchema],
)
def list_wbs_visibility(commessa_id: int, session: DBSession) -> List[WbsVisibilitySchema]:
    _ = _get_commessa_or_404(session, commessa_id)
    entries = WbsVisibilityService.list_visibility(session, commessa_id)
    return [
        WbsVisibilitySchema(
            level=entry.level,
            node_id=entry.node_id,
            code=entry.code,
            description=entry.description,
            hidden=entry.hidden,
        )
        for entry in entries
    ]


@router.put(
    "/{commessa_id}/wbs/visibility",
    response_model=List[WbsVisibilitySchema],
)
def update_wbs_visibility(
    commessa_id: int,
    session: DBSession,
    payload: List[WbsVisibilityUpdateSchema] = Body(default=[]),
) -> List[WbsVisibilitySchema]:
    _ = _get_commessa_or_404(session, commessa_id)
    updates = [(item.level, item.node_id, item.hidden) for item in payload]
    try:
        entries = WbsVisibilityService.update_visibility(session, commessa_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return [
        WbsVisibilitySchema(
            level=entry.level,
            node_id=entry.node_id,
            code=entry.code,
            description=entry.description,
            hidden=entry.hidden,
        )
        for entry in entries
    ]


@router.post(
    "/{commessa_id}/import-six/inspect",
    response_model=SixInspectionSchema,
    dependencies=[write_guard],
)
async def inspect_commessa_six(
    commessa_id: int,
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
) -> SixInspectionSchema:
    _ = _get_commessa_or_404(session, commessa_id)
    _ensure_six_or_xml_file(file)
    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    payload = await file.read()
    if len(payload) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File troppo grande",
        )
    try:
        result = six_import_service.inspect_details(payload, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SixInspectionSchema(**result)


@router.post(
    "/{commessa_id}/import-six/preview",
    response_model=SixPreventiviPreviewSchema,
    dependencies=[write_guard],
)
async def preview_commessa_six(
    commessa_id: int,
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
) -> SixPreventiviPreviewSchema:
    _ = _get_commessa_or_404(session, commessa_id)
    _ensure_six_or_xml_file(file)
    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    payload = await file.read()
    if len(payload) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File troppo grande",
        )
    try:
        options = six_import_service.inspect_content(payload, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SixPreventiviPreviewSchema(
        preventivi=[
            SixPreventivoOptionSchema(
                internal_id=opt.internal_id,
                code=opt.code,
                description=opt.description,
                author=opt.author,
                version=opt.version,
                date=opt.date,
                price_list_id=opt.price_list_id,
                price_list_label=opt.price_list_label,
                rilevazioni=opt.rilevazioni,
                items=opt.items,
                total_importo=opt.total_importo,
            )
            for opt in options
        ]
    )


@router.post(
    "/{commessa_id}/import-six",
    response_model=SixImportReportSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_guard],
)
async def import_commessa_six(
    commessa_id: int,
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
    preventivo_id: str | None = Form(default=None),
    compute_embeddings: bool = Form(default=False),
    extract_properties: bool = Form(default=False),
) -> SixImportReportSchema:
    _ = _get_commessa_or_404(session, commessa_id)
    _ensure_six_or_xml_file(file)
    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    saved_result = storage_service.save_upload(commessa_id, file)
    saved_path = saved_result.path
    try:
        report = six_import_service.import_six_file(
            session,
            commessa_id,
            saved_path,
            preventivo_id=preventivo_id,
            compute_embeddings=compute_embeddings,
            extract_properties=extract_properties,
        )
    except PreventivoSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(exc),
                "preventivi": [
                    SixPreventivoOptionSchema(
                        internal_id=opt.internal_id,
                        code=opt.code,
                        description=opt.description,
                    ).model_dump()
                    for opt in exc.options
                ],
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    record_audit_log(
        session,
        user_id=None,
        action="IMPORT_FILE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        payload=saved_result.sha256,
        outcome="success",
    )
    return SixImportReportSchema(**report)


@router.get("/{commessa_id}/confronto", response_model=ConfrontoOfferteSchema)
def get_commessa_confronto(commessa_id: int, session: DBSession) -> ConfrontoOfferteSchema:
    try:
        return InsightsService.get_commessa_confronto(session, commessa_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{commessa_id}/price-catalog", response_model=list[PriceListItemSchema])
def get_commessa_price_catalog(
    commessa_id: int,
    session: DBSession,
    used_only: bool = Query(
        False,
        description="Se true, restituisce solo le voci realmente utilizzate nel computo progetto della commessa.",
    ),
) -> list[PriceListItemSchema]:
    """Recupera l'elenco prezzi associato alla commessa."""
    from app.db.models import PriceListItem, Computo, VoceComputo, ComputoTipo

    commessa = _get_commessa_or_404(session, commessa_id)
    query = session.query(PriceListItem).filter(PriceListItem.commessa_id == commessa.id)

    if used_only:
        query = (
            query.join(
                Computo,
                (Computo.commessa_id == PriceListItem.commessa_id)
                & (Computo.tipo == ComputoTipo.progetto),
            )
            .join(
                VoceComputo,
                (VoceComputo.computo_id == Computo.id)
                & (VoceComputo.global_code == PriceListItem.global_code),
            )
            .distinct()
        )

    items = query.order_by(
        PriceListItem.wbs6_code,
        PriceListItem.wbs7_code,
        PriceListItem.item_code,
    ).all()

    offers_map = _collect_price_list_offers(session, [item.id for item in items])
    project_quantity_map = _collect_project_quantities(session, commessa.id)

    return [
        PriceListItemSchema(
            **_serialize_price_list_item(
                item,
                commessa,
                offers_map.get(item.id),
                project_quantity_map,
            )
        )
        for item in items
    ]


@router.get("/{commessa_id}/analisi", response_model=AnalisiCommessaSchema)
def get_commessa_analisi(
    commessa_id: int,
    session: DBSession,
    round_number: int | None = Query(default=None),
    impresa: str | None = Query(default=None),
) -> AnalisiCommessaSchema:
    commessa = _get_commessa_or_404(session, commessa_id)
    try:
        result = InsightsService.get_commessa_analisi(
            session, commessa.id, round_number=round_number, impresa=impresa
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{commessa_id}/analisi/wbs6/{wbs6_id}",
    response_model=AnalisiWBS6TrendSchema,
)
def get_commessa_wbs6_dettaglio(
    commessa_id: int,
    wbs6_id: str,
    session: DBSession,
    round_number: int | None = Query(default=None),
    impresa: str | None = Query(default=None),
) -> AnalisiWBS6TrendSchema:
    try:
        return InsightsService.get_commessa_wbs6_dettaglio(
            session,
            commessa_id,
            wbs6_id,
            round_number=round_number,
            impresa=impresa,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{commessa_id}/analisi/trend-round", response_model=TrendEvoluzioneSchema)
def get_commessa_trend_round(
    commessa_id: int,
    session: DBSession,
    impresa: str | None = Query(default=None),
) -> TrendEvoluzioneSchema:
    """Ottiene i dati per il grafico Trend Evoluzione Prezzi tra Round."""
    commessa = _get_commessa_or_404(session, commessa_id)
    try:
        result = InsightsService.get_commessa_trend_round(
            session, commessa.id, impresa=impresa
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{commessa_id}/analisi/heatmap-competitivita", response_model=HeatmapCompetitivitaSchema)
def get_commessa_heatmap_competitivita(
    commessa_id: int,
    session: DBSession,
    round_number: int | None = Query(default=None),
) -> HeatmapCompetitivitaSchema:
    """Ottiene i dati per il grafico Heatmap Competitività."""
    commessa = _get_commessa_or_404(session, commessa_id)
    try:
        result = InsightsService.get_commessa_heatmap_competitivita(
            session, commessa.id, round_number=round_number
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{commessa_id}/computo-progetto",
    status_code=status.HTTP_201_CREATED,
    response_model=ComputoSchema,
    dependencies=[write_guard],
)
async def upload_computo_progetto(
    commessa_id: int,
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
) -> ComputoSchema:
    commessa = CommesseService.get_commessa(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )

    if not file.filename or not file.filename.lower().endswith(
        (".xlsx", ".xlsm", ".xls")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Usa un file Excel (.xlsx, .xlsm, .xls)",
        )

    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    saved_result = storage_service.save_upload(commessa_id, file)
    saved_path = saved_result.path

    try:
        computo = import_service.import_computo_progetto(
            session=session,
            commessa_id=commessa_id,
            file=saved_path,
            originale_nome=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    record_audit_log(
        session,
        user_id=None,
        action="IMPORT_FILE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        payload=saved_result.sha256,
        outcome="success",
    )
    return ComputoSchema.model_validate(computo)


@router.post(
    "/{commessa_id}/ritorni",
    status_code=status.HTTP_201_CREATED,
    response_model=ComputoSchema,
    dependencies=[write_guard],
)
async def upload_ritorno_gara(
    commessa_id: int,
    request: Request,
    session: DBSession,
    impresa: str = Form(..., min_length=1),
    round_mode: str = Form("auto"),
    round_number: int | None = Form(default=None),
    sheet_name: str | None = Form(default=None),
    code_columns: str | None = Form(default=None),
    description_columns: str | None = Form(default=None),
    price_column: str | None = Form(default=None),
    quantity_column: str | None = Form(default=None),
    progressive_column: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> ComputoSchema:
    commessa = CommesseService.get_commessa(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )

    if not file.filename or not file.filename.lower().endswith(
        (".xlsx", ".xlsm", ".xls")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Usa un file Excel (.xlsx, .xlsm, .xls)",
        )

    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    saved_result = storage_service.save_upload(commessa_id, file)
    saved_path = saved_result.path

    parsed_code_columns = _parse_column_list(code_columns)
    parsed_description_columns = _parse_column_list(description_columns)
    normalized_price_column = (
        price_column.strip().lstrip("$").upper()
        if price_column and price_column.strip()
        else None
    )
    normalized_quantity_column = (
        quantity_column.strip().lstrip("$").upper()
        if quantity_column and quantity_column.strip()
        else None
    )
    normalized_progressive_column = (
        progressive_column.strip().lstrip("$").upper()
        if progressive_column and progressive_column.strip()
        else None
    )
    sheet_name_value = sheet_name.strip() if sheet_name and sheet_name.strip() else None

    try:
        computo = import_service.import_computo_ritorno(
            session=session,
            commessa_id=commessa_id,
            impresa=impresa,
            file=saved_path,
            originale_nome=file.filename,
            round_number=round_number,
            round_mode=round_mode,
            sheet_name=sheet_name_value,
            sheet_code_columns=parsed_code_columns,
            sheet_description_columns=parsed_description_columns,
            sheet_price_column=normalized_price_column,
            sheet_quantity_column=normalized_quantity_column,
            sheet_progressive_column=normalized_progressive_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    record_audit_log(
        session,
        user_id=None,
        action="IMPORT_FILE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        payload=saved_result.sha256,
        outcome="success",
    )
    return ComputoSchema.model_validate(computo)


@router.post(
    "/{commessa_id}/ritorni/batch-single-file",
    status_code=status.HTTP_201_CREATED,
    response_model=ImportBatchSingleFileResultSchema,
    dependencies=[write_guard],
)
async def upload_ritorni_batch_single_file(
    commessa_id: int,
    request: Request,
    session: DBSession,
    file: UploadFile = File(...),
    imprese_config: str = Form(..., description="JSON array con colonne prezzo/quantità per impresa"),
    sheet_name: str | None = Form(default=None),
    code_columns: str | None = Form(default=None),
    description_columns: str | None = Form(default=None),
    progressive_column: str | None = Form(default=None),
) -> ImportBatchSingleFileResultSchema:
    """
    Importa ritorni di gara per più imprese partendo da un unico file Excel.
    """
    commessa = CommesseService.get_commessa(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )

    _ensure_excel_file(file)

    try:
        config_payload = json.loads(imprese_config)
        if not isinstance(config_payload, list):
            raise ValueError("imprese_config deve essere una lista JSON")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Config imprese non valida: {exc}",
        )

    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(import_rate_limiter, client_ip)
    saved_result = storage_service.save_upload(commessa_id, file)
    saved_path = saved_result.path

    parsed_code_columns = _parse_column_list(code_columns)
    parsed_description_columns = _parse_column_list(description_columns)
    normalized_progressive_column = (
        progressive_column.strip().lstrip("$").upper()
        if progressive_column and progressive_column.strip()
        else None
    )
    sheet_name_value = sheet_name.strip() if sheet_name and sheet_name.strip() else None

    try:
        result = import_service.import_batch_single_file(
            session=session,
            commessa_id=commessa_id,
            file=saved_path,
            originale_nome=file.filename,
            imprese_config=config_payload,
            sheet_name=sheet_name_value,
            sheet_code_columns=parsed_code_columns,
            sheet_description_columns=parsed_description_columns,
            sheet_progressive_column=normalized_progressive_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    record_audit_log(
        session,
        user_id=None,
        action="IMPORT_BATCH_SINGLE_FILE",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        payload=saved_result.sha256,
        outcome="success",
    )

    computi_serialized = {
        impresa_label: ComputoSchema.model_validate(computo)
        for impresa_label, computo in (result.get("computi") or {}).items()
    }
    failed_entries = [
        {
            "impresa": item.get("impresa") or "",
            "error": item.get("error") or "Errore sconosciuto",
            "error_type": item.get("error_type"),
            "details": item.get("details"),
            "config": item.get("config"),
        }
        for item in result.get("failed", [])
    ]

    return ImportBatchSingleFileResultSchema(
        success=result.get("success", []),
        failed=failed_entries,
        total=result.get("total", len(config_payload)),
        success_count=result.get("success_count", 0),
        failed_count=result.get("failed_count", 0),
        computi=computi_serialized,
    )


@router.post(
    "/{commessa_id}/offers/manual-price",
    response_model=ManualPriceUpdateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[write_guard],
)
def update_manual_offer_price(
    commessa_id: int,
    payload: ManualPriceUpdateRequest,
    session: DBSession,
) -> ManualPriceUpdateResponse:
    _ = _get_commessa_or_404(session, commessa_id)
    try:
        offer, computo = import_service.update_manual_offer_price(
            session=session,
            commessa_id=commessa_id,
            computo_id=payload.computo_id,
            price_list_item_id=payload.price_list_item_id,
            prezzo_unitario=payload.prezzo_unitario,
            quantita=payload.quantita,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ManualPriceUpdateResponse(
        offer=PriceListOfferSchema(
            id=offer.id,
            price_list_item_id=offer.price_list_item_id,
            computo_id=offer.computo_id,
            impresa_id=offer.impresa_id,
            impresa_label=offer.impresa_label,
            round_number=offer.round_number,
            prezzo_unitario=offer.prezzo_unitario,
            quantita=offer.quantita,
            created_at=offer.created_at,
            updated_at=offer.updated_at,
        ),
        computo=ComputoSchema.model_validate(computo),
    )


@router.delete(
    "/{commessa_id}/computo/{computo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[admin_guard],
)
def delete_computo(commessa_id: int, computo_id: int, session: DBSession):
    computo = CommesseService.delete_computo(session, commessa_id, computo_id)
    if not computo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Computo non trovato"
        )


# ============================================================================
# Commessa Preferences (Settings)
# ============================================================================

@router.get("/{commessa_id}/preferences", response_model=CommessaPreferencesRead)
def get_commessa_preferences(commessa_id: int, session: DBSession) -> CommessaPreferencesRead:
    """Ottieni le preferenze della commessa. Crea automaticamente se non esistono."""
    # Verifica che la commessa esista
    commessa = session.get(Commessa, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commessa non trovata"
        )

    # Cerca le preferenze esistenti
    prefs = session.query(CommessaPreferences).filter(
        CommessaPreferences.commessa_id == commessa_id
    ).first()

    # Se non esistono, crea con valori default
    if not prefs:
        prefs = CommessaPreferences(commessa_id=commessa_id)
        session.add(prefs)
        session.commit()
        session.refresh(prefs)

    return CommessaPreferencesRead.model_validate(prefs)


@router.put(
    "/{commessa_id}/preferences",
    response_model=CommessaPreferencesRead,
    dependencies=[write_guard],
)
def update_commessa_preferences(
    commessa_id: int,
    payload: CommessaPreferencesBase,
    session: DBSession
) -> CommessaPreferencesRead:
    """Aggiorna le preferenze della commessa."""
    # Verifica che la commessa esista
    commessa = session.get(Commessa, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commessa non trovata"
        )

    # Cerca o crea le preferenze
    prefs = session.query(CommessaPreferences).filter(
        CommessaPreferences.commessa_id == commessa_id
    ).first()

    if not prefs:
        prefs = CommessaPreferences(commessa_id=commessa_id)
        session.add(prefs)

    # Aggiorna i campi
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)

    from datetime import datetime
    prefs.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(prefs)

    return CommessaPreferencesRead.model_validate(prefs)
