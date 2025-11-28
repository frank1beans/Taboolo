"""Test per verificare i metadata product_id nelle voci del computo."""
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
print("ANALISI METADATA PRODUCT_ID - Commessa 8")
print("=" * 80)

# Trova il computo di progetto (tipo='progetto')
cursor.execute("""
    SELECT id, nome
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'progetto'
    ORDER BY created_at DESC
    LIMIT 1
""")
computo_progetto = cursor.fetchone()

if not computo_progetto:
    print("Computo di progetto non trovato!")
    sys.exit(1)

computo_id, computo_nome = computo_progetto
print(f"Computo di progetto: {computo_nome} (ID: {computo_id})")
print("=" * 80)

# Analizza i metadata di tutte le voci del computo progetto
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

total_voci = 0
voci_con_product_id = 0
voci_senza_product_id = []
problematic_progressivi = []

for row in cursor.fetchall():
    total_voci += 1
    progressivo, codice, descrizione, metadata_json = row

    # Parse metadata JSON
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
            product_id = metadata.get("product_id")

            if product_id:
                voci_con_product_id += 1
            else:
                voci_senza_product_id.append({
                    "progressivo": progressivo,
                    "codice": codice,
                    "descrizione": descrizione[:50] if descrizione else None
                })
                if progressivo:
                    problematic_progressivi.append(progressivo)
        except json.JSONDecodeError:
            voci_senza_product_id.append({
                "progressivo": progressivo,
                "codice": codice,
                "descrizione": descrizione[:50] if descrizione else None,
                "error": "Invalid JSON"
            })
            if progressivo:
                problematic_progressivi.append(progressivo)
    else:
        voci_senza_product_id.append({
            "progressivo": progressivo,
            "codice": codice,
            "descrizione": descrizione[:50] if descrizione else None,
            "error": "No metadata"
        })
        if progressivo:
            problematic_progressivi.append(progressivo)

print(f"\nTotale voci nel computo progetto: {total_voci}")
print(f"Voci CON product_id nei metadata: {voci_con_product_id}")
print(f"Voci SENZA product_id nei metadata: {len(voci_senza_product_id)}")

if voci_senza_product_id:
    print(f"\nProgressivi problematici (senza product_id): {len(problematic_progressivi)}")
    print("-" * 80)
    print("Prime 20 voci senza product_id:")
    print("-" * 80)
    for i, voce in enumerate(voci_senza_product_id[:20], 1):
        prog = voce.get("progressivo") or "N/A"
        codice = voce.get("codice") or "N/A"
        desc = voce.get("descrizione") or "N/A"
        error = voce.get("error", "")
        error_msg = f" [{error}]" if error else ""
        print(f"{i:2d}. Prog: {prog:4} | Codice: {codice:20s} | Desc: {desc}{error_msg}")

# Verifica se questi progressivi mancanti corrispondono a quelli che poi hanno prezzo 0
print("\n" + "=" * 80)
print("CONFRONTO CON OFFERTE PREZZATE")
print("=" * 80)

# Trova un computo di ritorno per verificare
cursor.execute("""
    SELECT id, nome, impresa, round_number
    FROM computo
    WHERE commessa_id = 8 AND tipo = 'ritorno'
    ORDER BY created_at DESC
    LIMIT 1
""")
computo_ritorno = cursor.fetchone()

if computo_ritorno:
    ritorno_id, ritorno_nome, imputo_impresa, round_num = computo_ritorno
    print(f"\nComputo ritorno: {ritorno_nome} (Impresa: {imputo_impresa}, Round: {round_num})")

    # Conta quante voci nel ritorno hanno prezzo = 0
    cursor.execute("""
        SELECT COUNT(*)
        FROM vocecomputo
        WHERE computo_id = ? AND (prezzo_unitario IS NULL OR prezzo_unitario = 0)
    """, (ritorno_id,))
    voci_prezzo_zero = cursor.fetchone()[0]

    print(f"Voci con prezzo = 0 nel ritorno: {voci_prezzo_zero}")

    # Mostra alcuni esempi di voci con prezzo 0
    cursor.execute("""
        SELECT progressivo, codice, descrizione, prezzo_unitario
        FROM vocecomputo
        WHERE computo_id = ? AND (prezzo_unitario IS NULL OR prezzo_unitario = 0)
        ORDER BY ordine
        LIMIT 10
    """, (ritorno_id,))

    print("\nPrime 10 voci con prezzo = 0 nel ritorno:")
    print("-" * 80)
    for i, row in enumerate(cursor.fetchall(), 1):
        prog, cod, desc, prezzo = row
        prog_str = str(prog) if prog else "N/A"
        cod_str = cod if cod else "N/A"
        desc_str = (desc[:40] if desc else "N/A")
        print(f"{i:2d}. Prog: {prog_str:4} | Codice: {cod_str:20s} | Prezzo: {prezzo}")
else:
    print("\nNessun computo di ritorno trovato.")

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
