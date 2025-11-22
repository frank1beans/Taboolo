from typing import Optional
import logging
import re
from fastapi import APIRouter, HTTPException, status, Query
from sqlmodel import select
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import DBSession, require_role, UserRole
from app.db.models import (
    Settings,
    PriceListItem,
    Computo,
    ComputoTipo,
    PriceListOffer,
    PropertyLexicon,
    PropertyPattern,
    PropertyOverride,
    PropertyFeedback,
)
from app.db.models_wbs import Impresa
from app.schemas import (
    SettingsRead,
    SettingsUpdate,
    SettingsResponse,
    NlpModelOption,
    PropertySchemaResponse,
    ExtractRequest,
    ExtractedPropertiesResponse,
    PropertyLexiconCreate,
    PropertyLexiconRead,
    PropertyLexiconUpdate,
    PropertyPatternCreate,
    PropertyPatternRead,
    PropertyPatternUpdate,
    PropertyOverridePayload,
    PropertyOverrideRead,
    PropertyFeedbackPayload,
    PropertyFeedbackRead,
)
from app.services.nlp import (
    semantic_embedding_service,
    document_faiss_pipeline,
    price_list_faiss_service,
    get_available_semantic_models,
)
from app.services.importer import ImportService
from app.services.property_extraction import (
    extract_properties_from_text,
    extract_properties_auto,
    list_categories,
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[require_role([UserRole.project_manager, UserRole.admin])])
# Endpoints pubblici per schemi/properties (solo lettura)
public_router = APIRouter()


def _serialize_settings(settings: Settings) -> SettingsResponse:
    embeddings_outdated = bool(
        settings.nlp_embeddings_model_id
        and settings.nlp_embeddings_model_id != settings.nlp_model_id
    )
    models = [
        NlpModelOption(**model) for model in get_available_semantic_models()
    ]
    return SettingsResponse(
        settings=SettingsRead.model_validate(settings),
        nlp_models=models,
        nlp_embeddings_outdated=embeddings_outdated,
    )


def _configure_nlp_service(settings: Settings) -> None:
    semantic_embedding_service.configure(
        model_id=settings.nlp_model_id,
        max_length=settings.nlp_max_length,
        batch_size=settings.nlp_batch_size,
    )
    document_faiss_pipeline.configure(model_name=settings.nlp_model_id)


def _warmup_nlp_model() -> None:
    try:
        semantic_embedding_service.warmup()
    except RuntimeError as exc:  # pragma: no cover - dipendenze runtime
        logger.error("Impossibile scaricare il modello NLP selezionato: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impossibile scaricare il modello NLP selezionato: {exc}",
        ) from exc


@router.get("/", response_model=SettingsResponse)
def get_settings(session: DBSession) -> SettingsResponse:
    """Recupera le impostazioni globali (singola riga)."""
    settings = session.query(Settings).first()
    
    if not settings:
        # Crea settings con valori di default se non esistono
        settings = Settings()
        settings.nlp_embeddings_model_id = settings.nlp_model_id
        session.add(settings)
        session.commit()
        session.refresh(settings)

    _configure_nlp_service(settings)
    return _serialize_settings(settings)


@router.put("/", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate, session: DBSession) -> SettingsResponse:
    """Aggiorna le impostazioni globali."""
    settings = session.query(Settings).first()
    payload_data = payload.model_dump(exclude_unset=True)
    created = False
    
    if not settings:
        # Crea se non esiste con i valori di default
        settings = Settings()
        session.add(settings)
        created = True

    for key, value in payload_data.items():
        setattr(settings, key, value)

    if created and settings.nlp_embeddings_model_id is None:
        settings.nlp_embeddings_model_id = settings.nlp_model_id
    
    session.commit()
    session.refresh(settings)
    _configure_nlp_service(settings)
    model_fields = {"nlp_model_id", "nlp_batch_size", "nlp_max_length"}
    if created or payload_data.keys() & model_fields:
        _warmup_nlp_model()
    return _serialize_settings(settings)


@router.post("/regenerate-embeddings")
def regenerate_embeddings(
    session: DBSession,
    commessa_id: Optional[int] = Query(
        default=None,
        description="ID della commessa per cui rigenerare gli embedding. Se non specificato, rigenera per tutte le commesse."
    ),
) -> dict:
    """Rigenera gli embedding semantici per il catalogo prezzi di una commessa o di tutte le commesse."""
    settings_row = session.query(Settings).first()
    if settings_row:
        _configure_nlp_service(settings_row)
        _warmup_nlp_model()

    if not semantic_embedding_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servizio embedding semantici non disponibile. Verifica che le dipendenze NLP siano installate.",
        )

    # Costruisci la query base
    query = select(PriceListItem)
    if commessa_id is not None:
        query = query.where(PriceListItem.commessa_id == commessa_id)

    items = session.exec(query).all()
    total = len(items)

    if total == 0:
        message = f"Nessuna voce trovata per la commessa {commessa_id}" if commessa_id else "Nessuna voce nel catalogo prezzi"
        return {
            "message": message,
            "total": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

    logger.info(
        "Rigenerazione embedding per %s voci con il modello '%s'",
        total,
        semantic_embedding_service.model_id,
    )

    updated = 0
    skipped = 0
    errors = 0

    for idx, item in enumerate(items, 1):
        if idx % 100 == 0:
            logger.info(f"Processate {idx}/{total} voci...")

        # Prepara entry dict per embedding
        metadata = item.extra_metadata or {}
        price_list_labels = {}
        preferred_lists = []
        if isinstance(metadata, dict):
            labels = metadata.get("price_list_labels")
            if isinstance(labels, dict):
                price_list_labels = labels
            pref = metadata.get("preferred_price_lists")
            if isinstance(pref, list):
                preferred_lists = pref

        entry = {
            "item_code": item.item_code,
            "code": item.item_code,
            "product_id": item.product_id,
            "item_description": item.item_description,
            "description": item.item_description,
            "wbs6_code": item.wbs6_code,
            "wbs6_description": item.wbs6_description,
            "wbs7_code": item.wbs7_code,
            "wbs7_description": item.wbs7_description,
            "price_lists": item.price_lists,
            "price_list_labels": price_list_labels,
            "preferred_price_lists": preferred_lists,
        }

        try:
            embedding_metadata = semantic_embedding_service.prepare_price_list_metadata(entry)
            if not embedding_metadata:
                skipped += 1
                continue

            # Aggiorna metadata
            metadata = item.extra_metadata or {}
            if not isinstance(metadata, dict):
                metadata = {}

            nlp_metadata = metadata.setdefault("nlp", {})
            nlp_metadata[semantic_embedding_service.metadata_slot] = embedding_metadata
            nlp_metadata["model_id"] = semantic_embedding_service.model_id
            item.extra_metadata = metadata
            # Marca il campo come modificato per SQLAlchemy
            flag_modified(item, "extra_metadata")
            session.add(item)
            updated += 1

        except Exception as exc:
            logger.error(f"Errore per item {item.id} ({item.item_code}): {exc}")
            errors += 1

    # Commit delle modifiche sugli item
    session.commit()

    if settings_row:
        settings_row.nlp_embeddings_model_id = semantic_embedding_service.model_id
        session.add(settings_row)
        session.commit()

    # Invalida indice FAISS per forzare ricostruzione alla prossima ricerca
    if commessa_id is not None:
        price_list_faiss_service.delete_index(commessa_id)
        logger.info("Indice FAISS eliminato per commessa %s", commessa_id)
    else:
        # Elimina tutti gli indici FAISS
        import glob
        for index_file in glob.glob(str(price_list_faiss_service.cache_dir / "*.faiss")):
            try:
                from pathlib import Path
                Path(index_file).unlink()
            except Exception as exc:
                logger.warning("Errore eliminazione indice %s: %s", index_file, exc)
        price_list_faiss_service._index = None
        logger.info("Tutti gli indici FAISS eliminati")

    message = f"Embedding rigenerati per la commessa {commessa_id}" if commessa_id else "Embedding rigenerati per tutte le commesse"
    logger.info(f"{message}. Aggiornate: {updated}, Saltate: {skipped}, Errori: {errors}")

    return {
        "message": message,
        "total": total,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def _load_property_schemas() -> PropertySchemaResponse:
    try:
        categories = list_categories()
    except Exception as exc:  # pragma: no cover - robustezza lettura file
        logger.error("Impossibile leggere gli schemi proprietà: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impossibile leggere gli schemi proprietà ({exc})",
        ) from exc

    return PropertySchemaResponse(
        categories=[
            {
                "id": cat.get("id"),
                "name": cat.get("name"),
                "required": cat.get("required") or [],
                "properties": cat.get("properties") or [],
            }
            for cat in categories
        ]
    )


def _extract_properties_payload(payload: ExtractRequest) -> ExtractedPropertiesResponse:
    try:
        result = extract_properties_from_text(text=payload.text, category_id=payload.category_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ExtractedPropertiesResponse.model_validate(result)


@public_router.get("/property-schemas", response_model=PropertySchemaResponse)
def get_property_schemas_public() -> PropertySchemaResponse:
    """Schema proprietà accessibile senza autenticazione."""
    return _load_property_schemas()


@public_router.post("/extract-properties", response_model=ExtractedPropertiesResponse)
def extract_properties_public(payload: ExtractRequest) -> ExtractedPropertiesResponse:
    """Estrae proprietà (public) tramite regole deterministiche."""
    return _extract_properties_payload(payload)


@router.get("/property-schemas", response_model=PropertySchemaResponse)
def get_property_schemas_private() -> PropertySchemaResponse:
    """Schema proprietà autenticato (stesso output del public)."""
    return _load_property_schemas()


@router.post("/extract-properties", response_model=ExtractedPropertiesResponse)
def extract_properties_private(payload: ExtractRequest) -> ExtractedPropertiesResponse:
    """Estrazione proprietà autenticata (stesso comportamento del public)."""
    return _extract_properties_payload(payload)


@router.post("/regenerate-properties")
def regenerate_properties(
    session: DBSession,
    commessa_id: Optional[int] = Query(
        default=None,
        description=(
            "ID della commessa per cui rigenerare le proprieta. "
            "Se non specificato, rigenera per tutte le commesse."
        ),
    ),
) -> dict:
    """Ricalcola le proprieta estratte per le voci elenco prezzi (pipeline ibrida unica)."""

    query = select(PriceListItem)
    if commessa_id is not None:
        query = query.where(PriceListItem.commessa_id == commessa_id)

    items = session.exec(query).all()
    total = len(items)
    if total == 0:
        message = (
            f"Nessuna voce trovata per la commessa {commessa_id}"
            if commessa_id
            else "Nessuna voce nel catalogo prezzi"
        )
        return {
            "message": message,
            "total": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

    updated = 0
    skipped = 0
    errors = 0

    for idx, item in enumerate(items, 1):
        if idx % 100 == 0:
            logger.info("Processate proprieta %s/%s ...", idx, total)

        entry = {
            "item_code": item.item_code,
            "code": item.item_code,
            "product_id": item.product_id,
            "item_description": item.item_description,
            "description": item.item_description,
            "wbs6_code": item.wbs6_code,
            "wbs6_description": item.wbs6_description,
            "wbs7_code": item.wbs7_code,
            "wbs7_description": item.wbs7_description,
        }

        try:
            extracted = extract_properties_auto(entry, session=session)
            if not extracted:
                skipped += 1
                continue
            metadata = item.extra_metadata or {}
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["extracted_properties"] = extracted
            item.extra_metadata = metadata
            flag_modified(item, "extra_metadata")
            session.add(item)
            updated += 1
        except Exception as exc:  # pragma: no cover - robustezza
            logger.error(
                "Errore estrazione proprieta per voce %s (%s): %s",
                item.id,
                item.item_code,
                exc,
            )
            errors += 1

    session.commit()

    message = (
        f"Proprieta rigenerate per la commessa {commessa_id}"
        if commessa_id
        else "Proprieta rigenerate per tutte le commesse"
    )
    return {
        "message": message,
        "total": total,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def _update_fields(model, updates: dict) -> None:
    for key, value in updates.items():
        if value is None:
            continue
        setattr(model, key, value)


@router.get("/property-lexicon", response_model=list[PropertyLexiconRead])
def list_property_lexicon(session: DBSession) -> list[PropertyLexiconRead]:
    entries = session.exec(select(PropertyLexicon).order_by(PropertyLexicon.id)).all()
    return entries


@router.post("/property-lexicon", response_model=PropertyLexiconRead)
def create_property_lexicon(payload: PropertyLexiconCreate, session: DBSession) -> PropertyLexiconRead:
    entry = PropertyLexicon(**payload.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.patch("/property-lexicon/{lex_id}", response_model=PropertyLexiconRead)
def update_property_lexicon(lex_id: int, payload: PropertyLexiconUpdate, session: DBSession) -> PropertyLexiconRead:
    entry = session.get(PropertyLexicon, lex_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexicon entry not found")
    _update_fields(entry, payload.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/property-lexicon/{lex_id}")
def delete_property_lexicon(lex_id: int, session: DBSession) -> dict:
    entry = session.get(PropertyLexicon, lex_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexicon entry not found")
    session.delete(entry)
    session.commit()
    return {"status": "ok", "deleted": lex_id}


@router.get("/property-patterns", response_model=list[PropertyPatternRead])
def list_property_patterns(session: DBSession) -> list[PropertyPatternRead]:
    patterns = session.exec(select(PropertyPattern).order_by(PropertyPattern.priority.desc(), PropertyPattern.id)).all()
    return patterns


@router.post("/property-patterns", response_model=PropertyPatternRead)
def create_property_pattern(payload: PropertyPatternCreate, session: DBSession) -> PropertyPatternRead:
    pattern = PropertyPattern(**payload.model_dump())
    session.add(pattern)
    session.commit()
    session.refresh(pattern)
    return pattern


@router.patch("/property-patterns/{pattern_id}", response_model=PropertyPatternRead)
def update_property_pattern(pattern_id: int, payload: PropertyPatternUpdate, session: DBSession) -> PropertyPatternRead:
    pattern = session.get(PropertyPattern, pattern_id)
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    _update_fields(pattern, payload.model_dump())
    session.add(pattern)
    session.commit()
    session.refresh(pattern)
    return pattern


@router.delete("/property-patterns/{pattern_id}")
def delete_property_pattern(pattern_id: int, session: DBSession) -> dict:
    pattern = session.get(PropertyPattern, pattern_id)
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    session.delete(pattern)
    session.commit()
    return {"status": "ok", "deleted": pattern_id}


@router.get("/price-list-items/{item_id}/properties-override", response_model=PropertyOverrideRead)
def get_property_override(item_id: int, session: DBSession) -> PropertyOverrideRead:
    override = session.exec(
        select(PropertyOverride).where(PropertyOverride.price_list_item_id == item_id)
    ).first()
    if not override:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")
    return override


@router.patch("/price-list-items/{item_id}/properties-override", response_model=PropertyOverrideRead)
def upsert_property_override(item_id: int, payload: PropertyOverridePayload, session: DBSession) -> PropertyOverrideRead:
    item = session.get(PriceListItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list item not found")

    existing = session.exec(
        select(PropertyOverride).where(PropertyOverride.price_list_item_id == item_id)
    ).first()
    if existing:
        _update_fields(existing, payload.model_dump())
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    override = PropertyOverride(price_list_item_id=item_id, **payload.model_dump())
    session.add(override)
    session.commit()
    session.refresh(override)
    return override


@router.post("/price-list-items/{item_id}/property-feedback", response_model=PropertyFeedbackRead)
def create_property_feedback(item_id: int, payload: PropertyFeedbackPayload, session: DBSession) -> PropertyFeedbackRead:
    item = session.get(PriceListItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list item not found")
    feedback = PropertyFeedback(price_list_item_id=item_id, **payload.model_dump())
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback

def _sanitize_impresa_label(label: str | None) -> str | None:
    if not label:
        return None
    text = label.strip()
    if not text:
        return None
    text = text.replace("Round", "").strip()
    text = re.sub(r"\(\d+\)$", "", text).strip()
    return text or None


def _get_or_create_impresa(session: DBSession, label: str | None) -> Impresa | None:
    clean = _sanitize_impresa_label(label)
    if not clean:
        return None
    normalized = re.sub(r"\s+", " ", clean).lower()
    existing = session.exec(
        select(Impresa).where(Impresa.normalized_label == normalized)
    ).first()
    if existing:
        return existing
    impresa = Impresa(label=clean, normalized_label=normalized)
    session.add(impresa)
    session.flush()
    return impresa


@router.post("/normalize-imprese")
def normalize_imprese(
    session: DBSession,
    commessa_id: Optional[int] = Query(
        default=None,
        description="ID della commessa per cui normalizzare le imprese. Se non specificato, normalizza tutte.",
    ),
) -> dict:
    """Uniforma le etichette delle imprese su tutti i ritorni (rimuove suffissi tipo '(2)' e riallinea gli offer)."""

    query = select(Computo).where(Computo.tipo == ComputoTipo.ritorno)
    if commessa_id is not None:
        query = query.where(Computo.commessa_id == commessa_id)

    ritorni = session.exec(query).all()
    if not ritorni:
        message = f"Nessun ritorno trovato per la commessa {commessa_id}" if commessa_id else "Nessun ritorno presente"
        return {"message": message, "total": 0, "updated": 0, "errors": 0}

    updated = 0
    errors = 0

    for ritorno in ritorni:
        try:
            impresa_clean = _sanitize_impresa_label(ritorno.impresa)
            impresa_entry = _get_or_create_impresa(session, impresa_clean)
            if impresa_clean != ritorno.impresa:
                ritorno.impresa = impresa_clean
                session.add(ritorno)

            offers = session.exec(
                select(PriceListOffer).where(PriceListOffer.computo_id == ritorno.id)
            ).all()
            for offer in offers:
                if impresa_entry:
                    offer.impresa_id = impresa_entry.id
                offer.impresa_label = impresa_clean
                session.add(offer)
            updated += 1
        except Exception as exc:  # pragma: no cover - robustezza
            logger.error("Errore normalizzando impresa per computo %s: %s", ritorno.id, exc)
            errors += 1

    session.commit()

    message = f"Imprese normalizzate per la commessa {commessa_id}" if commessa_id else "Imprese normalizzate per tutte le commesse"
    return {"message": message, "total": len(ritorni), "updated": updated, "errors": errors}
