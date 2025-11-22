from pathlib import Path
from app.excel import parse_computo_excel
from app.services.importer import _build_description_price_map
file_path = Path("backend/storage/commessa_0001/uploads/20251116T201824_4440_ES_E_LC_01_-_Lista_delle_lavorazioni_per_appalto_opere_civili.xlsx")
parser_result = parse_computo_excel(file_path, sheet_name="4440 ES E LC 01")
price_map = _build_description_price_map(parser_result.voci)
sig = "protezione dei pavimenti durante l'esecuzione dei lavori, mediante apposizione di telo di idonea tipologia e spessore, adeguatamente fissato, compreso il ripristino in caso di ammaloramento e/o danneggiamento in corso d'opera e la rimozione finale, compresi eventuali oneri di smaltimento.|m2|a001"
print('price map entry', price_map.get(sig))
