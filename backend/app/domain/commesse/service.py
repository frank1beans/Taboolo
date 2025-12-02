"""Domain-level wrapper that forwards to the application service implementation.

This keeps the planned import path ``app.domain.commesse.service`` working without
duplicating the logic that actually lives in ``app.services.commesse``.
"""

from app.services.commesse import CommesseService

__all__ = ["CommesseService"]
