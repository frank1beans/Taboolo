from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from threading import Lock
from typing import Any, Dict
import time
import uuid

from fastapi import HTTPException, status

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core import settings

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
    pbkdf2_sha256__rounds=260_000,
)


class InvalidTokenError(Exception):
    """Eccezione applicativa per token non valido o scaduto."""


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _build_payload(subject: str, email: str, role: str, expires_delta: timedelta) -> Dict[str, Any]:
    expire = datetime.now(timezone.utc) + expires_delta
    return {
        "sub": subject,
        "email": email,
        "role": role,
        "exp": expire,
        "jti": uuid.uuid4().hex,
    }


def create_access_token(*, subject: str, email: str, role: str, expires_minutes: int | None = None) -> str:
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    payload = _build_payload(
        subject=subject,
        email=email,
        role=role,
        expires_delta=timedelta(minutes=expire_minutes),
    )
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, subject: str, email: str, role: str, expires_minutes: int | None = None) -> str:
    expire_minutes = expires_minutes or settings.refresh_token_expire_minutes
    payload = _build_payload(
        subject=subject,
        email=email,
        role=role,
        expires_delta=timedelta(minutes=expire_minutes),
    )
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
    except JWTError as exc:  # pragma: no cover - validazione delegata all'handler
        raise InvalidTokenError(str(exc)) from exc


def decode_refresh_token(token: str) -> Dict[str, Any]:
    return decode_access_token(token)


def token_fingerprint(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


class SlidingWindowRateLimiter:
    """Rate limiting in-memory con finestra mobile (thread-safe)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = Lock()

    def hit(self, key: str) -> None:
        now = time.time()
        with self._lock:
            hits = self._hits.setdefault(key, [])
            # Mantieni solo gli hit nella finestra
            hits[:] = [ts for ts in hits if now - ts <= self.window_seconds]
            if len(hits) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Troppe richieste, riprova più tardi",
                )
            hits.append(now)


def enforce_rate_limit(limiter: SlidingWindowRateLimiter, key: str) -> None:
    limiter.hit(key)
