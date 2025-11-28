"""Analisi della commessa 001 per capire l'impatto del nuovo LcImportService."""
import sys
from pathlib import Path
import sqlite3
import json
from collections import defaultdict

# Setup path
backend_path = Path(__file__).parent / "backend"
db_path = backend_path / "storage" / "database.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("ANALISI COMMESSA 001 - Impact Analysis Nuovo LcImportService")
print("=" * 80)

# 1. Info computo progetto
cursor.execute("""
    SELECT id, nome
    FROM computo
    WHERE commessa_id = 1 AND tipo = 'progetto'
    ORDER BY created_at DESC
    LIMIT 1
""")
progetto_id, progetto_nome = cursor.fetchone()

print(f"\n1. COMPUTO PROGETTO")
print(f"   ID: {progetto_id}")
print(f"   Nome: {progetto_nome}")

# Conta voci progetto
cursor.execute("SELECT COUNT(*) FROM vocecomputo WHERE computo_id = ?", (progetto_id,))
num_voci_progetto = cursor.fetchone()[0]
print(f"   Voci totali: {num_voci_progetto}")

# 2. Analizza product_id nel progetto
cursor.execute("""
    SELECT progressivo, codice, extra_metadata
    FROM vocecomputo
    WHERE computo_id = ?
    ORDER BY ordine
""", (progetto_id,))

product_id_to_progressivi = defaultdict(list)
progressivi_con_product_id = 0

for row in cursor.fetchall():
    progressivo, codice, metadata_json = row
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
            product_id = metadata.get("product_id")
            if product_id:
                product_id_to_progressivi[product_id].append({
                    "progressivo": progressivo,
                    "codice": codice
                })
                progressivi_con_product_id += 1
        except json.JSONDecodeError:
            pass

print(f"   Progressivi con product_id: {progressivi_con_product_id}")
print(f"   Product_id unici: {len(product_id_to_progressivi)}")

# Trova product_id con multipli progressivi
duplicati = {
    pid: progs
    for pid, progs in product_id_to_progressivi.items()
    if len(progs) > 1
}

print(f"\n2. PRODUCT_ID CON MULTIPLI PROGRESSIVI")
print(f"   Product_id con multipli progressivi: {len(duplicati)}")
print(f"   Percentuale: {len(duplicati)/len(product_id_to_progressivi)*100:.1f}%")

# Top 10
sorted_dups = sorted(duplicati.items(), key=lambda x: len(x[1]), reverse=True)
print(f"\n   Top 10 product_id con più progressivi:")
for i, (pid, progs) in enumerate(sorted_dups[:10], 1):
    codici = list(set(p["codice"] for p in progs if p["codice"]))
    codice_str = codici[0] if len(codici) == 1 else f"{len(codici)} codici diversi"
    print(f"   {i:2d}. PID {pid[:15]:15s} -> {len(progs):3d} progressivi ({codice_str})")

# 3. Analizza computi ritorno esistenti
cursor.execute("""
    SELECT id, impresa, round_number
    FROM computo
    WHERE commessa_id = 1 AND tipo = 'ritorno'
    ORDER BY created_at
""")
ritorni = cursor.fetchall()

print(f"\n3. COMPUTI RITORNO ESISTENTI")
print(f"   Totale ritorni: {len(ritorni)}")

for ritorno_id, impresa, round_num in ritorni:
    # Conta voci con prezzo zero
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN prezzo_unitario IS NULL OR prezzo_unitario = 0 THEN 1 ELSE 0 END) as zero_prices
        FROM vocecomputo
        WHERE computo_id = ?
    """, (ritorno_id,))
    total, zero_prices = cursor.fetchone()
    valid_prices = total - zero_prices if zero_prices else total
    coverage = (valid_prices / total * 100) if total > 0 else 0

    print(f"\n   Ritorno ID {ritorno_id} - {impresa} (Round {round_num}):")
    print(f"     Voci totali: {total}")
    print(f"     Voci con prezzo > 0: {valid_prices} ({coverage:.1f}%)")
    print(f"     Voci con prezzo = 0: {zero_prices}")

# 4. Analizza price_list_items
cursor.execute("SELECT COUNT(*) FROM price_list_item WHERE commessa_id = 1")
num_price_items = cursor.fetchone()[0]
print(f"\n4. PRICE_LIST_ITEMS")
print(f"   Totale items: {num_price_items}")

# 5. Per un ritorno, analizza le offerte
cursor.execute("""
    SELECT id, impresa
    FROM computo
    WHERE commessa_id = 1 AND tipo = 'ritorno'
    ORDER BY created_at DESC
    LIMIT 1
""")
sample_ritorno_id, sample_impresa = cursor.fetchone()

cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN prezzo_unitario IS NULL OR prezzo_unitario = 0 THEN 1 ELSE 0 END) as zero_offers
    FROM price_list_offer
    WHERE computo_id = ?
""", (sample_ritorno_id,))
total_offers, zero_offers = cursor.fetchone()
valid_offers = total_offers - zero_offers if zero_offers else total_offers

print(f"\n5. PRICE_LIST_OFFERS (Ritorno {sample_ritorno_id} - {sample_impresa})")
print(f"   Totale offerte: {total_offers}")
print(f"   Offerte con prezzo > 0: {valid_offers} ({valid_offers/total_offers*100:.1f}%)")
print(f"   Offerte con prezzo = 0: {zero_offers}")

# 6. Stima impatto del nuovo servizio
print("\n" + "=" * 80)
print("IMPATTO ATTESO DEL NUOVO LcImportService")
print("=" * 80)

# Calcola quanti progressivi potrebbero beneficiare
total_progressivi_affected = sum(len(progs) for progs in duplicati.values())

print(f"""
PROBLEMA ATTUALE:
- {len(duplicati)} product_id hanno multipli progressivi
- Totale progressivi coinvolti: {total_progressivi_affected}
- Alcuni di questi progressivi ricevono prezzo 0 per errore

SOLUZIONE NUOVO SERVIZIO:
- TUTTI i progressivi con stesso product_id riceveranno lo stesso prezzo
- Se l'offerta ha prezzo X per product_id Y, TUTTI i progressivi con Y prendono X
- Coverage atteso: ~100% (vs ~99% attuale per commessa 001)

NOTA: Commessa 001 ha già ottima coverage ({coverage:.1f}%), quindi l'impatto
sarà minimo. Il vero beneficio si vedrà sulla commessa 008 che ha 574 voci
con prezzo zero su 1239 (46% di fallimento).
""")

conn.close()
print("=" * 80)
print("Analisi completata!")
print("=" * 80)
