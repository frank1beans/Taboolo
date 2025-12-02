"""Analisi del progressivo 2640 che ha discrepanza enorme"""
import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T171954_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("ANALISI PROGRESSIVO 2640")
print("=" * 80)

# Leggi il foglio Excel
df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)

# Trova il blocco del progressivo 2640
prog_col = "N."
progressivi_df = df[df[prog_col].notna()].copy()

# Trova l'indice del progressivo 2640
prog_idx = progressivi_df[progressivi_df[prog_col] == 2640].index

if len(prog_idx) == 0:
    print("ERRORE: Progressivo 2640 non trovato!")
    exit(1)

testa_idx = prog_idx[0]
print(f"Progressivo 2640 trovato alla riga {testa_idx}")

# Trova il prossimo progressivo
all_prog_indexes = progressivi_df.index.tolist()
testa_pos = all_prog_indexes.index(testa_idx)

if testa_pos + 1 < len(all_prog_indexes):
    fine_idx = all_prog_indexes[testa_pos + 1]
else:
    fine_idx = len(df)

print(f"Blocco va dalla riga {testa_idx} alla riga {fine_idx - 1}")

# Estrai il blocco
blocco = df.loc[testa_idx:fine_idx-1]

print(f"\nCONTENUTO BLOCCO ({len(blocco)} righe):")
print("-" * 80)

qty_col = "QUANTITA'"
for idx, row in blocco.iterrows():
    print(f"\nRiga {idx}:")
    print(f"  N.: {row[prog_col]}")
    print(f"  CODICE: {row['CODICE']}")
    desc = str(row["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:100]
    print(f"  DESCRIZIONE: {desc}")
    print(f"  QUANTITA': {row[qty_col]}")
    print(f"  PREZZO: {row['PREZZO']}")
    print(f"  IMPORTO: {row['IMPORTO']}")

print(f"\n{'=' * 80}")
print("LOGICA TESTA-CODA:")
print("-" * 80)

testa = blocco.iloc[0]
print(f"\nTESTA (riga {testa_idx}):")
print(f"  Progressivo: {testa[prog_col]}")
print(f"  Codice: {testa['CODICE']}")
desc = str(testa["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])
print(f"  Descrizione: {desc[:200]}")

print(f"\nCERCO CODA (ultima riga con quantità o prezzo)...")
coda_idx = None
coda_row = None

for idx in reversed(range(len(blocco))):
    row = blocco.iloc[idx]
    qty = row[qty_col]
    price = row["PREZZO"]

    print(f"  Riga {blocco.index[idx]}: qty={qty}, price={price}", end="")

    if pd.notna(qty) or pd.notna(price):
        print(" <-- CODA!")
        coda_idx = blocco.index[idx]
        coda_row = row
        break
    else:
        print()

if coda_row is not None:
    print(f"\nCODA (riga {coda_idx}):")
    print(f"  Descrizione: {str(coda_row['INDICAZIONE DEI LAVORI E DELLE PROVVISTE'])[:100]}")
    print(f"  Quantità: {coda_row[qty_col]}")
    print(f"  Prezzo: {coda_row['PREZZO']}")
    print(f"  Importo: {coda_row['IMPORTO']}")

    # Calcola importo atteso
    if pd.notna(coda_row[qty_col]) and pd.notna(coda_row['PREZZO']):
        qty_val = coda_row[qty_col]
        price_val = coda_row['PREZZO']
        importo_calc = qty_val * price_val
        print(f"\n  IMPORTO CALCOLATO (qty * prezzo): {importo_calc:.2f}")

        if pd.notna(coda_row['IMPORTO']):
            diff = abs(importo_calc - coda_row['IMPORTO'])
            if diff > 0.01:
                print(f"  ATTENZIONE: Differenza con importo in Excel: {diff:.2f}")
else:
    print("\nERRORE: CODA NON TROVATA!")

print(f"\n{'=' * 80}")
print("CONCLUSIONE:")
print(f"  Il parser estrae dalla CODA:")
print(f"    - Quantità: {coda_row[qty_col] if coda_row is not None else 'N/A'}")
print(f"    - Prezzo: {coda_row['PREZZO'] if coda_row is not None else 'N/A'}")
print(f"    - Importo: {coda_row['IMPORTO'] if coda_row is not None else 'N/A'}")

if coda_row is not None:
    if pd.isna(coda_row['PREZZO']) and pd.isna(coda_row['IMPORTO']):
        print(f"\n  PROBLEMA: La CODA non ha né PREZZO né IMPORTO!")
        print(f"  Il parser dovrebbe restituire importo=0")
        print(f"  Ma il DB ha €604,999.75 - da dove viene?")
