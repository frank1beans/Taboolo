from __future__ import annotations

from typing import Optional

from hashlib import sha256

from sqlmodel import Session

from app.db.models import AuditLog


def _safe_hash(payload: bytes | str | None) -> Optional[str]:
    if payload is None:
        return None
    if isinstance(payload, str):
        payload = payload.encode("utf-8", "ignore")
    return sha256(payload).hexdigest()


def record_audit_log(
    session: Session,
    *,
    user_id: Optional[int],
    action: str,
    endpoint: Optional[str] = None,
    ip_address: Optional[str] = None,
    method: Optional[str] = None,
    payload: bytes | str | None = None,
    outcome: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action,
        method=method,
        endpoint=endpoint,
        ip_address=ip_address,
        payload_hash=_safe_hash(payload),
        outcome=outcome,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log
