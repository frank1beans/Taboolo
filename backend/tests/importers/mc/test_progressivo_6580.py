"""Analisi progressivo 6580 (L037.040.05)"""
import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T171954_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("ANALISI PROGRESSIVO 6580 (L037.040.05)")
print("=" * 80)

# Leggi il foglio Excel
df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)

# Trova il progressivo 6580
prog_col = "N."
progressivi_df = df[df[prog_col].notna()].copy()

prog_6580_idx = progressivi_df[progressivi_df[prog_col] == 6580].index

if len(prog_6580_idx) == 0:
    print("ERRORE: Progressivo 6580 non trovato!")
    exit(1)

testa_idx = prog_6580_idx[0]
print(f"Progressivo 6580 trovato alla riga {testa_idx}")

# Trova il prossimo progressivo (o fine file)
all_prog_indexes = progressivi_df.index.tolist()
testa_pos = all_prog_indexes.index(testa_idx)

if testa_pos + 1 < len(all_prog_indexes):
    fine_idx = all_prog_indexes[testa_pos + 1]
    print(f"Prossimo progressivo alla riga {fine_idx}")
else:
    fine_idx = len(df)
    print(f"Ultimo progressivo - fino a fine file (riga {fine_idx})")

print(f"Blocco: righe {testa_idx} - {fine_idx-1} ({fine_idx - testa_idx} righe)")

# Estrai il blocco
blocco = df.loc[testa_idx:fine_idx-1]

print(f"\nCONTENUTO BLOCCO COMPLETO:")
print("=" * 80)

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

# LOGICA HEAD-TAIL
print(f"\n{'=' * 80}")
print("LOGICA TESTA-CODA:")
print("-" * 80)

testa = blocco.iloc[0]
print(f"\nTESTA (riga {testa_idx}):")
print(f"  Progressivo: {testa[prog_col]}")
print(f"  Codice: {testa['CODICE']}")

print(f"\nCERCO CODA (ultima riga con qty o price)...")

coda_row = None
coda_idx = None

for idx in reversed(range(len(blocco))):
    row = blocco.iloc[idx]
    qty = row[qty_col]
    price = row['PREZZO']

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
    print(f"  Descrizione: {str(coda_row['INDICAZIONE DEI LAVORI E DELLE PROVVISTE'])[:60]}")
    print(f"  Quantità: {coda_row[qty_col]}")
    print(f"  Prezzo: {coda_row['PREZZO']}")
    print(f"  Importo: {coda_row['IMPORTO']}")

    if pd.notna(coda_row[qty_col]) and pd.notna(coda_row['PREZZO']):
        calc = coda_row[qty_col] * coda_row['PREZZO']
        print(f"\n  IMPORTO CALCOLATO: {calc:.2f}")
        print(f"  IMPORTO IN EXCEL: {coda_row['IMPORTO']:.2f}")
else:
    print("\nERRORE: CODA NON TROVATA!")
