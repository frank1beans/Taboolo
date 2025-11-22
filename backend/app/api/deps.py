from typing import Annotated, Callable, Sequence

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core import settings
from app.core.security import decode_access_token, InvalidTokenError
from app.db import get_session
from app.db.models import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=False
)

DBSession = Annotated[Session, Depends(get_session)]


def _extract_token(request: Request, bearer: str | None, cookie_token: str | None) -> str:
    if bearer:
        return bearer
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", maxsplit=1)[1]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Token di accesso mancante"
    )


def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: DBSession,
    access_cookie: str | None = Cookie(
        default=None, alias=settings.access_token_cookie_name, include_in_schema=False
    ),
) -> User:
    """Recupera l'utente autenticato a partire da un Bearer token JWT."""
    raw_token = _extract_token(request, token, access_cookie)
    try:
        payload = decode_access_token(raw_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token privo di subject",
        )
    user = session.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato o disabilitato",
        )
    return user


def require_role(allowed_roles: Sequence[UserRole]) -> Callable:
    def _role_guard(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permessi insufficienti",
            )
        return current_user

    return Depends(_role_guard)


__all__ = ["DBSession", "get_current_user", "require_role", "UserRole"]
