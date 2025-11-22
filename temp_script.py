from app.services.importer import _parse_custom_return_excel
from pathlib import Path
path = Path(r"backend/storage/commessa_0002/uploads/20251119T094354_CAEC.xlsx")
parsed = _parse_custom_return_excel(path, "EPU - phase 1", ["CODICE"], [], "PREZZO 01", None, None)
print('voci:', len(parsed.computo.voci))
print(parsed.computo.voci[0])
