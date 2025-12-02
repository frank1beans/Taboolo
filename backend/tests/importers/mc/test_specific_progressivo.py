"""Test per analizzare progressivo specifico con prezzo mancante"""
import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T110901_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("ANALISI PROGRESSIVO 2170 (codice 1C.01.800.0130)")
print("=" * 80)

# Leggi il foglio Excel
df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)

# Trova il blocco del progressivo 2170
prog_col = "N."
progressivi_df = df[df[prog_col].notna()].copy()

# Trova l'indice del progressivo 2170
prog_2170_idx = progressivi_df[progressivi_df[prog_col] == 2170].index

if len(prog_2170_idx) == 0:
    print("ERRORE: Progressivo 2170 non trovato!")
    exit(1)

testa_idx = prog_2170_idx[0]
print(f"Progressivo 2170 trovato alla riga {testa_idx}")

# Trova il prossimo progressivo
all_prog_indexes = progressivi_df.index.tolist()
testa_pos = all_prog_indexes.index(testa_idx)

if testa_pos + 1 < len(all_prog_indexes):
    fine_idx = all_prog_indexes[testa_pos + 1]
else:
    fine_idx = len(df)

print(f"Blocco va dalla riga {testa_idx} alla riga {fine_idx - 1} ({fine_idx - testa_idx} righe)")

# Estrai il blocco
blocco = df.loc[testa_idx:fine_idx-1]

print(f"\nCONTENUTO BLOCCO:")
print("-" * 80)

qty_col = "QUANTITA'"
for idx, row in blocco.iterrows():
    print(f"\nRiga {idx}:")
    print(f"  N.: {row[prog_col]}")
    print(f"  CODICE: {row['CODICE']}")
    desc = str(row["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:80]
    print(f"  DESCRIZIONE: {desc}")
    print(f"  QUANTITA': {row[qty_col]}")
    print(f"  PREZZO: {row['PREZZO']}")
    print(f"  IMPORTO: {row['IMPORTO']}")

print(f"\n{'=' * 80}")
print("ANALISI LOGICA TESTA-CODA:")
print("-" * 80)

testa = blocco.iloc[0]
print(f"\nTESTA (riga {testa_idx}):")
print(f"  Progressivo: {testa[prog_col]}")
print(f"  Codice: {testa['CODICE']}")
print(f"  Descrizione: {str(testa['INDICAZIONE DEI LAVORI E DELLE PROVVISTE'])[:60]}")

print(f"\nCERCO CODA (ultima riga con quantità o prezzo)...")
coda_idx = None
coda_row = None

for idx in reversed(range(len(blocco))):
    row = blocco.iloc[idx]
    qty = row[qty_col]
    price = row["PREZZO"]

    print(f"  Riga {blocco.index[idx]}: qty={qty}, price={price}", end="")

    if pd.notna(qty) or pd.notna(price):
        print(" <-- CODA TROVATA!")
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
else:
    print("\nERRORE: CODA NON TROVATA!")

print(f"\n{'=' * 80}")
print("CONCLUSIONE:")
if coda_row is not None and pd.isna(coda_row["PREZZO"]):
    print(f"  PROBLEMA: La CODA ha PREZZO=NaN!")
    print(f"  Quantità coda: {coda_row[qty_col]}")
    print(f"  Importo coda: {coda_row['IMPORTO']}")
    if pd.notna(coda_row['IMPORTO']) and pd.notna(coda_row[qty_col]):
        qty = coda_row[qty_col]
        importo = coda_row['IMPORTO']
        if qty != 0:
            prezzo_calc = importo / qty
            print(f"  PREZZO CALCOLATO da importo/qty: {prezzo_calc:.4f}")
else:
    print("  OK")
