"""Test per il nuovo LcImportService sulla commessa 001."""
import sys
from pathlib import Path

# Setup path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import Session, create_engine, select
from app.db.models import Computo, VoceComputo
from app.services.importers.lc_import_service import LcImportService

# Connessione database
db_path = backend_path / "storage" / "database.sqlite"
engine = create_engine(f"sqlite:///{db_path}")

print("=" * 80)
print("TEST NUOVO LcImportService - Commessa 001")
print("=" * 80)

with Session(engine) as session:
    # 1. Verifica computo progetto
    computo_progetto = session.exec(
        select(Computo)
        .where(Computo.commessa_id == 1, Computo.tipo == "progetto")
        .order_by(Computo.created_at.desc())
    ).first()

    if not computo_progetto:
        print("❌ Computo progetto non trovato!")
        sys.exit(1)

    print(f"\n1. COMPUTO PROGETTO")
    print(f"   ID: {computo_progetto.id}")
    print(f"   Nome: {computo_progetto.nome}")

    # Conta voci progetto
    voci_progetto = session.exec(
        select(VoceComputo).where(VoceComputo.computo_id == computo_progetto.id)
    ).all()
    print(f"   Voci: {len(voci_progetto)}")

    # Conta voci con product_id
    voci_con_product_id = sum(
        1 for v in voci_progetto
        if isinstance(v.extra_metadata, dict) and v.extra_metadata.get("product_id")
    )
    print(f"   Voci con product_id: {voci_con_product_id}/{len(voci_progetto)}")

    # 2. Verifica computo ritorno esistente
    computo_ritorno = session.exec(
        select(Computo)
        .where(Computo.commessa_id == 1, Computo.tipo == "ritorno")
        .order_by(Computo.created_at.desc())
    ).first()

    if not computo_ritorno:
        print("\n❌ Nessun computo ritorno trovato!")
        sys.exit(1)

    print(f"\n2. COMPUTO RITORNO ESISTENTE (per confronto)")
    print(f"   ID: {computo_ritorno.id}")
    print(f"   Nome: {computo_ritorno.nome}")
    print(f"   Impresa: {computo_ritorno.impresa}")
    print(f"   Round: {computo_ritorno.round_number}")

    # Conta voci con prezzo zero
    voci_ritorno = session.exec(
        select(VoceComputo).where(VoceComputo.computo_id == computo_ritorno.id)
    ).all()
    voci_prezzo_zero = sum(
        1 for v in voci_ritorno
        if v.prezzo_unitario is None or v.prezzo_unitario == 0
    )
    voci_prezzo_valido = len(voci_ritorno) - voci_prezzo_zero

    print(f"   Voci totali: {len(voci_ritorno)}")
    print(f"   Voci con prezzo > 0: {voci_prezzo_valido}")
    print(f"   Voci con prezzo = 0: {voci_prezzo_zero}")
    print(f"   Coverage: {voci_prezzo_valido/len(voci_ritorno)*100:.1f}%")
    print(f"   Importo totale: €{computo_ritorno.importo_totale:,.2f}")

    # 3. Analizza product_id duplicati nel progetto
    from collections import defaultdict
    import json

    product_id_counts = defaultdict(list)
    for voce in voci_progetto:
        if isinstance(voce.extra_metadata, dict):
            product_id = voce.extra_metadata.get("product_id")
            if product_id:
                product_id_counts[product_id].append(voce.progressivo)

    # Trova product_id con multipli progressivi
    duplicati = {
        pid: progs for pid, progs in product_id_counts.items() if len(progs) > 1
    }

    print(f"\n3. ANALISI PRODUCT_ID DUPLICATI")
    print(f"   Product_id unici: {len(product_id_counts)}")
    print(f"   Product_id con multipli progressivi: {len(duplicati)}")

    if duplicati:
        print(f"\n   Top 10 product_id con più progressivi:")
        sorted_dups = sorted(duplicati.items(), key=lambda x: len(x[1]), reverse=True)
        for i, (pid, progs) in enumerate(sorted_dups[:10], 1):
            print(f"   {i:2d}. Product_id {pid}: {len(progs)} progressivi")

    # 4. Verifica price_list_items
    from app.db.models import PriceListItem

    price_items = session.exec(
        select(PriceListItem).where(PriceListItem.commessa_id == 1)
    ).all()

    print(f"\n4. PRICE_LIST_ITEMS")
    print(f"   Totale items: {len(price_items)}")

    # 5. Verifica offerte
    from app.db.models import PriceListOffer

    offerte = session.exec(
        select(PriceListOffer).where(PriceListOffer.computo_id == computo_ritorno.id)
    ).all()

    offerte_con_prezzo = sum(1 for o in offerte if o.prezzo_unitario and o.prezzo_unitario > 0)
    offerte_zero = len(offerte) - offerte_con_prezzo

    print(f"\n5. PRICE_LIST_OFFERS (computo {computo_ritorno.id})")
    print(f"   Totale offerte: {len(offerte)}")
    print(f"   Offerte con prezzo > 0: {offerte_con_prezzo}")
    print(f"   Offerte con prezzo = 0: {offerte_zero}")

print("\n" + "=" * 80)
print("CONCLUSIONE")
print("=" * 80)

print(f"""
Il problema evidenziato:
- {len(duplicati)} product_id sono usati da multipli progressivi
- {voci_prezzo_zero} voci hanno prezzo = 0 nel ritorno
- {offerte_zero} offerte hanno prezzo = 0

Il nuovo LcImportService dovrebbe:
1. Applicare lo stesso prezzo a TUTTI i progressivi con stesso product_id
2. Ridurre drasticamente il numero di voci con prezzo = 0
3. Coverage atteso: ~100% (vs {voci_prezzo_valido/len(voci_ritorno)*100:.1f}% attuale)

Per testare il nuovo servizio, bisognerebbe re-importare il file LC originale.
""")

print("=" * 80)
print("Test completato!")
print("=" * 80)
