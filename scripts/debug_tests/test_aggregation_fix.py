"""Test per verificare la correzione dell'aggregazione voci."""
import sys
from pathlib import Path

# Setup path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Importa solo ciò che serve evitando circular imports
import sqlite3

# Connessione diretta al database
db_path = backend_path / "storage" / "database.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Conta le voci nella tabella vocecomputo per commessa 8
cursor.execute("""
    SELECT COUNT(*)
    FROM vocecomputo
    WHERE computo_id IN (SELECT id FROM computo WHERE commessa_id = 8)
""")
vocecomputo_count = cursor.fetchone()[0]

# Conta le voci uniche per progressivo
cursor.execute("""
    SELECT COUNT(DISTINCT progressivo)
    FROM vocecomputo
    WHERE computo_id IN (SELECT id FROM computo WHERE commessa_id = 8)
    AND progressivo IS NOT NULL
""")
unique_progressivi = cursor.fetchone()[0]

# Conta voci con stesso codice ma progressivi diversi
cursor.execute("""
    SELECT codice, COUNT(DISTINCT progressivo) as prog_count
    FROM vocecomputo
    WHERE computo_id IN (SELECT id FROM computo WHERE commessa_id = 8)
    AND progressivo IS NOT NULL
    AND codice IS NOT NULL
    GROUP BY codice
    HAVING prog_count > 1
    ORDER BY prog_count DESC
    LIMIT 10
""")
duplicates = cursor.fetchall()

print("=" * 80)
print("ANALISI DATABASE - Commessa 8")
print("=" * 80)
print(f"Totale voci in vocecomputo: {vocecomputo_count}")
print(f"Progressivi unici: {unique_progressivi}")
print(f"\nVoci con stesso codice ma progressivi diversi:")
print("-" * 80)
for codice, count in duplicates:
    print(f"  Codice: {codice:30s} | Progressivi diversi: {count}")

# Test con l'API endpoint
print("\n" + "=" * 80)
print("Test dell'endpoint API /computi/{id}/wbs")
print("=" * 80)

# Importa il servizio direttamente
try:
    from app.db.models import Computo
    from sqlmodel import Session, create_engine, select
    from app.services.analysis.wbs_analysis import WbsAnalysisService

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        # Trova il computo per commessa 8
        computo = session.exec(select(Computo).where(Computo.commessa_id == 8)).first()

        if computo:
            print(f"Computo ID: {computo.id}")
            result = WbsAnalysisService.get_wbs_summary(session, computo.id)
            print(f"Voci aggregate restituite dall'API: {len(result.voci)}")
            print(f"Importo totale: €{result.importo_totale:,.2f}")

            # Mostra alcune voci aggregate per debug
            print("\nPrime 10 voci aggregate:")
            print("-" * 80)
            for i, voce in enumerate(result.voci[:10], 1):
                prog = voce.progressivo if voce.progressivo else "N/A"
                print(f"{i:2d}. Prog: {prog:4s} | Codice: {voce.codice or 'N/A':30s}")
        else:
            print("Computo non trovato per commessa 8")

except Exception as e:
    print(f"Errore durante test API: {e}")
    import traceback
    traceback.print_exc()

conn.close()
print("\n" + "=" * 80)
print("Test completato!")
print("=" * 80)
