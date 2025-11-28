from __future__ import annotations

import logging
from hashlib import sha256
from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core import settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.models import AuditLog
from app.db.session import engine

logger = logging.getLogger(__name__)


async def _extract_user_id(request: Request) -> int | None:
    """
    Prova a recuperare l'ID utente dal token JWT presente
    nell'header Authorization Bearer o nel cookie di access token.
    Restituisce None se non è possibile estrarlo in modo sicuro.
    """
    token: str | None = None

    # 1️⃣ Prima prova dall'header Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", maxsplit=1)[1].strip()

    # 2️⃣ Se non presente, prova dal cookie
    if not token and settings.access_token_cookie_name in request.cookies:
        token = request.cookies.get(settings.access_token_cookie_name)

    if not token:
        return None

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        # Token non valido/non decodificabile → lo ignoriamo ai fini dell'audit
        return None

    sub = payload.get("sub")
    if sub is None:
        return None

    try:
        return int(sub)
    except (TypeError, ValueError):
        return None


def _is_https(request: Request) -> bool:
    """
    Determina se la richiesta è stata fatta via HTTPS, tenendo conto
    dei proxy (es. Render/NGINX) che usano X-Forwarded-Proto.
    """
    # Se sei dietro proxy, spesso request.url.scheme risulta "http"
    # ma X-Forwarded-Proto indica "https".
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        return forwarded_proto.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"


async def audit_and_security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable],
):
    """
    Middleware globale che:
    - verifica HTTPS (se richiesto)
    - limita la dimensione del payload
    - registra audit di ogni chiamata API v1
    """

    # 🔐 1. Controllo HTTPS (se abilitato)
    if settings.require_https and not _is_https(request):
        logger.warning(
            "Richiesta non-HTTPS ricevuta per %s (client=%s)",
            request.url.path,
            request.client.host if request.client else "unknown",
        )

    # 📏 2. Controllo dimensione massima del body
    max_bytes = settings.max_request_body_mb * 1024 * 1024

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Payload troppo grande (>{settings.max_request_body_mb}MB)"
                        )
                    },
                )
        except ValueError:
            # Header content-length non valido → lo ignoriamo e controlliamo il body reale
            pass

    # Leggiamo il body UNA volta sola
    body = await request.body()
    if len(body) > max_bytes:
        return JSONResponse(
            status_code=413,
            content={
                "detail": f"Payload troppo grande (>{settings.max_request_body_mb}MB)"
            },
        )

    # Salviamo il body per le route downstream (hack standard in FastAPI/Starlette)
    request._body = body  # type: ignore[attr-defined]

    # 👤 3. Proviamo a ricavare user_id dal token (se presente)
    user_id = await _extract_user_id(request)

    # Risultato di default: assumiamo successo, e correggiamo se serve
    outcome = "success"

    try:
        # ▶️ 4. Procediamo con la richiesta vera e propria
        response = await call_next(request)

        if response.status_code >= 400:
            outcome = "failure"

        return response

    except Exception:
        outcome = "failure"
        # Lasciamo propagare l'eccezione dopo aver segnato il fallimento
        raise

    finally:
        # 📝 5. Audit (best effort, non deve MAI bloccare l'API)
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
