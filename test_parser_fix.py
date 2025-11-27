#!/usr/bin/env python
"""Test del fix per righe intermedie con solo quantità"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Import diretto per evitare circular imports
from app.services.importers import parser
_parse_custom_return_excel = parser._parse_custom_return_excel

# Test con file GARC
file_path = Path("backend/storage/commessa_0008/uploads/20251127T150324_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("="*80)
print("TEST PARSER MC CON FIX")
print("="*80)
print(f"File: {file_path.name}")
print()

try:
    result = _parse_custom_return_excel(
        file_path=file_path,
        sheet_name="3600 ES E EC 02b",
        code_columns=["CODICE"],
        description_columns=["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"],
        price_column="PU GARC",
        quantity_column="QUANTITA'",
        progressive_column="N.",
        combine_totals=True,  # MC mode
    )

    print(f"Parsing completato!")
    print(f"Voci trovate: {len(result.voci)}")

    # Analizza voci
    with_price = sum(1 for v in result.voci if v.prezzo_unitario and v.prezzo_unitario > 0)
    no_price = sum(1 for v in result.voci if not v.prezzo_unitario or v.prezzo_unitario == 0)

    print(f"  Con prezzo > 0: {with_price} ({100*with_price/len(result.voci) if result.voci else 0:.1f}%)")
    print(f"  Con prezzo = 0: {no_price} ({100*no_price/len(result.voci) if result.voci else 0:.1f}%)")

    # Cerca progressivo #10 (caso problematico)
    voce_10 = next((v for v in result.voci if v.progressivo == 10), None)
    if voce_10:
        print(f"\nProgressivo #10 (caso test):")
        print(f"  Codice: {voce_10.codice}")
        print(f"  Descrizione: {voce_10.descrizione[:50]}")
        print(f"  Quantita: {voce_10.quantita}")
        print(f"  Prezzo: {voce_10.prezzo_unitario}")
        if voce_10.prezzo_unitario and voce_10.prezzo_unitario > 0:
            print(f"  ✅ FIX FUNZIONA! Prezzo trovato.")
        else:
            print(f"  ❌ FIX NON FUNZIONA. Prezzo ancora a zero.")
    else:
        print(f"\n⚠️ Progressivo #10 non trovato nel parsing")

    # Altri progressivi test
    test_progs = [10, 20, 30, 2230, 2240, 2250]
    print(f"\nTest progressivi specifici:")
    for prog in test_progs:
        voce = next((v for v in result.voci if v.progressivo == prog), None)
        if voce:
            status = "✅" if voce.prezzo_unitario and voce.prezzo_unitario > 0 else "❌"
            price_str = f"EUR {voce.prezzo_unitario:.2f}" if voce.prezzo_unitario else "EUR 0.00"
            print(f"  {status} #{prog:5d}: {price_str:12s} | Q={voce.quantita or 'N/A':8s} | {voce.codice or 'N/A'}")
        else:
            print(f"  ⚠️  #{prog:5d}: NON TROVATO")

    print("\n" + "="*80)
    print("Test completato!")
    print("="*80)

except Exception as e:
    print(f"\n❌ ERRORE:")
    print(f"  {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
