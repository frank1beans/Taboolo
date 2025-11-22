from sqlmodel import select
from app.db.session import session_scope
from app.db.models import VoceComputo

with session_scope() as session:
    rows = session.exec(select(VoceComputo).where(VoceComputo.computo_id==2)).all()
    total_return = 0.0
    for row in rows:
        meta = row.extra_metadata or {}
        total_return += float(meta.get('return_import') or 0.0)
    print('return total', total_return)
