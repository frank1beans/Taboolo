from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.db.models import (
    Computo,
    PriceListItem,
    PriceListOffer,
    VoceComputo,
)


@dataclass
class _InsightsCacheEntry:
    version: str
    timestamp: datetime
    data: dict


_INSIGHTS_CACHE: dict[int, _InsightsCacheEntry] = {}
_INSIGHTS_CACHE_LOCK = RLock()
_INSIGHTS_CACHE_TTL = timedelta(minutes=5)


class AnalysisCacheService:
    @staticmethod
    def compute_dataset_version(session: Session, commessa_id: int) -> str:
        """Calcola una versione basata sui timestamp/ID degli elementi collegati alla commessa.

        Ottimizzato: esegue una singola query invece di 4 separate.
        """
        # Single query with scalar subqueries for all MAX values
        result = session.exec(
            select(
                select(func.max(Computo.updated_at))
                .where(Computo.commessa_id == commessa_id)
                .correlate(None)
                .scalar_subquery()
                .label("max_computo"),
                select(func.max(VoceComputo.id))
                .where(VoceComputo.commessa_id == commessa_id)
                .correlate(None)
                .scalar_subquery()
                .label("max_voce"),
                select(func.max(PriceListOffer.updated_at))
                .where(PriceListOffer.commessa_id == commessa_id)
                .correlate(None)
                .scalar_subquery()
                .label("max_offer"),
                select(func.max(PriceListItem.updated_at))
                .where(PriceListItem.commessa_id == commessa_id)
                .correlate(None)
                .scalar_subquery()
                .label("max_price_item"),
            )
        ).one()

        parts = [
            str(result[0] or ""),
            str(result[1] or ""),
            str(result[2] or ""),
            str(result[3] or ""),
        ]
        return "|".join(parts)

    @staticmethod
    def try_get(commessa_id: int, version: str) -> dict | None:
        now = datetime.utcnow()
        with _INSIGHTS_CACHE_LOCK:
            entry = _INSIGHTS_CACHE.get(commessa_id)
            if (
                entry
                and entry.version == version
                and now - entry.timestamp <= _INSIGHTS_CACHE_TTL
            ):
                return entry.data
        return None

    @staticmethod
    def store(commessa_id: int, version: str, data: dict) -> None:
        with _INSIGHTS_CACHE_LOCK:
            _INSIGHTS_CACHE[commessa_id] = _InsightsCacheEntry(
                version=version,
                timestamp=datetime.utcnow(),
                data=data,
            )
