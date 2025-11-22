from sqlmodel import select
from app.db.session import session_scope
from app.db.models import VoceComputo
from app.services.importer import _description_signature_from_model, _description_signature_from_parsed
from app.excel import parse_computo_excel
from pathlib import Path

file_path = Path("backend/storage/commessa_0001/uploads/20251116T201824_4440_ES_E_LC_01_-_Lista_delle_lavorazioni_per_appalto_opere_civili.xlsx")
parser_result = parse_computo_excel(file_path, sheet_name="4440 ES E LC 01")
excel_map = {}
for voce in parser_result.voci:
    key = _description_signature_from_parsed(voce)
    if key and key not in excel_map:
        excel_map[key] = voce.prezzo_unitario

with session_scope() as session:
    voce = session.exec(select(VoceComputo).where(VoceComputo.computo_id==1, VoceComputo.codice=='A001.020.02')).first()
    project_sig = _description_signature_from_model(voce)
    price = excel_map.get(project_sig)
    print('project signature', project_sig)
    print('excel price', price)
