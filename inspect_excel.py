from pathlib import Path
from app.excel import parse_computo_excel
file_path = Path("backend/storage/commessa_0001/uploads/20251116T201824_4440_ES_E_LC_01_-_Lista_delle_lavorazioni_per_appalto_opere_civili.xlsx")
parser_result = parse_computo_excel(file_path, sheet_name="4440 ES E LC 01")
for voce in parser_result.voci[:20]:
    print(voce.codice, voce.descrizione[:60], voce.quantita, voce.prezzo_unitario)
