"""Analisi dell'ultimo progressivo del file"""
import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T171954_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("ANALISI ULTIMO PROGRESSIVO (L037.040.05)")
print("=" * 80)

# Leggi il foglio Excel
df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)
df = df.dropna(how="all")

print(f"Totale righe nel foglio: {len(df)}")

# Trova tutti i progressivi
prog_col = "N."
progressivi_df = df[df[prog_col].notna()].copy()
print(f"Totale progressivi: {len(progressivi_df)}")

# Trova l'ultimo progressivo
ultimo_prog_idx = progressivi_df.index[-1]
ultimo_prog_value = progressivi_df.iloc[-1][prog_col]

print(f"\nUltimo progressivo: {ultimo_prog_value}")
print(f"Indice riga: {ultimo_prog_idx}")

# Estrai il blocco dell'ultimo progressivo (fino alla fine del file)
blocco = df.loc[ultimo_prog_idx:]

print(f"\nBLOCCO ULTIMO PROGRESSIVO ({len(blocco)} righe totali):")
print("=" * 80)

qty_col = "QUANTITA'"
for idx, row in blocco.iterrows():
    print(f"\nRiga {idx}:")
    print(f"  N.: {row[prog_col]}")
    print(f"  CODICE: {row['CODICE']}")
    desc = str(row["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])
    if len(desc) > 100:
        desc = desc[:100] + "..."
    print(f"  DESCRIZIONE: {desc}")
    print(f"  QUANTITA': {row[qty_col]}")
    print(f"  PREZZO: {row['PREZZO']}")
    print(f"  IMPORTO: {row['IMPORTO']}")

# STEP 1: PULIZIA PRELIMINARE (simula il parser)
print(f"\n{'=' * 80}")
print("STEP 1: PULIZIA PRELIMINARE")
print("-" * 80)

cleaned_rows = []
for idx, row in blocco.iterrows():
    codice = row['CODICE']
    desc = row["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"]
    qty = row[qty_col]
    price = row['PREZZO']
    prog = row[prog_col]

    # Salta righe completamente vuote
    has_any_value = (
        pd.notna(codice) or pd.notna(desc) or
        pd.notna(qty) or pd.notna(price) or pd.notna(prog)
    )
    if not has_any_value:
        print(f"Riga {idx}: SALTATA (completamente vuota)")
        continue

    # Elimina righe "Totale ..." senza progressivo
    if pd.notna(desc) and str(desc).lower().startswith("totale ") and pd.isna(prog):
        print(f"Riga {idx}: SALTATA (Totale senza progressivo)")
        continue

    # Elimina righe di titolo capitolo
    has_code_or_desc = pd.notna(codice) or pd.notna(desc)
    has_no_data = pd.isna(prog) and pd.isna(qty) and pd.isna(price)

    if has_code_or_desc and has_no_data:
        print(f"Riga {idx}: SALTATA (titolo capitolo)")
        continue

    print(f"Riga {idx}: MANTENUTA")
    cleaned_rows.append((idx, row))

print(f"\nRighe dopo pulizia: {len(cleaned_rows)}")

# STEP 2: TROVA CODA
print(f"\n{'=' * 80}")
print("STEP 2: CERCA CODA (ultima riga con qty o price)")
print("-" * 80)

coda_row = None
coda_idx = None

for idx, row in reversed(cleaned_rows):
    qty = row[qty_col]
    price = row['PREZZO']

    print(f"Riga {idx}: qty={qty}, price={price}", end="")

    if pd.notna(qty) or pd.notna(price):
        print(" <-- CODA TROVATA!")
        coda_idx = idx
        coda_row = row
        break
    else:
        print()

if coda_row is not None:
    print(f"\n{'=' * 80}")
    print("CODA TROVATA:")
    print(f"  Riga: {coda_idx}")
    print(f"  Codice: {coda_row['CODICE']}")
    print(f"  Descrizione: {str(coda_row['INDICAZIONE DEI LAVORI E DELLE PROVVISTE'])[:80]}")
    print(f"  Quantità: {coda_row[qty_col]}")
    print(f"  Prezzo: {coda_row['PREZZO']}")
    print(f"  Importo: {coda_row['IMPORTO']}")

    # Verifica
    if pd.notna(coda_row['PREZZO']) and pd.notna(coda_row[qty_col]):
        importo_calc = coda_row[qty_col] * coda_row['PREZZO']
        print(f"\n  IMPORTO CALCOLATO: {importo_calc:.2f}")
        if pd.notna(coda_row['IMPORTO']):
            diff = abs(importo_calc - coda_row['IMPORTO'])
            if diff > 0.01:
                print(f"  ATTENZIONE: Differenza con Excel: {diff:.2f}")
else:
    print("\nERRORE: CODA NON TROVATA!")
    print("Il parser restituirebbe prezzo=None per questo progressivo!")
