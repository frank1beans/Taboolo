"""Domain-level compatibility wrapper for WBS predictor utilities."""

from app.services.wbs_predictor import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith("_")]
