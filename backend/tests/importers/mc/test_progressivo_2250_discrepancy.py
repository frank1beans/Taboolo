"""Riproduce la discrepanza di quantità/prezzo per 1C.00.700.0030.b nel flusso MC."""
import sys
from pathlib import Path

from sqlmodel import Session, select

sys.path.insert(0, "c:/Users/f.biggi/Taboolo/backend")

from app.db import engine  # noqa: E402
from app.db.models import Computo, ComputoTipo, VoceComputo  # noqa: E402
from app.services.importers import parse_mc_return_excel  # noqa: E402
from app.services.importers.matching import (  # noqa: E402
    _align_return_rows,
    _build_description_price_map,
    _has_progressivi,
)
from app.services.importers.matching.legacy import (  # noqa: E402
    _align_progressive_return,
    _build_return_index,
    _wbs_base_key_from_parsed,
    _wbs_key_from_model,
)

FILE_PATH = Path(
    r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251201T160329_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx"
)
TARGET_PROGRESSIVI = (2230, 2250)

print("TEST DISCREPANZA MC - CODICE 1C.00.700.0030.b (progressivo 2250)")
print("=" * 80)

# 1) Parse ritorno MC con la stessa colonna usata per GARC (PU GARC)
parsed = parse_mc_return_excel(
    file_path=FILE_PATH,
    sheet_name="3600 ES E EC 02b",
    code_columns=["CODICE"],
    description_columns=["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"],
    price_column="PU GARC",
    quantity_column="QUANTITA'",
    progressive_column="N.",
)
ritorno_subset = [v for v in parsed.computo.voci if v.progressivo in TARGET_PROGRESSIVI]
expected_2250 = next(v for v in ritorno_subset if v.progressivo == 2250)

print("\nVALORI ESTRATTI DAL FILE (solo progressivi 2230 e 2250):")
for voce in ritorno_subset:
    print(
        f"  Prog {voce.progressivo}: codice={voce.codice}, "
        f"qty={voce.quantita}, price={voce.prezzo_unitario}, importo={voce.importo}"
    )

with Session(engine) as session:
    computo_base = session.exec(
        select(Computo)
        .where(
            Computo.commessa_id == 8,
            Computo.tipo == ComputoTipo.progetto,
        )
        .order_by(Computo.created_at.desc())
    ).first()

    progetto_subset = session.exec(
        select(VoceComputo)
        .where(
            VoceComputo.computo_id == computo_base.id,
            VoceComputo.progressivo.in_(TARGET_PROGRESSIVI),
        )
        .order_by(VoceComputo.ordine)
    ).all()

    print("\nVALORI DEL COMPUTO DI PROGETTO:")
    for voce in progetto_subset:
        print(
            f"  Prog {voce.progressivo}: codice={voce.codice}, "
            f"qty={voce.quantita}, price={voce.prezzo_unitario}, importo={voce.importo}"
        )

    print("\nWBS vs BASE KEY (motivo dello skip dei progressivi):")
    for voce in progetto_subset:
        ritorno = next(v for v in ritorno_subset if v.progressivo == voce.progressivo)
        print(
            f"  Prog {voce.progressivo}: project_wbs={_wbs_key_from_model(voce)}, "
            f"return_base={_wbs_base_key_from_parsed(ritorno)}"
        )

    # 2) Allineamento progressivo puro: matched_count = 0 -> scatta il fallback
    index, wrappers = _build_return_index(ritorno_subset)
    progressive_result = _align_progressive_return(
        progetto_subset,
        index,
        wrappers,
    )
    print(f"\nProgressive match count: {progressive_result.matched_count}")
    for voce in progressive_result.voci_allineate:
        if voce.progressivo in TARGET_PROGRESSIVI:
            print(
                f"  Prog {voce.progressivo}: qty={voce.quantita}, "
                f"price={voce.prezzo_unitario}, metadata={voce.metadata}"
            )

    # 3) Allineamento effettivo della pipeline (fallback per descrizione)
    alignment = _align_return_rows(
        progetto_subset,
        ritorno_subset,
        prefer_progressivi=_has_progressivi(ritorno_subset),
        description_price_map=_build_description_price_map(ritorno_subset),
    )

print("\nRISULTATO DELLA PIPELINE (allineamento progressivo attivo):")
for voce in alignment.voci_allineate:
    if voce.progressivo in TARGET_PROGRESSIVI:
        print(
            f"  Prog {voce.progressivo}: qty={voce.quantita}, "
            f"price={voce.prezzo_unitario}, importo={voce.importo}"
        )

# 4) Stato attuale nel DB per l'import GARC
garc_return = session.exec(
    select(Computo)
    .where(
        Computo.commessa_id == 8,
        Computo.tipo == ComputoTipo.ritorno,
        Computo.impresa == "GARC",
    )
    .order_by(Computo.created_at.desc())
).first()
voce_db = session.exec(
    select(VoceComputo)
    .where(
        VoceComputo.computo_id == garc_return.id,
        VoceComputo.progressivo == 2250,
    )
).first()

print("\nVALORE SALVATO NEL DB (GARC):")
print(
    f"  Prog 2250 DB: qty={voce_db.quantita}, price={voce_db.prezzo_unitario}, "
    f"importo={voce_db.importo}"
)

print("\nCONFRONTO FINALE:")
print(
    f"  Atteso dal file per prog 2250: qty={expected_2250.quantita}, "
    f"price={expected_2250.prezzo_unitario}"
)
if progressive_result.matched_count == 0:
    print(
        "  AVVISO: senza match su progressivo, la pipeline sarebbe tornata al "
        "fallback per descrizione (scambio 2230/2250)."
    )
else:
    print("  OK: ora i progressivi vengono agganciati direttamente, niente fallback.")
