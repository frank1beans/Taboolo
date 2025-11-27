from typing import Any, Sequence

from sqlalchemy import func
from app.api.deps import DBSession
from app.db.models import (
    Commessa,
    Computo,
    ComputoTipo,
    PriceListItem,
    PriceListOffer,
)
from app.db.models_wbs import Voce as VoceNorm, VoceProgetto


def serialize_price_list_item(
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
            serialized = serialize_price_list_offer(offer)
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


def serialize_price_list_offer(offer: PriceListOffer) -> dict[str, Any]:
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


def collect_price_list_offers(
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


def collect_project_quantities(
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
