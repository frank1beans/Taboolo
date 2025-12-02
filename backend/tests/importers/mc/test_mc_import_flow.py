"""Test per verificare import MC completo"""
import sys
sys.path.insert(0, 'c:/Users/f.biggi/Taboolo/backend')

from pathlib import Path
from collections import defaultdict
from sqlmodel import Session, create_engine, select
from app.db import get_session
from app.db.models import Computo, ComputoTipo, VoceComputo
from app.excel import parse_computo_excel

# Parse file ritorno
file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T110901_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("TEST IMPORT MC - ANALISI PREZZI MANCANTI")
print("=" * 80)

# Parse il file ritorno
print("\n1. PARSING FILE RITORNO...")
parsed = parse_computo_excel(
    file_path,
    sheet_name="3600 ES E EC 02b",
    price_column="PREZZO",
    quantity_column="QUANTITA'",
)

print(f"   Totale voci parsed: {len(parsed.voci)}")

# Conta voci senza prezzo nel file parsato
no_price_parsed = [v for v in parsed.voci if v.prezzo_unitario is None]
print(f"   Voci senza prezzo nel file parsato: {len(no_price_parsed)}")

# Raggruppa per codice
by_code = defaultdict(list)
for voce in parsed.voci:
    if voce.codice and voce.progressivo:
        by_code[voce.codice].append({
            'progressivo': voce.progressivo,
            'prezzo': voce.prezzo_unitario,
            'quantita': voce.quantita
        })

multi_prog_codes = {code: items for code, items in by_code.items() if len(items) > 1}
print(f"   Codici con progressivi multipli: {len(multi_prog_codes)}")

# Esempi
print("\n2. ESEMPI CODICI CON PROGRESSIVI MULTIPLI:")
print("-" * 80)
for i, (code, items) in enumerate(list(multi_prog_codes.items())[:5]):
    print(f"\n   Codice: {code} ({len(items)} progressivi)")
    for item in items[:3]:
        status = "OK" if item['prezzo'] is not None else "MISSING"
        print(f"     - Prog {item['progressivo']}: prezzo={item['prezzo']} [{status}]")

# Adesso simuliamo l'import come fa il servizio MC
print(f"\n{'=' * 80}")
print("3. SIMULAZIONE IMPORT (dal database)...")
print("-" * 80)

# Connetti al database
from app.db import engine_from_env
engine = engine_from_env()

with Session(engine) as session:
    # Recupera computo progetto
    computo_progetto = session.exec(
        select(Computo)
        .where(
            Computo.commessa_id == 8,
            Computo.tipo == ComputoTipo.progetto,
        )
        .order_by(Computo.created_at.desc())
    ).first()

    if not computo_progetto:
        print("   ERRORE: Computo progetto non trovato per commessa 8")
        sys.exit(1)

    print(f"   Computo progetto ID: {computo_progetto.id}")

    # Recupera voci progetto
    voci_progetto = session.exec(
        select(VoceComputo)
        .where(VoceComputo.computo_id == computo_progetto.id)
        .order_by(VoceComputo.ordine)
    ).all()

    print(f"   Voci progetto: {len(voci_progetto)}")

    # Trova voci progetto con progressivi che hanno stesso codice
    progetto_by_code = defaultdict(list)
    for voce in voci_progetto:
        if voce.codice and voce.progressivo:
            progetto_by_code[voce.codice].append({
                'progressivo': voce.progressivo,
                'prezzo': voce.prezzo_unitario,
            })

    multi_prog_project = {code: items for code, items in progetto_by_code.items() if len(items) > 1}
    print(f"   Codici con progressivi multipli nel progetto: {len(multi_prog_project)}")

    # Ora facciamo il matching come fa il servizio
    print(f"\n4. MATCHING PROGRESSIVI...")
    print("-" * 80)

    # Crea index dei progressivi del ritorno
    ritorno_by_prog = {}
    for voce in parsed.voci:
        if voce.progressivo:
            ritorno_by_prog[voce.progressivo] = voce

    print(f"   Progressivi nel ritorno: {len(ritorno_by_prog)}")

    # Verifica matching per codici con progressivi multipli
    print(f"\n5. VERIFICA PREZZI PER CODICI CON PROGRESSIVI MULTIPLI:")
    print("-" * 80)

    # Prendi i primi 10 codici con progressivi multipli
    test_codes = list(multi_prog_project.items())[:10]

    for code, prog_items in test_codes:
        print(f"\n   Codice: {code}")
        print(f"   Progressivi: {[item['progressivo'] for item in prog_items]}")

        for item in prog_items:
            prog = item['progressivo']
            prog_price = item['prezzo']

            ritorno_voce = ritorno_by_prog.get(prog)
            if ritorno_voce:
                ritorno_price = ritorno_voce.prezzo_unitario
                status = "OK" if ritorno_price is not None else "MISSING!"
                print(f"     Prog {prog}: progetto={prog_price}, ritorno={ritorno_price} [{status}]")
            else:
                print(f"     Prog {prog}: NOT FOUND IN RETURN")

print(f"\n{'=' * 80}")
print("OK: Test completato!")
