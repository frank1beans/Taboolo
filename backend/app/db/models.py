"""Database models - Compatibility layer.

IMPORTANT: This file now serves as a compatibility layer for backward compatibility.
All models have been moved to their respective domain packages:

- Users & Auth: app.domain.users.models
- Commesse: app.domain.commesse.models
- Computi & Voci: app.domain.computi.models
- Catalog (Price Lists): app.domain.catalog.models
- Settings: app.domain.settings.models
- WBS: app.db.models_wbs (kept here as it's complex and well-organized)

For new code, import from the domain packages directly.
This file re-exports everything for backward compatibility with existing code.
"""
from __future__ import annotations

# Re-export all models from domain packages for backward compatibility
from app.domain.users.models import (
    User,
    UserProfile,
    UserRole,
    RefreshToken,
    AuditLog,
)
from app.domain.commesse.models import (
    Commessa,
    CommessaBase,
    CommessaRead,
    CommessaStato,
    CommessaPreferences,
    CommessaPreferencesBase,
    CommessaPreferencesRead,
)
from app.domain.computi.models import (
    Computo,
    ComputoBase,
    ComputoRead,
    ComputoTipo,
    VoceComputo,
    VoceBase,
    VoceRead,
    ImportConfig,
    ImportConfigBase,
    ImportConfigRead,
)
from app.domain.catalog.models import (
    PriceListItem,
    PriceListOffer,
    PropertyLexicon,
    PropertyPattern,
    PropertyOverride,
    PropertyFeedback,
)
from app.domain.settings.models import (
    Settings,
    SettingsBase,
    SettingsRead,
)

# Import WBS models from their current location
from app.db.models_wbs import *

__all__ = [
    # Users & Auth
    "User",
    "UserProfile",
    "UserRole",
    "RefreshToken",
    "AuditLog",
    # Commesse
    "Commessa",
    "CommessaBase",
    "CommessaRead",
    "CommessaStato",
    "CommessaPreferences",
    "CommessaPreferencesBase",
    "CommessaPreferencesRead",
    # Computi
    "Computo",
    "ComputoBase",
    "ComputoRead",
    "ComputoTipo",
    "VoceComputo",
    "VoceBase",
    "VoceRead",
    "ImportConfig",
    "ImportConfigBase",
    "ImportConfigRead",
    # Catalog
    "PriceListItem",
    "PriceListOffer",
    "PropertyLexicon",
    "PropertyPattern",
    "PropertyOverride",
    "PropertyFeedback",
    # Settings
    "Settings",
    "SettingsBase",
    "SettingsRead",
]
