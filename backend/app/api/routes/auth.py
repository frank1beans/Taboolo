from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.api.deps import DBSession, get_current_user
from app.core import settings
from app.core.security import (
    InvalidTokenError,
    SlidingWindowRateLimiter,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    enforce_rate_limit,
    hash_password,
    token_fingerprint,
    verify_password,
)
from app.db.models import RefreshToken, User, UserProfile, UserRole
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserRead
from app.services import record_audit_log

router = APIRouter()
login_rate_limiter = SlidingWindowRateLimiter(
    settings.login_rate_limit_attempts, settings.login_rate_limit_window_seconds
)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    session: DBSession,
    payload: UserCreate = Body(...),
):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.viewer,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    profile = UserProfile(user_id=user.id)
    session.add(profile)
    session.commit()
    return user


def _persist_refresh_token(
    session: Session, user: User, refresh_token: str, replaced_by: RefreshToken | None = None
) -> RefreshToken:
    token = RefreshToken(
        user_id=user.id,
        token_fingerprint=token_fingerprint(refresh_token),
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.refresh_token_expire_minutes),
        replaced_by_id=replaced_by.id if replaced_by else None,
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        settings.access_token_cookie_name,
        access_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        settings.refresh_token_cookie_name,
        refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.refresh_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    session: DBSession,
    credentials: LoginRequest = Body(...),
):
    client_ip = request.client.host if request.client else "anonymous"
    enforce_rate_limit(login_rate_limiter, client_ip)

    user = session.exec(select(User).where(User.email == credentials.email)).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        record_audit_log(
            session,
            user_id=user.id if user else None,
            action="LOGIN",
            endpoint=str(request.url),
            ip_address=client_ip,
            method="POST",
            outcome="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato",
        )

    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role.value,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id), email=user.email, role=user.role.value
    )
    _persist_refresh_token(session, user, refresh_token)
    _set_auth_cookies(response, access_token, refresh_token)

    record_audit_log(
        session,
        user_id=user.id,
        action="LOGIN",
        endpoint=str(request.url),
        ip_address=client_ip,
        method="POST",
        outcome="success",
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, session: DBSession):
    provided = request.cookies.get(settings.refresh_token_cookie_name)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        provided = auth_header.split(" ", maxsplit=1)[1]
    if not provided:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante")

    try:
        payload = decode_refresh_token(provided)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido") from exc

    user_id = payload.get("sub")
    user = session.get(User, int(user_id)) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utente non valido")

    token_row = session.exec(
        select(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .where(RefreshToken.token_fingerprint == token_fingerprint(provided))
        .where(RefreshToken.revoked.is_(False))
    ).first()
    if not token_row or token_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token scaduto")

    token_row.revoked = True
    session.add(token_row)
    session.commit()

    access_token = create_access_token(
        subject=str(user.id), email=user.email, role=user.role.value
    )
    refresh_token_value = create_refresh_token(
        subject=str(user.id), email=user.email, role=user.role.value
    )
    new_token = _persist_refresh_token(session, user, refresh_token_value, replaced_by=token_row)
    token_row.replaced_by_id = new_token.id
    session.add(token_row)
    session.commit()
    _set_auth_cookies(response, access_token, refresh_token_value)
    record_audit_log(
        session,
        user_id=user.id,
        action="REFRESH",
        endpoint=str(request.url),
        ip_address=request.client.host if request.client else None,
        method="POST",
        outcome="success",
    )
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token_value, user=user
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response, session: DBSession, user: User = Depends(get_current_user)):
    tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    ).all()
    for token in tokens:
        token.revoked = True
        session.add(token)
    session.commit()

    response.delete_cookie(settings.access_token_cookie_name)
    response.delete_cookie(settings.refresh_token_cookie_name)

    record_audit_log(
        session,
        user_id=user.id,
        action="LOGOUT",
        endpoint=str(request.url),
        ip_address=request.client.host if request.client else None,
        method="POST",
        outcome="success",
    )
    return {"detail": "Logout effettuato"}
