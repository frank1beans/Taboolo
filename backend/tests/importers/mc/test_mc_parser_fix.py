"""Test per verificare che il parser MC con head-tail funzioni"""
import sys
sys.path.insert(0, 'c:/Users/f.biggi/Taboolo/backend')

from pathlib import Path
from app.services.importers import parse_mc_return_excel

file_path = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251129T110901_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")

print("TEST PARSER MC CON HEAD-TAIL LOGIC")
print("=" * 80)

# Parse usando il nuovo parser
parsed = parse_mc_return_excel(
    file_path=file_path,
    sheet_name="3600 ES E EC 02b",
    code_columns=["CODICE"],
    description_columns=["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"],
    price_column="PREZZO",
    quantity_column="QUANTITA'",
    progressive_column="N.",
)

voci = parsed.computo.voci
print(f"\nTotale voci parsed: {len(voci)}")

# Conta voci senza prezzo
no_price = [v for v in voci if v.prezzo_unitario is None]
print(f"Voci senza prezzo: {len(no_price)} ({len(no_price)/len(voci)*100:.1f}%)")

# Verifica progressivo 2170
prog_2170 = next((v for v in voci if v.progressivo == 2170), None)
if prog_2170:
    print(f"\nProgressivo 2170:")
    print(f"  Codice: {prog_2170.codice}")
    print(f"  Descrizione: {prog_2170.descrizione[:60]}")
    print(f"  Quantità: {prog_2170.quantita}")
    print(f"  Prezzo: {prog_2170.prezzo_unitario}")
    print(f"  Importo: {prog_2170.importo}")

    if prog_2170.prezzo_unitario is not None:
        print("  [OK] Prezzo estratto correttamente!")
    else:
        print("  [ERRORE] Prezzo mancante!")
else:
    print("\n[ERRORE] Progressivo 2170 non trovato!")

# Verifica altri progressivi con stesso codice
print(f"\n{'=' * 80}")
print("CODICE 1C.01.800.0130 (dovrebbe avere 12 progressivi):")
print("-" * 80)

voci_1c = [v for v in voci if v.codice and "1C.01.800.0130" in v.codice]
print(f"Trovati {len(voci_1c)} progressivi con questo codice")

for voce in voci_1c[:5]:  # Primi 5
    status = "[OK]" if voce.prezzo_unitario is not None else "[MISSING]"
    print(f"  Prog {voce.progressivo}: prezzo={voce.prezzo_unitario} {status}")

# Statistica finale
with_price = [v for v in voci if v.prezzo_unitario is not None]
print(f"\n{'=' * 80}")
print(f"RISULTATO FINALE:")
print(f"  Voci con prezzo: {len(with_price)}/{len(voci)} ({len(with_price)/len(voci)*100:.1f}%)")
print(f"  Voci senza prezzo: {len(no_price)}/{len(voci)} ({len(no_price)/len(voci)*100:.1f}%)")

if len(no_price) == 0:
    print("\n[PERFETTO] Tutte le voci hanno un prezzo!")
elif len(no_price) < 50:
    print(f"\n[BUONO] Solo {len(no_price)} voci senza prezzo (probabilmente legittime)")
else:
    print(f"\n[PROBLEMA] Troppe voci senza prezzo ({len(no_price)})")
