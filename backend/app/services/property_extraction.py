"""Compatibility shim for the legacy import path.

All logic now lives in ``app.services.nlp.property_extraction``; this module simply
re-exports everything to avoid code drift across duplicated files.
"""

from app.services.nlp.property_extraction import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith("_")]
