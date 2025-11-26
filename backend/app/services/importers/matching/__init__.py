"""
Matching module - Sistema di allineamento e abbinamento voci.

Struttura modulare:
- config: Costanti e configurazione
- normalization: Normalizzazione token e text processing
- report: Generazione report e warning
- legacy: Logica di matching completa (da suddividere incrementalmente)

TODO: Migrare gradualmente funzioni da legacy.py a moduli dedicati:
- progressive.py: _align_progressive_return, logica matching progressivi
- description.py: _align_description_only_return, matching descrizioni
- pricelist.py: _match_price_list_item_*, _build_price_list_lookup
"""

# Re-export da legacy per retrocompatibilità
from .legacy import (
    # Main alignment functions
    _align_return_rows,
    _ReturnAlignmentResult,

    # Description/WBS utils
    _build_description_price_map,
    _has_progressivi,
    _sum_project_quantities,

    # Report building
    _build_matching_report,
    _build_lc_matching_report,
    _voce_label,
    _shorten_label,
    _format_quantity_value,

    # Validation
    _detect_duplicate_progressivi,
    _detect_forced_zero_violations,

    # Price list matching
    _build_price_list_lookup,
    _match_price_list_item_entry,
    _build_project_snapshot_from_price_offers,

    # Utils
    _prices_match,
    _log_unmatched_price_entries,
    _log_price_conflicts,
)

# Export nuovi moduli
from . import config
from . import normalization
from . import report

__all__ = [
    # Legacy exports (main functions)
    "_align_return_rows",
    "_ReturnAlignmentResult",
    "_build_description_price_map",
    "_has_progressivi",
    "_sum_project_quantities",
    "_build_matching_report",
    "_build_lc_matching_report",
    "_voce_label",
    "_shorten_label",
    "_format_quantity_value",
    "_detect_duplicate_progressivi",
    "_detect_forced_zero_violations",
    "_build_price_list_lookup",
    "_match_price_list_item_entry",
    "_build_project_snapshot_from_price_offers",
    "_prices_match",
    "_log_unmatched_price_entries",
    "_log_price_conflicts",

    # New modules
    "config",
    "normalization",
    "report",
]
