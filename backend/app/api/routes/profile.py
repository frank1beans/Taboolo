from fastapi import APIRouter, Depends, Request
from sqlmodel import select

from app.api.deps import DBSession, get_current_user, require_role, UserRole
from app.db.models import User, UserProfile
from app.schemas import ProfileUpdate, UserProfileRead, UserRead
from app.services import record_audit_log

router = APIRouter(
    dependencies=[
        require_role(
            [UserRole.viewer, UserRole.computista, UserRole.project_manager, UserRole.admin]
        )
    ]
)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/profile", response_model=UserProfileRead)
def get_profile(
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    profile = session.exec(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    ).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.put("/profile", response_model=UserProfileRead)
def update_profile(
    request: Request,
    payload: ProfileUpdate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    profile = session.exec(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    ).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)

    if payload.company is not None:
        profile.company = payload.company
    if payload.language is not None:
        profile.language = payload.language
    if payload.settings is not None:
        profile.settings = payload.settings

    session.add(profile)
    session.commit()
    session.refresh(profile)

    record_audit_log(
        session,
        user_id=current_user.id,
        action="UPDATE_PROFILE",
        endpoint=str(request.url),
        ip_address=request.client.host if request.client else None,
        method="PUT",
        payload=payload.model_dump(),
        outcome="success",
    )
    return profile
