from __future__ import annotations

import logging
from hashlib import sha256
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core import settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.models import AuditLog
from app.db.session import engine

logger = logging.getLogger(__name__)


async def _extract_user_id(request: Request) -> int | None:
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", maxsplit=1)[1]
    elif settings.access_token_cookie_name in request.cookies:
        token = request.cookies.get(settings.access_token_cookie_name)

    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        return None
    try:
        return int(payload.get("sub")) if payload.get("sub") else None
    except (TypeError, ValueError):
        return None


async def audit_and_security_middleware(
    request: Request, call_next: Callable
):
    if settings.require_https and request.url.scheme != "https":
        logger.warning("Richiesta non-HTTPS ricevuta per %s", request.url.path)

    content_length = request.headers.get("content-length")
    max_bytes = settings.max_request_body_mb * 1024 * 1024
    if content_length and int(content_length) > max_bytes:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Payload troppo grande (>{settings.max_request_body_mb}MB)"},
        )

    body = await request.body()
    if len(body) > max_bytes:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Payload troppo grande (>{settings.max_request_body_mb}MB)"},
        )
    request._body = body  # type: ignore[attr-defined]

    user_id = await _extract_user_id(request)
    outcome = "success"
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            outcome = "failure"
        return response
    except Exception:
        outcome = "failure"
        raise
    finally:
        if request.url.path.startswith(settings.api_v1_prefix):
            try:
                payload_hash = sha256(body).hexdigest() if body else None
                with Session(engine) as session:
                    log = AuditLog(
                        user_id=user_id,
                        action="API_CALL",
                        method=request.method,
                        endpoint=request.url.path,
                        ip_address=request.client.host if request.client else None,
                        payload_hash=payload_hash,
                        outcome=outcome,
                    )
                    session.add(log)
                    session.commit()
            except Exception as exc:  # pragma: no cover - audit best effort
                logger.warning("Audit log fallito: %s", exc)


__all__ = ["audit_and_security_middleware"]
