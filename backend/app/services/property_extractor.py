"""Compatibility shim for the legacy property extractor path.

The real implementation lives in ``app.services.nlp.property_extractor``; this file
keeps existing imports working while avoiding duplicated code.
"""

from app.services.nlp.property_extractor import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith("_")]
