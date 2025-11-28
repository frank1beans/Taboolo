"""Test per verificare le offerte create nella tabella price_list_offer."""
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
print("ANALISI PRICE_LIST_OFFER - Commessa 8")
print("=" * 80)

# Trova il computo di ritorno
cursor.execute("""
    SELECT id, nome, impresa, round_number
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'ritorno'
    ORDER BY created_at DESC
    LIMIT 1
""")
computo_ritorno = cursor.fetchone()
ritorno_id, ritorno_nome, impresa, round_num = computo_ritorno

print(f"\nComputo ritorno: {ritorno_nome}")
print(f"Impresa: {impresa}, Round: {round_num}")
print("=" * 80)

# Conta quanti price_list_item ci sono per questa commessa
cursor.execute("""
    SELECT COUNT(*)
    FROM price_list_item
    WHERE commessa_id = 8
""")
total_price_items = cursor.fetchone()[0]

# Conta quante offerte sono state create per questo computo
cursor.execute("""
    SELECT COUNT(*)
    FROM price_list_offer
    WHERE computo_id = ?
""", (ritorno_id,))
total_offers = cursor.fetchone()[0]

print(f"\nTotale price_list_item per commessa 8: {total_price_items}")
print(f"Totale price_list_offer per ritorno {ritorno_id}: {total_offers}")
print(f"Coverage: {(total_offers / total_price_items * 100):.1f}%")

# Trova price_list_item SENZA offerta
cursor.execute("""
    SELECT pli.id, pli.product_id, pli.item_code, pli.item_description
    FROM price_list_item pli
    WHERE pli.commessa_id = 8
    AND pli.id NOT IN (
        SELECT price_list_item_id
        FROM price_list_offer
        WHERE computo_id = ?
    )
    LIMIT 20
""", (ritorno_id,))

items_without_offers = cursor.fetchall()

if items_without_offers:
    print(f"\nPrice_list_item SENZA offerta: {len(items_without_offers)} (mostrando primi 20)")
    print("-" * 80)
    for i, row in enumerate(items_without_offers, 1):
        item_id, product_id, item_code, item_desc = row
        desc = (item_desc[:40] if item_desc else "N/A")
        print(f"{i:2d}. ItemID: {item_id:4d} | PID: {product_id:20s} | Code: {item_code or 'N/A':20s}")

# Verifica quante voci progetto usano questi price_list_item senza offerta
print("\n" + "=" * 80)
print("IMPATTO SUI PROGRESSIVI")
print("=" * 80)

# Trova il computo progetto
cursor.execute("""
    SELECT id
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'progetto'
    ORDER BY created_at DESC
    LIMIT 1
""")
progetto_id = cursor.fetchone()[0]

# Recupera tutti i product_id che non hanno offerta
cursor.execute("""
    SELECT DISTINCT pli.product_id
    FROM price_list_item pli
    WHERE pli.commessa_id = 8
    AND pli.id NOT IN (
        SELECT price_list_item_id
        FROM price_list_offer
        WHERE computo_id = ?
    )
""", (ritorno_id,))

missing_product_ids = set(row[0] for row in cursor.fetchall())
print(f"\nProduct_id SENZA offerta: {len(missing_product_ids)}")

# Conta quante voci progetto usano questi product_id
cursor.execute("""
    SELECT progressivo, codice, descrizione, extra_metadata
    FROM vocecomputo
    WHERE computo_id = ?
""", (progetto_id,))

affected_progressivi = []
for row in cursor.fetchall():
    progressivo, codice, descrizione, metadata_json = row
    if metadata_json:
        metadata = json.loads(metadata_json)
        product_id = metadata.get("product_id")
        if product_id in missing_product_ids:
            affected_progressivi.append({
                "progressivo": progressivo,
                "product_id": product_id,
                "codice": codice,
                "descrizione": descrizione[:40] if descrizione else None
            })

print(f"Progressivi impattati (con product_id senza offerta): {len(affected_progressivi)}")

if affected_progressivi:
    print("\nPrimi 20 progressivi impattati:")
    print("-" * 80)
    for i, voce in enumerate(affected_progressivi[:20], 1):
        prog = voce["progressivo"]
        pid = voce["product_id"]
        cod = voce["codice"] or "N/A"
        print(f"{i:2d}. Prog: {prog:4d} | PID: {pid:20s} | Code: {cod:20s}")

# Verifica se questi progressivi hanno effettivamente prezzo 0 nel ritorno
cursor.execute("""
    SELECT progressivo, prezzo_unitario
    FROM vocecomputo
    WHERE computo_id = ?
    AND (prezzo_unitario IS NULL OR prezzo_unitario = 0)
""", (ritorno_id,))

zero_price_progs = {row[0] for row in cursor.fetchall() if row[0]}
affected_progs = {v["progressivo"] for v in affected_progressivi if v["progressivo"]}
overlap = zero_price_progs & affected_progs

print(f"\nProgressivi con prezzo = 0 nel ritorno: {len(zero_price_progs)}")
print(f"Progressivi con product_id senza offerta: {len(affected_progs)}")
print(f"Overlap (progressivi con entrambi i problemi): {len(overlap)}")

if len(overlap) > 0 and len(zero_price_progs) > 0:
    coverage = (len(overlap) / len(zero_price_progs)) * 100
    print(f"\nCopertura: {coverage:.1f}% dei prezzi a zero sono dovuti a product_id senza offerta")

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
