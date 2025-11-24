from app.services.six_import_service import SixParser
from pathlib import Path

data=Path("backend/storage/commessa_0007/uploads/20251123T130448_3600_20-11-2025.xml").read_bytes()
p=SixParser(data)
print('opts', len(p.list_preventivi()))
