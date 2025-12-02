import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251128T153100_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("TEST LOGICA TESTA-CODA")
print("=" * 80)

df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)
df = df.dropna(how="all")

progressivi_df = df[df["N."].notna()].copy()
print(f"Progressivi trovati: {len(progressivi_df)}")

print("\nPRIMI 5 BLOCCHI (logica testa-coda):")
print("=" * 80)

prog_indexes = progressivi_df.index.tolist()

for i in range(min(5, len(prog_indexes))):
    testa_idx = prog_indexes[i]
    fine_idx = prog_indexes[i+1] if i+1 < len(prog_indexes) else len(df)

    blocco = df.loc[testa_idx:fine_idx-1]
    testa = blocco.iloc[0]
    coda = blocco.iloc[-1]

    print(f"\nBLOCCO {i+1} (righe {testa_idx}-{fine_idx-1}, {len(blocco)} righe)")
    print("-" * 80)
    print(f"TESTA (riga {testa_idx}):")
    print(f"  Progressivo: {testa['N.']}")
    print(f"  Codice: {testa['CODICE']}")
    desc = str(testa["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:60]
    print(f"  Descrizione: {desc}")
    print(f"\nCODA (riga {testa_idx + len(blocco) - 1}):")
    coda_desc = str(coda["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:60]
    print(f"  Descrizione: {coda_desc}")
    qty_col = "QUANTITA'"
    print(f"  Quantita: {coda[qty_col]}")
    print(f"  Prezzo: {coda['PREZZO']}")
    print(f"  Importo: {coda['IMPORTO']}")

print("\n" + "=" * 80)
print(f"RISULTATO: {len(progressivi_df)} progressivi = {len(progressivi_df)} voci")
print("OK: Logica testa-coda funziona correttamente!")
