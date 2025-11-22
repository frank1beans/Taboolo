from fastapi import APIRouter

from app.core import settings as app_settings
from .routes import auth, commesse, computi, dashboard, settings, import_configs, profile

api_router = APIRouter(prefix=app_settings.api_v1_prefix)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(commesse.router, prefix="/commesse", tags=["commesse"])
api_router.include_router(computi.router, prefix="/computi", tags=["computi"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(settings.public_router, prefix="/settings", tags=["settings"])
api_router.include_router(import_configs.router, prefix="/import-configs", tags=["import-configs"])
api_router.include_router(profile.router, tags=["users"])

__all__ = ["api_router"]
