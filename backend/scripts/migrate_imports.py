#!/usr/bin/env python3
"""
Script to automatically migrate imports from old structure to new structure.
"""
import re
import sys
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Models
    r'from app\.db\.models import (.+)Settings': r'from app.domain.settings.models import Settings',
    r'from app\.db\.models import (.+)User(.+)': r'from app.domain.users.models import \1User\2',
    r'from app\.db\.models import (.+)Commessa(.+)': r'from app.domain.commesse.models import \1Commessa\2',
    r'from app\.db\.models import (.+)Computo(.+)': r'from app.domain.computi.models import \1Computo\2',
    r'from app\.db\.models import (.+)Voce(.+)': r'from app.domain.computi.models import \1Voce\2',
    r'from app\.db\.models import (.+)PriceList(.+)': r'from app.domain.catalog.models import \1PriceList\2',
    r'from app\.db\.models import (.+)Property(.+)': r'from app.domain.catalog.models import \1Property\2',

    # Services - NLP
    r'from app\.services\.nlp import': r'from app.services.nlp.embedding_service import',
    r'from app\.services\.property_extraction import': r'from app.services.nlp.property_extraction import',
    r'from app\.services\.property_extractor import': r'from app.services.nlp.property_extractor import',

    # Services - Others
    r'from app\.services\.storage import': r'from app.services.storage.storage_service import',
    r'from app\.services\.audit import': r'from app.services.audit.audit_service import',
}

def migrate_file(file_path: Path) -> bool:
    """Migrate imports in a single file."""
    print(f"Processing {file_path}...")

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        modified = False

        for old_pattern, new_import in IMPORT_MAPPINGS.items():
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_import, content)
                modified = True

        if modified:
            file_path.write_text(content, encoding='utf-8')
            print(f"  [OK] Updated {file_path}")
            return True
        else:
            print(f"  [-] No changes needed")
            return False

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return False

def main():
    """Main migration function."""
    backend_dir = Path(__file__).parent.parent
    app_dir = backend_dir / "app"

    # Find all Python files in api/v1/endpoints
    endpoints_dir = app_dir / "api" / "v1" / "endpoints"

    if not endpoints_dir.exists():
        print(f"Error: {endpoints_dir} not found")
        return 1

    files_updated = 0
    files_processed = 0

    print(f"Migrating imports in {endpoints_dir}...\n")

    for py_file in endpoints_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        files_processed += 1
        if migrate_file(py_file):
            files_updated += 1

    print(f"\n[SUCCESS] Migration complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Files updated: {files_updated}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
