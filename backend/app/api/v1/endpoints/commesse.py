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
    catalog_search_service,
    commessa_bundle_service,
    CommesseService,
    import_service,
    PreventivoSelectionError,
    record_audit_log,
    serialization_service,
    six_import_service,
    storage_service,
    WbsImportService,
    WbsVisibilityService,
)
from app.services.analysis.analysis import AnalysisService
from app.services.analysis.comparison import ComparisonService
from app.services.analysis.trends import TrendsService
from app.services.nlp.embedding_service import extract_construction_attributes

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


def _parse_column_list(value: str | None) -> list[str] | None:
    """Normalizza una stringa di colonne tipo 'A,B,C' in lista maiuscola."""
    if not value or not value.strip():
        return None
    return [item.strip().lstrip("$").upper() for item in value.split(",") if item.strip()]


def _ensure_excel_file(upload: UploadFile) -> None:
    if not upload.filename or not upload.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Usa un file Excel (.xlsx, .xlsm, .xls)",
        )


def _get_commessa_or_404(session: DBSession, commessa_id: int) -> Commessa:
    commessa = CommesseService.get_commessa(session, commessa_id)
    if not commessa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )
    return commessa


def _parse_optional_commessa_id(raw: int | str | None, field_name: str = "commessa_id") -> int | None:
    """Accetta ID commessa anche come stringa vuota e lo normalizza a int o None."""
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    normalized = raw.strip()
    if not normalized:
        return None
    try:
        return int(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve essere un intero valido",
        ) from exc


def _ensure_six_or_xml_file(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith((".six", ".xml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non supportato. Fornisci un file STR Vision (.six o .xml)",
        )


# ============================================================================
# Price Catalog Routes (dichiarate prima delle rotte dinamiche per evitare clash su /{commessa_id})
# ============================================================================

@router.get("/price-catalog", response_model=list[PriceListItemSchema])
def list_price_catalog(
    session: DBSession,
    search: str | None = Query(
        default=None,
        description="Filtro testuale su codice, descrizione e WBS.",
    ),
    commessa_id: int | str | None = Query(
        default=None, description="Limita i risultati alla commessa indicata."
    ),
    business_unit: str | None = Query(
        default=None, description="Filtra per Business Unit esatta."
    ),
) -> list[PriceListItemSchema]:
    """Elenco prezzi aggregato di tutte le commesse."""
    commessa_id_value = _parse_optional_commessa_id(commessa_id)
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

    if commessa_id_value is not None:
        query = query.filter(PriceListItem.commessa_id == commessa_id_value)

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
    project_quantity_map = serialization_service.collect_project_quantities(session, commessa_id_value)
    offers_map = serialization_service.collect_price_list_offers(session, [item.id for item, _ in rows])

    return [
        PriceListItemSchema(
            **serialization_service.serialize_price_list_item(
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
    commessa_id: int | str | None = Query(
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
    commessa_id_value = _parse_optional_commessa_id(commessa_id)
    try:
        results = catalog_search_service.search_catalog(
            session=session,
            query=query,
            commessa_id=commessa_id_value,
            top_k=top_k,
            min_score=min_score,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return [
        PriceListItemSearchResultSchema(**item)
        for item in results
    ]


@router.get("/price-catalog/summary", response_model=PriceCatalogSummarySchema)
def list_price_catalog_summary(session: DBSession) -> PriceCatalogSummarySchema:
    """Riepilogo del catalogo prezzi raggruppato per business unit e commessa."""
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
# CRUD Routes
# ============================================================================

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


@router.put("/{commessa_id}", response_model=CommessaSchema)
def update_commessa(commessa_id: int, payload: CommessaCreate, session: DBSession) -> CommessaSchema:
    updated = CommesseService.update_commessa(session, commessa_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )
    return updated


@router.delete("/{commessa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commessa(commessa_id: int, session: DBSession):
    deleted = CommesseService.delete_commessa(session, commessa_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Commessa non trovata"
        )


# ============================================================================
# Bundle Import/Export Routes
# ============================================================================

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


# ============================================================================
# WBS Routes
# ============================================================================

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


# ============================================================================
# SIX Import Routes  
# ============================================================================

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
    from app.db.models import VoceComputo

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

    offers_map = serialization_service.collect_price_list_offers(session, [item.id for item in items])
    project_quantity_map = serialization_service.collect_project_quantities(session, commessa.id)

    return [
        PriceListItemSchema(
            **serialization_service.serialize_price_list_item(
                item,
                commessa,
                offers_map.get(item.id),
                project_quantity_map,
            )
        )
        for item in items
    ]


# ============================================================================
# Analysis Routes
# ============================================================================

@router.get("/{commessa_id}/analisi", response_model=AnalisiCommessaSchema)
def get_commessa_analisi(
    commessa_id: int,
    session: DBSession,
    round_number: int | None = Query(None, alias="round"),
    impresa: str | None = None,
) -> AnalisiCommessaSchema:
    _get_commessa_or_404(session, commessa_id)
    return AnalysisService.get_commessa_analisi(
        session, commessa_id, round_number=round_number, impresa=impresa
    )


@router.get("/{commessa_id}/confronto", response_model=ConfrontoOfferteSchema)
def get_commessa_confronto(
    commessa_id: int,
    session: DBSession,
) -> ConfrontoOfferteSchema:
    _get_commessa_or_404(session, commessa_id)
    return ComparisonService.get_commessa_confronto(session, commessa_id)


@router.get("/{commessa_id}/wbs6-trend/{wbs6_id}", response_model=AnalisiWBS6TrendSchema)
def get_commessa_wbs6_dettaglio(
    commessa_id: int,
    wbs6_id: str,
    session: DBSession,
    round_number: int | None = Query(None, alias="round"),
    impresa: str | None = None,
) -> AnalisiWBS6TrendSchema:
    _get_commessa_or_404(session, commessa_id)
    return AnalysisService.get_commessa_wbs6_dettaglio(
        session, commessa_id, wbs6_id, round_number=round_number, impresa=impresa
    )


@router.get("/{commessa_id}/trend-round", response_model=TrendEvoluzioneSchema)
def get_commessa_trend_round(
    commessa_id: int,
    session: DBSession,
    impresa: str | None = None,
) -> TrendEvoluzioneSchema:
    _get_commessa_or_404(session, commessa_id)
    return TrendsService.get_commessa_trend_round(session, commessa_id, impresa=impresa)


@router.get("/{commessa_id}/analisi/trend-round", response_model=TrendEvoluzioneSchema)
def get_commessa_trend_round_legacy(
    commessa_id: int,
    session: DBSession,
    impresa: str | None = None,
) -> TrendEvoluzioneSchema:
    # Alias per compatibilità con il frontend /analisi/trend-round
    _get_commessa_or_404(session, commessa_id)
    return TrendsService.get_commessa_trend_round(session, commessa_id, impresa=impresa)


@router.get(
    "/{commessa_id}/heatmap-competitivita", response_model=HeatmapCompetitivitaSchema
)
def get_commessa_heatmap_competitivita(
    commessa_id: int,
    session: DBSession,
    round_number: int | None = Query(None, alias="round"),
) -> HeatmapCompetitivitaSchema:
    _get_commessa_or_404(session, commessa_id)
    return TrendsService.get_commessa_heatmap_competitivita(
        session, commessa_id, round_number=round_number
    )


@router.get(
    "/{commessa_id}/analisi/heatmap-competitivita", response_model=HeatmapCompetitivitaSchema
)
def get_commessa_heatmap_competitivita_legacy(
    commessa_id: int,
    session: DBSession,
    round_number: int | None = Query(None, alias="round"),
) -> HeatmapCompetitivitaSchema:
    # Alias per compatibilità con il frontend /analisi/heatmap-competitivita
    _get_commessa_or_404(session, commessa_id)
    return TrendsService.get_commessa_heatmap_competitivita(
        session, commessa_id, round_number=round_number
    )


# ============================================================================
# Upload Routes
# ============================================================================

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
