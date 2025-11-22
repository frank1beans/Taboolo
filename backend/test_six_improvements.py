"""
Test script per verificare i miglioramenti all'import STR Vision
"""
import sys
import io
from pathlib import Path
from app.services.six_import_service import SixParser

# Fix encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_six_improvements():
    # Path al file XML di test
    xml_path = Path(r"C:\Users\f.biggi\Taboo\measure-maker-plus\backend\storage\commessa_0001\uploads\20251114T200840_4440_08-11-2025.xml")

    if not xml_path.exists():
        print(f"❌ File non trovato: {xml_path}")
        return

    print("📂 Caricamento file XML...")
    xml_bytes = xml_path.read_bytes()

    print("🔍 Parsing XML con miglioramenti...")
    parser = SixParser(xml_bytes)

    # Test 1: Verifica metadata preventivi
    print("\n" + "="*50)
    print("TEST 1: Metadata Preventivi")
    print("="*50)
    preventivi = parser.list_preventivi()
    print(f"✅ Trovati {len(preventivi)} preventivi")

    for prev in preventivi:
        print(f"\n📋 Preventivo: {prev.label}")
        print(f"   ID Interno: {prev.internal_id}")
        print(f"   Codice: {prev.code}")
        print(f"   Autore: {prev.author or 'N/A'}")
        print(f"   Versione: {prev.version or 'N/A'}")
        print(f"   Data: {prev.date or 'N/A'}")
        print(f"   Lista Prezzi: {prev.price_list_id or 'N/A'}")

    # Test 2: Verifica categorie SOA
    print("\n" + "="*50)
    print("TEST 2: Categorie SOA")
    print("="*50)
    print(f"✅ Trovate {len(parser.soa_categories)} categorie SOA")

    # Mostra le prime 5 categorie
    for i, (soa_id, (code, description)) in enumerate(list(parser.soa_categories.items())[:5]):
        print(f"\n🏗️  SOA ID: {soa_id}")
        print(f"   Codice: {code}")
        print(f"   Descrizione: {description}")

    if len(parser.soa_categories) > 5:
        print(f"\n   ... e altre {len(parser.soa_categories) - 5} categorie")

    # Test 3: Verifica pattern riferimenti migliorato
    print("\n" + "="*50)
    print("TEST 3: Pattern Riferimenti")
    print("="*50)

    test_strings = [
        "voce n. 123",
        "rif. 456",
        "#789",
        "→ 101",
        "[202]",
        "<303>",
        "prog. 404",
        "riferimento nr. 505",
    ]

    import re
    for test in test_strings:
        matches = parser._reference_pattern.findall(test)
        if matches:
            # Extract non-empty group
            if isinstance(matches[0], tuple):
                match_value = next((g for g in matches[0] if g), None)
            else:
                match_value = matches[0]
            print(f"✅ '{test}' → trovato: {match_value}")
        else:
            print(f"❌ '{test}' → non trovato")

    # Test 4: Verifica esportazione catalogo con SOA
    print("\n" + "="*50)
    print("TEST 4: Export Catalogo Prezzi con SOA")
    print("="*50)

    catalog = parser.export_price_catalog()
    print(f"✅ Catalogo contiene {len(catalog)} articoli")

    # Verifica se ci sono campi SOA
    items_with_soa = [item for item in catalog if item.get('soa_category') or item.get('soa_description')]
    print(f"📊 Articoli con info SOA: {len(items_with_soa)}")

    # Mostra un esempio
    if catalog:
        example = catalog[0]
        print(f"\n📦 Esempio articolo:")
        print(f"   Codice: {example.get('code')}")
        print(f"   Descrizione: {example.get('description')[:50]}...")
        print(f"   WBS6: {example.get('wbs6_code')} - {example.get('wbs6_description')}")
        print(f"   WBS7: {example.get('wbs7_code')} - {example.get('wbs7_description')}")
        print(f"   SOA: {example.get('soa_category')} - {example.get('soa_description')}")

    print("\n" + "="*50)
    print("✨ Test completati!")
    print("="*50)

if __name__ == "__main__":
    test_six_improvements()
