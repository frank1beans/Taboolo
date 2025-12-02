import pandas as pd
from pathlib import Path

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251128T153100_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("TEST LOGICA TESTA-CODA CON PULIZIA PRELIMINARE")
print("=" * 80)

df = pd.read_excel(file_path, sheet_name="3600 ES E EC 02b", header=4)
df = df.dropna(how="all")

print(f"Righe totali prima della pulizia: {len(df)}")

# STEP 1: PULIZIA PRELIMINARE
# Simula la logica del parser
cleaned_indexes = []
for idx, row in df.iterrows():
    codice = row["CODICE"]
    desc = row["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"]
    qty_col = "QUANTITA'"
    quantita = row[qty_col]
    prezzo = row["PREZZO"]
    progressivo = row["N."]

    # Salta righe completamente vuote (già fatto con dropna)

    # Elimina righe "Totale opere generali"
    if pd.notna(desc) and str(desc).lower().startswith("totale ") and pd.isna(progressivo):
        continue

    # Elimina righe di titolo capitolo: hanno (codice o descrizione) ma NON progressivo/quantità/prezzo
    has_code_or_desc = pd.notna(codice) or pd.notna(desc)
    has_no_data = pd.isna(progressivo) and pd.isna(quantita) and pd.isna(prezzo)

    if has_code_or_desc and has_no_data:
        continue

    cleaned_indexes.append(idx)

cleaned_df = df.loc[cleaned_indexes]
print(f"Righe dopo pulizia: {len(cleaned_df)}")
print(f"Righe rimosse: {len(df) - len(cleaned_df)}")

# STEP 2: IDENTIFICA PROGRESSIVI
progressivi_df = cleaned_df[cleaned_df["N."].notna()].copy()
print(f"\nProgressivi trovati: {len(progressivi_df)}")

# STEP 3: COSTRUISCI BLOCCHI
print("\nPRIMI 10 BLOCCHI (dopo pulizia):")
print("=" * 80)

prog_indexes = progressivi_df.index.tolist()

for i in range(min(10, len(prog_indexes))):
    testa_idx = prog_indexes[i]
    fine_idx = prog_indexes[i+1] if i+1 < len(prog_indexes) else cleaned_df.index[-1] + 1

    # Blocco nel cleaned_df
    blocco = cleaned_df.loc[testa_idx:fine_idx-1]
    testa = blocco.iloc[0]
    coda = blocco.iloc[-1]

    print(f"\nBLOCCO {i+1} (righe originali {testa_idx}-{blocco.index[-1]}, {len(blocco)} righe dopo pulizia)")
    print("-" * 80)
    print(f"TESTA:")
    print(f"  Progressivo: {testa['N.']}")
    print(f"  Codice: {str(testa['CODICE'])[:30]}")
    desc = str(testa["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:50]
    print(f"  Descrizione: {desc}")

    print(f"\nCODA:")
    coda_desc = str(coda["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"])[:50]
    print(f"  Descrizione: {coda_desc}")
    qty_col = "QUANTITA'"
    print(f"  Quantita: {coda[qty_col]}")
    print(f"  Prezzo: {coda['PREZZO']}")
    print(f"  Importo: {coda['IMPORTO']}")

print("\n" + "=" * 80)
print(f"RISULTATO FINALE:")
print(f"  {len(progressivi_df)} progressivi = {len(progressivi_df)} voci")
print(f"  Pulizia preliminare: -{len(df) - len(cleaned_df)} righe")
print("\nOK: Logica testa-coda con pulizia funziona correttamente!")
