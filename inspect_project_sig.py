from sqlmodel import select
from app.db.session import session_scope
from app.db.models import VoceComputo
from app.services.importer import _description_signature_from_model
with session_scope() as session:
    voce = session.exec(select(VoceComputo).where(VoceComputo.computo_id==1, VoceComputo.codice=='A001.020.02')).first()
    print(_description_signature_from_model(voce))
