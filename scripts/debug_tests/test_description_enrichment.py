"""Test per verificare l'arricchimento delle descrizioni parent-child."""
import sys
from pathlib import Path

# Aggiungi backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import diretto per evitare circular import
import importlib.util
spec = importlib.util.spec_from_file_location(
    "six_import_service",
    backend_path / "app" / "services" / "six_import_service.py"
)
six_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(six_module)
SixImportService = six_module.SixImportService

# Percorso al file SIX reale
six_file = Path(r"C:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251127T184957_3600_20-11-2025.xml")

if not six_file.exists():
    print(f"File non trovato: {six_file}")
    sys.exit(1)

print(f"Caricamento file: {six_file}")
print("=" * 80)

# Crea il servizio e carica il file
service = SixImportService()
with open(six_file, "r", encoding="utf-8") as f:
    xml_content = f.read()

service.load_xml(xml_content)

# Verifica l'arricchimento delle descrizioni
test_codes = [
    "1C.00.700.0010",      # Parent
    "1C.00.700.0010.b",    # Child
    "1C.00.700.0020",      # Parent
    "1C.00.700.0020.b",    # Child
    "1C.01.070.0010",      # Parent
    "1C.01.070.0010.b",    # Child
]

print("\nTest arricchimento descrizioni:")
print("=" * 80)

for code in test_codes:
    # Cerca il prodotto per codice
    product = None
    for p in service.products.values():
        if p.code == code:
            product = p
            break

    if product:
        is_parent = "✓ PARENT" if product.is_parent_voice else "  child"
        print(f"\n{is_parent} | Codice: {code}")
        print(f"Descrizione originale:")
        print(f"  {product.description[:100]}..." if len(product.description) > 100 else f"  {product.description}")
        if product.enriched_description and product.enriched_description != product.description:
            print(f"Descrizione arricchita:")
            print(f"  {product.enriched_description[:150]}..." if len(product.enriched_description) > 150 else f"  {product.enriched_description}")
        else:
            print(f"Descrizione arricchita: (identica)")
    else:
        print(f"\n  child | Codice: {code} - NON TROVATO")

print("\n" + "=" * 80)
print("Test completato!")
