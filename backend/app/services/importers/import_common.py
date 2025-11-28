"""
Funzioni comuni condivise tra LcImportService e McImportService.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Sequence

from app.db.models import VoceComputo
from app.excel import ParsedVoce
from app.services.importers.common import _ceil_amount

logger = logging.getLogger(__name__)


def _build_parsed_from_progetto(
    voce: VoceComputo,
    quantita: float | None,
    prezzo_unitario: float | None,
    importo: float | None,
) -> ParsedVoce:
    """
    Costruisce un ParsedVoce da una VoceComputo del progetto.

    Funzione comune usata sia da LC che da MC per creare voci del computo ritorno
    basandosi su voci del computo progetto.
    """
    wbs_levels = []
    for level in range(1, 8):  # WBS levels 1-7
        code = getattr(voce, f"wbs_{level}_code", None)
        desc = getattr(voce, f"wbs_{level}_description", None)
        if code or desc:
            wbs_levels.append({
                "level": level,
                "code": code,
                "description": desc,
            })

    return ParsedVoce(
        ordine=voce.ordine,
        progressivo=voce.progressivo,
        codice=voce.codice,
        descrizione=voce.descrizione,
        wbs_levels=wbs_levels,
        unita_misura=voce.unita_misura,
        quantita=quantita,
        prezzo_unitario=prezzo_unitario,
        importo=importo,
        note=voce.note,
        metadata=voce.extra_metadata,
    )


def calculate_total_import(voci: Sequence[ParsedVoce]) -> float:
    """
    Calcola l'importo totale di un computo da una lista di voci.

    Args:
        voci: Lista di voci parsed

    Returns:
        Importo totale arrotondato
    """
    if not voci:
        return 0.0

    total = sum(
        Decimal(str(voce.importo))
        for voce in voci
        if voce.importo is not None
    )
    return float(_ceil_amount(total))


def validate_progetto_voci(voci: Sequence[VoceComputo]) -> None:
    """
    Valida che le voci del computo progetto siano utilizzabili.

    Raises:
        ValueError: Se le voci non sono valide
    """
    if not voci:
        raise ValueError("Il computo metrico (MC) non contiene voci importabili")

    # Verifica che ci siano progressivi
    progressivi = [v.progressivo for v in voci if v.progressivo is not None]
    if not progressivi:
        logger.warning("Nessun progressivo trovato nelle voci del computo progetto")

    # Verifica product_id nei metadata
    voci_con_product_id = 0
    for voce in voci:
        metadata = voce.extra_metadata or {}
        if isinstance(metadata, dict) and metadata.get("product_id"):
            voci_con_product_id += 1

    if voci_con_product_id == 0:
        logger.warning("Nessuna voce con product_id trovata nei metadata")
    else:
        logger.info(
            f"Voci con product_id: {voci_con_product_id}/{len(voci)} "
            f"({voci_con_product_id/len(voci)*100:.1f}%)"
        )
