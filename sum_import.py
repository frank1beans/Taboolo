from sqlmodel import select
from app.db.session import session_scope
from app.db.models import VoceComputo

with session_scope() as session:
    rows = session.exec(select(VoceComputo).where(VoceComputo.computo_id==2)).all()
    total = sum((row.importo or 0.0) for row in rows)
    print('computed total', total)
