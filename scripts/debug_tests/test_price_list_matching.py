"""Test per verificare il matching tra voci progetto e PriceListItem."""
import sys
from pathlib import Path
import sqlite3
import json

# Setup path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Connessione diretta al database
db_path = backend_path / "storage" / "database.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("ANALISI MATCHING PRODUCT_ID: Voci Progetto -> PriceListItem")
print("=" * 80)

# Trova il computo di progetto
cursor.execute("""
    SELECT id, nome
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'progetto'
    ORDER BY created_at DESC
    LIMIT 1
""")
computo_progetto = cursor.fetchone()
computo_id, computo_nome = computo_progetto

# Recupera tutti i product_id dalle voci progetto
cursor.execute("""
    SELECT
        progressivo,
        codice,
        descrizione,
        extra_metadata
    FROM vocecomputo
    WHERE computo_id = ?
    ORDER BY ordine
""", (computo_id,))

progetto_product_ids = {}  # progressivo -> product_id
for row in cursor.fetchall():
    progressivo, codice, descrizione, metadata_json = row
    if metadata_json:
        metadata = json.loads(metadata_json)
        product_id = metadata.get("product_id")
        if product_id and progressivo:
            progetto_product_ids[progressivo] = {
                "product_id": product_id,
                "codice": codice,
                "descrizione": descrizione[:50] if descrizione else None
            }

print(f"Voci progetto con product_id: {len(progetto_product_ids)}")

# Recupera tutti i product_id dalla tabella PriceListItem
cursor.execute("""
    SELECT product_id, item_code, item_description
    FROM price_list_item
    WHERE commessa_id = 8
""")

price_list_product_ids = set()
price_list_index = {}  # product_id -> item info
for row in cursor.fetchall():
    product_id, item_code, item_description = row
    if product_id:
        price_list_product_ids.add(product_id)
        price_list_index[product_id] = {
            "item_code": item_code,
            "item_description": item_description[:50] if item_description else None
        }

print(f"PriceListItem con product_id: {len(price_list_product_ids)}")
print("=" * 80)

# Trova i product_id delle voci progetto che NON sono in PriceListItem
missing_in_price_list = []
for progressivo, voce_info in progetto_product_ids.items():
    product_id = voce_info["product_id"]
    if product_id not in price_list_product_ids:
        missing_in_price_list.append({
            "progressivo": progressivo,
            "product_id": product_id,
            "codice": voce_info["codice"],
            "descrizione": voce_info["descrizione"]
        })

print(f"\nProduct_id presenti nelle voci progetto ma ASSENTI in PriceListItem: {len(missing_in_price_list)}")

if missing_in_price_list:
    print("-" * 80)
    print("Prime 20 voci con product_id mancante in PriceListItem:")
    print("-" * 80)
    for i, voce in enumerate(missing_in_price_list[:20], 1):
        prog = voce["progressivo"]
        pid = voce["product_id"]
        codice = voce["codice"] or "N/A"
        desc = voce["descrizione"] or "N/A"
        print(f"{i:2d}. Prog: {prog:4d} | PID: {pid:20s} | Codice: {codice:20s}")

# Verifica se questi progressivi mancanti corrispondono a quelli con prezzo 0
print("\n" + "=" * 80)
print("CONFRONTO CON VOCI A PREZZO ZERO NEL RITORNO")
print("=" * 80)

cursor.execute("""
    SELECT id FROM computo
    WHERE commessa_id = 8 AND tipo = 'ritorno'
    ORDER BY created_at DESC
    LIMIT 1
""")
ritorno_id = cursor.fetchone()[0]

cursor.execute("""
    SELECT progressivo, codice, prezzo_unitario
    FROM vocecomputo
    WHERE computo_id = ? AND (prezzo_unitario IS NULL OR prezzo_unitario = 0)
    ORDER BY ordine
""", (ritorno_id,))

zero_price_progressivi = set()
for row in cursor.fetchall():
    progressivo, codice, prezzo = row
    if progressivo:
        zero_price_progressivi.add(progressivo)

missing_progressivi = {v["progressivo"] for v in missing_in_price_list}
overlap = zero_price_progressivi & missing_progressivi

print(f"\nProgressivi con prezzo = 0 nel ritorno: {len(zero_price_progressivi)}")
print(f"Progressivi con product_id mancante in PriceListItem: {len(missing_progressivi)}")
print(f"Progressivi in comune (overlap): {len(overlap)}")

if len(overlap) > 0:
    coverage = (len(overlap) / len(zero_price_progressivi)) * 100 if zero_price_progressivi else 0
    print(f"\nCopertura: {coverage:.1f}% dei prezzi a zero sono dovuti a product_id mancanti in PriceListItem")

    # Mostra alcuni esempi di progressivi in overlap
    print("\nPrimi 10 progressivi con entrambi i problemi:")
    print("-" * 80)
    for i, prog in enumerate(sorted(list(overlap))[:10], 1):
        voce = progetto_product_ids.get(prog, {})
        pid = voce.get("product_id", "N/A")
        codice = voce.get("codice", "N/A")
        print(f"{i:2d}. Prog: {prog:4d} | PID: {pid:20s} | Codice: {codice}")

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
