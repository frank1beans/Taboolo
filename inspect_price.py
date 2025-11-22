from sqlmodel import select
from app.db.session import session_scope
from app.db.models import VoceComputo

with session_scope() as session:
    rows = session.exec(select(VoceComputo).where(VoceComputo.computo_id==2, VoceComputo.codice=='A001.020.02')).all()
    for row in rows[:5]:
        print(row.quantita, row.prezzo_unitario)
