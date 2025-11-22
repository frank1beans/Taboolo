from sqlmodel import select, delete
from app.db.session import session_scope
from app.db.models import Computo, ComputoTipo, VoceComputo

with session_scope() as session:
    comps = session.exec(select(Computo).where(Computo.tipo==ComputoTipo.ritorno)).all()
    for comp in comps:
        session.exec(delete(VoceComputo).where(VoceComputo.computo_id==comp.id))
        session.delete(comp)
    session.commit()
