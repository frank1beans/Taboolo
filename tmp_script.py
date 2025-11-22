import sys
sys.path.append("backend")
from pathlib import Path
from sqlmodel import Session, select
from app.db.session import engine
from app.db.models import PriceListItem
from app.services.importer import (_parse_custom_return_excel, _build_price_list_lookup, _match_price_list_item_entry)
path = Path("backend/storage/commessa_0003/uploads/20251119T143907_CAEC.xlsx")
parse_result = _parse_custom_return_excel(path, "EPU - phase 1", ["CODICE"], ["BREVE"], "PREZZO 01", None, None)
rows = [voce for voce in parse_result.computo.voci if voce.codice and voce.codice.startswith("A005.040.5")]
with Session(engine) as session:
    items = session.exec(select(PriceListItem).where(PriceListItem.commessa_id == 3)).all()
code_map, signature_map, description_map, head_map, tail_map, embedding_map = _build_price_list_lookup(items)
for voce in rows:
    item = _match_price_list_item_entry(voce, code_map, signature_map, description_map, head_map, tail_map, embedding_map)
    if item:
        print(voce.codice, '->', item.item_code, item.id)
    else:
        print(voce.codice, '->', None)
