from pathlib import Path
from typing import Sequence

from app.services.importers.parser import _parse_custom_return_excel, _CustomReturnParseResult


def parse_mc_return_excel(
    file_path: Path,
    sheet_name: str | None,
    code_columns: Sequence[str],
    description_columns: Sequence[str],
    price_column: str,
    quantity_column: str | None = None,
    progressive_column: str | None = None,
) -> _CustomReturnParseResult:
    """Wrapper esplicito per il parser MC (combine_totals=True)."""
    return _parse_custom_return_excel(
        file_path,
        sheet_name,
        code_columns,
        description_columns,
        price_column,
        quantity_column,
        progressive_column,
        combine_totals=True,
    )
