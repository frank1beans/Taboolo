"""Script per analizzare la discrepanza nel totale"""
import sys
sys.path.insert(0, 'c:/Users/f.biggi/Taboolo/backend')

from pathlib import Path
from decimal import Decimal
from sqlmodel import Session, select
from app.db import engine
from app.db.models import Computo, ComputoTipo, VoceComputo
from app.services.importers import parse_mc_return_excel

# File di ritorno
file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T171954_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("ANALISI DISCREPANZA TOTALE")
print("=" * 80)

# 1. Parse il file con head-tail
print("\n1. PARSING FILE (logica head-tail)...")
parsed = parse_mc_return_excel(
    file_path=file_path,
    sheet_name="3600 ES E EC 02b",
    code_columns=["CODICE"],
    description_columns=["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"],
    price_column="PREZZO",
    quantity_column="QUANTITA'",
    progressive_column="N.",
)

voci_parsed = parsed.computo.voci
totale_parsed = sum(Decimal(str(v.importo or 0)) for v in voci_parsed)

print(f"   Voci parsate: {len(voci_parsed)}")
print(f"   Totale importo parsed: €{totale_parsed:,.2f}")

# 2. Verifica totale da database
with Session(engine) as session:
    # Trova l'ultimo computo GARC importato
    computo_garc = session.exec(
        select(Computo)
        .where(
            Computo.commessa_id == 8,
            Computo.tipo == ComputoTipo.ritorno,
            Computo.impresa == "GARC",
        )
        .order_by(Computo.created_at.desc())
    ).first()

    if not computo_garc:
        print("\nERRORE: Computo GARC non trovato!")
        sys.exit(1)

    print(f"\n2. COMPUTO DATABASE (ID={computo_garc.id})...")
    print(f"   Importo totale DB: €{computo_garc.importo_totale:,.2f}")

    # Recupera voci
    voci_db = session.exec(
        select(VoceComputo)
        .where(VoceComputo.computo_id == computo_garc.id)
        .order_by(VoceComputo.ordine)
    ).all()

    print(f"   Voci nel DB: {len(voci_db)}")

    # Calcola totale dalle voci
    totale_voci_db = sum(Decimal(str(v.importo or 0)) for v in voci_db)
    print(f"   Totale da voci DB: €{totale_voci_db:,.2f}")

    # 3. Confronto
    print(f"\n{'=' * 80}")
    print("3. CONFRONTO:")
    print("-" * 80)
    print(f"   Atteso (utente):     €8,614,705.93")
    print(f"   Totale parsed:       €{totale_parsed:,.2f}")
    print(f"   Totale DB (campo):   €{computo_garc.importo_totale:,.2f}")
    print(f"   Totale DB (voci):    €{totale_voci_db:,.2f}")

    diff_atteso_parsed = Decimal("8614705.93") - totale_parsed
    diff_atteso_db = Decimal("8614705.93") - Decimal(str(computo_garc.importo_totale))
    diff_parsed_db = totale_parsed - totale_voci_db

    print(f"\n   Differenza atteso vs parsed: €{diff_atteso_parsed:,.2f}")
    print(f"   Differenza atteso vs DB:     €{diff_atteso_db:,.2f}")
    print(f"   Differenza parsed vs DB:     €{diff_parsed_db:,.2f}")

    # 4. Trova voci con discrepanze
    print(f"\n{'=' * 80}")
    print("4. ANALISI VOCI CON DIFFERENZE:")
    print("-" * 80)

    # Crea mapping per progressivo
    parsed_by_prog = {v.progressivo: v for v in voci_parsed if v.progressivo}
    db_by_prog = {v.progressivo: v for v in voci_db if v.progressivo}

    all_progs = set(parsed_by_prog.keys()) | set(db_by_prog.keys())

    discrepanze = []
    for prog in sorted(all_progs):
        v_parsed = parsed_by_prog.get(prog)
        v_db = db_by_prog.get(prog)

        if v_parsed and not v_db:
            discrepanze.append({
                'prog': prog,
                'tipo': 'SOLO_PARSED',
                'importo_parsed': v_parsed.importo,
                'importo_db': 0,
                'diff': v_parsed.importo or 0
            })
        elif v_db and not v_parsed:
            discrepanze.append({
                'prog': prog,
                'tipo': 'SOLO_DB',
                'importo_parsed': 0,
                'importo_db': v_db.importo,
                'diff': -(v_db.importo or 0)
            })
        elif v_parsed and v_db:
            imp_p = Decimal(str(v_parsed.importo or 0))
            imp_db = Decimal(str(v_db.importo or 0))
            diff = imp_p - imp_db

            if abs(diff) > Decimal("0.01"):
                discrepanze.append({
                    'prog': prog,
                    'tipo': 'DIFFERENZA',
                    'importo_parsed': float(imp_p),
                    'importo_db': float(imp_db),
                    'diff': float(diff),
                    'codice': v_parsed.codice or v_db.codice,
                })

    if discrepanze:
        print(f"\nTrovate {len(discrepanze)} voci con discrepanze:")

        # Ordina per differenza assoluta
        discrepanze.sort(key=lambda x: abs(x['diff']), reverse=True)

        for i, disc in enumerate(discrepanze[:20]):  # Prime 20
            print(f"\n{i+1}. Progressivo {disc['prog']} [{disc['tipo']}]:")
            if disc['tipo'] == 'DIFFERENZA':
                print(f"   Codice: {disc.get('codice', 'N/A')}")
            print(f"   Importo parsed: €{disc['importo_parsed']:,.2f}")
            print(f"   Importo DB:     €{disc['importo_db']:,.2f}")
            print(f"   Differenza:     €{disc['diff']:,.2f}")

        # Totale differenze
        totale_diff = sum(Decimal(str(d['diff'])) for d in discrepanze)
        print(f"\n   TOTALE DIFFERENZE: €{totale_diff:,.2f}")
    else:
        print("\nNessuna discrepanza trovata tra parsed e DB!")

print(f"\n{'=' * 80}")
print("CONCLUSIONE:")

if abs(diff_atteso_parsed) < Decimal("0.01"):
    print("  Il parser estrae il totale corretto!")
    print("  Il problema è nell'allineamento/salvataggio nel DB")
elif abs(diff_atteso_db) < Decimal("0.01"):
    print("  Il DB contiene il totale corretto!")
    print("  Il problema era nel parser (ora risolto)")
else:
    print(f"  C'è ancora una discrepanza di €{diff_atteso_db:,.2f}")
    print("  Servono ulteriori indagini")
