"""Test per verificare i prezzi nelle offerte vs prezzi nelle voci ritorno."""
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
print("ANALISI PREZZI: price_list_offer vs vocecomputo ritorno")
print("=" * 80)

# Trova computo di ritorno
cursor.execute("""
    SELECT id, nome, impresa
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'ritorno'
    ORDER BY created_at DESC
    LIMIT 1
""")
ritorno_id, ritorno_nome, impresa = cursor.fetchone()

print(f"\nComputo ritorno: {ritorno_nome} (ID: {ritorno_id})")
print(f"Impresa: {impresa}")
print("=" * 80)

# Statistiche offerte
cursor.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN prezzo_unitario IS NULL OR prezzo_unitario = 0 THEN 1 ELSE 0 END) as zero_prices,
        SUM(CASE WHEN prezzo_unitario IS NOT NULL AND prezzo_unitario > 0 THEN 1 ELSE 0 END) as valid_prices
    FROM price_list_offer
    WHERE computo_id = ?
""", (ritorno_id,))
total_offers, zero_offers, valid_offers = cursor.fetchone()

print(f"\nStatistiche price_list_offer:")
print(f"  Totale offerte: {total_offers}")
print(f"  Offerte con prezzo > 0: {valid_offers}")
print(f"  Offerte con prezzo = 0 o NULL: {zero_offers}")
print(f"  Coverage prezzi validi: {(valid_offers / total_offers * 100):.1f}%")

# Mostra alcune offerte con prezzo 0
if zero_offers > 0:
    print(f"\n  Prime 20 offerte con prezzo = 0:")
    print("  " + "-" * 76)
    cursor.execute("""
        SELECT plo.id, plo.price_list_item_id, plo.prezzo_unitario, pli.product_id, pli.item_code
        FROM price_list_offer plo
        JOIN price_list_item pli ON plo.price_list_item_id = pli.id
        WHERE plo.computo_id = ?
        AND (plo.prezzo_unitario IS NULL OR plo.prezzo_unitario = 0)
        LIMIT 20
    """, (ritorno_id,))

    for i, row in enumerate(cursor.fetchall(), 1):
        offer_id, item_id, prezzo, product_id, item_code = row
        print(f"  {i:2d}. OfferID: {offer_id:4d} | ItemID: {item_id:4d} | PID: {product_id:20s} | Code: {item_code or 'N/A':15s} | Prezzo: {prezzo}")

# Trova computo progetto
cursor.execute("""
    SELECT id
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'progetto'
    ORDER BY created_at DESC
    LIMIT 1
""")
progetto_id = cursor.fetchone()[0]

# Analizza un progressivo specifico che ha prezzo 0
cursor.execute("""
    SELECT progressivo, codice, prezzo_unitario, extra_metadata
    FROM vocecomputo
    WHERE computo_id = ? AND (prezzo_unitario IS NULL OR prezzo_unitario = 0)
    ORDER BY ordine
    LIMIT 1
""", (ritorno_id,))

sample_zero_voce = cursor.fetchone()
if sample_zero_voce:
    prog, codice, prezzo, metadata_json = sample_zero_voce

    print("\n" + "=" * 80)
    print(f"ANALISI DETTAGLIATA: Progressivo {prog} (esempio di voce con prezzo 0)")
    print("=" * 80)

    # Trova la stessa voce nel computo progetto
    cursor.execute("""
        SELECT extra_metadata, prezzo_unitario
        FROM vocecomputo
        WHERE computo_id = ? AND progressivo = ?
    """, (progetto_id, prog))

    progetto_voce = cursor.fetchone()
    if progetto_voce:
        progetto_metadata_json, progetto_prezzo = progetto_voce
        progetto_metadata = json.loads(progetto_metadata_json) if progetto_metadata_json else {}
        product_id = progetto_metadata.get("product_id")

        print(f"\nProgressivo {prog} nel computo PROGETTO:")
        print(f"  Product ID: {product_id}")
        print(f"  Codice: {codice}")
        print(f"  Prezzo progetto: {progetto_prezzo}")

        # Trova il price_list_item corrispondente
        if product_id:
            cursor.execute("""
                SELECT id, item_code, item_description
                FROM price_list_item
                WHERE product_id = ? AND commessa_id = 8
            """, (product_id,))

            price_item = cursor.fetchone()
            if price_item:
                item_id, item_code, item_desc = price_item
                print(f"\nPrice_list_item trovato:")
                print(f"  Item ID: {item_id}")
                print(f"  Item Code: {item_code}")
                print(f"  Item Desc: {(item_desc[:50] if item_desc else 'N/A')}")

                # Trova l'offerta corrispondente
                cursor.execute("""
                    SELECT prezzo_unitario, quantita
                    FROM price_list_offer
                    WHERE price_list_item_id = ? AND computo_id = ?
                """, (item_id, ritorno_id))

                offer = cursor.fetchone()
                if offer:
                    offer_prezzo, offer_quantita = offer
                    print(f"\nPrice_list_offer trovata:")
                    print(f"  Prezzo offerta: {offer_prezzo}")
                    print(f"  Quantita offerta: {offer_quantita}")
                else:
                    print(f"\n❌ PROBLEMA: Nessuna offerta trovata per price_list_item_id {item_id}!")
            else:
                print(f"\n❌ PROBLEMA: Nessun price_list_item trovato per product_id {product_id}!")
        else:
            print(f"\n❌ PROBLEMA: Nessun product_id nei metadata!")

        print(f"\nProgressivo {prog} nel computo RITORNO:")
        print(f"  Prezzo ritorno: {prezzo}")

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
