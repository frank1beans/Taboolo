"""Test dettagliato per il progressivo 10."""
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
print("ANALISI DETTAGLIATA: Progressivo 10")
print("=" * 80)

# Trova computi
cursor.execute("""
    SELECT id, tipo
    FROM computo
    WHERE commessa_id = 8 AND tipo IN ('progetto', 'ritorno')
    ORDER BY tipo, created_at DESC
""")
computi = {row[1]: row[0] for row in cursor.fetchall()}
progetto_id = computi.get('progetto')
ritorno_id = list(cursor.execute("SELECT id FROM computo WHERE commessa_id = 8 AND tipo = 'ritorno' ORDER BY created_at DESC LIMIT 1"))[0][0]

print(f"Computo progetto ID: {progetto_id}")
print(f"Computo ritorno ID: {ritorno_id}")
print("=" * 80)

# Voce nel progetto
cursor.execute("""
    SELECT progressivo, codice, descrizione, prezzo_unitario, quantita, importo, extra_metadata
    FROM vocecomputo
    WHERE computo_id = ? AND progressivo = 10
""", (progetto_id,))

prog_voce = cursor.fetchone()
if prog_voce:
    prog, cod, desc, prezzo, quantita, importo, metadata_json = prog_voce
    metadata = json.loads(metadata_json) if metadata_json else {}
    product_id = metadata.get("product_id")

    print("\n1. VOCE NEL PROGETTO (progressivo 10):")
    print(f"   Codice: {cod}")
    print(f"   Descrizione: {desc[:60] if desc else 'N/A'}")
    print(f"   Product ID: {product_id}")
    print(f"   Prezzo: {prezzo}")
    print(f"   Quantita: {quantita}")
    print(f"   Importo: {importo}")

    # Price list item
    if product_id:
        cursor.execute("""
            SELECT id, item_code, item_description
            FROM price_list_item
            WHERE product_id = ? AND commessa_id = 8
        """, (product_id,))

        price_item = cursor.fetchone()
        if price_item:
            item_id, item_code, item_desc = price_item
            print(f"\n2. PRICE_LIST_ITEM (product_id {product_id}):")
            print(f"   Item ID: {item_id}")
            print(f"   Item Code: {item_code}")
            print(f"   Item Desc: {item_desc[:60] if item_desc else 'N/A'}")

            # Offerta
            cursor.execute("""
                SELECT prezzo_unitario, quantita
                FROM price_list_offer
                WHERE price_list_item_id = ? AND computo_id = ?
            """, (item_id, ritorno_id))

            offer = cursor.fetchone()
            if offer:
                offer_prezzo, offer_quantita = offer
                print(f"\n3. PRICE_LIST_OFFER (item_id {item_id}, computo {ritorno_id}):")
                print(f"   Prezzo offerta: {offer_prezzo}")
                print(f"   Quantita offerta: {offer_quantita}")
            else:
                print(f"\n3. ❌ Nessuna offerta trovata!")

# Voce nel ritorno
cursor.execute("""
    SELECT progressivo, codice, descrizione, prezzo_unitario, quantita, importo, extra_metadata
    FROM vocecomputo
    WHERE computo_id = ? AND progressivo = 10
""", (ritorno_id,))

rit_voce = cursor.fetchone()
if rit_voce:
    prog, cod, desc, prezzo, quantita, importo, metadata_json = rit_voce
    metadata = json.loads(metadata_json) if metadata_json else {}
    product_id_rit = metadata.get("product_id")

    print(f"\n4. VOCE NEL RITORNO (progressivo 10):")
    print(f"   Codice: {cod}")
    print(f"   Descrizione: {desc[:60] if desc else 'N/A'}")
    print(f"   Product ID: {product_id_rit}")
    print(f"   Prezzo: {prezzo} [ZERO!]")
    print(f"   Quantita: {quantita}")
    print(f"   Importo: {importo}")

# Verifica se ci sono ALTRE voci nel progetto con lo stesso product_id
print(f"\n5. ALTRE VOCI NEL PROGETTO con product_id {product_id}:")
print("   " + "-" * 76)
cursor.execute("""
    SELECT progressivo, codice, descrizione, prezzo_unitario, quantita
    FROM vocecomputo
    WHERE computo_id = ? AND extra_metadata LIKE ?
    ORDER BY progressivo
    LIMIT 10
""", (progetto_id, f'%"product_id": "{product_id}"%'))

for i, row in enumerate(cursor.fetchall(), 1):
    p, c, d, pr, q = row
    print(f"   {i}. Prog: {p:4d} | Code: {c:20s} | Prezzo: {pr:8.2f} | Quant: {q}")

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
