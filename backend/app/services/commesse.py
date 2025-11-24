from __future__ import annotations

from typing import Sequence

from sqlmodel import Session, select

from app.db.models import Commessa, Computo, ComputoTipo
from app.schemas import CommessaCreate
from .storage import storage_service


class CommesseService:

    @staticmethod
    def list_commesse(session: Session) -> Sequence[Commessa]:
        statement = select(Commessa).order_by(Commessa.created_at.desc())
        return session.exec(statement).all()

    @staticmethod
    def get_commessa(session: Session, commessa_id: int) -> Commessa | None:
        return session.get(Commessa, commessa_id)

    @staticmethod
    def get_commessa_with_computi(
        session: Session, commessa_id: int
    ) -> tuple[Commessa | None, list[Computo]]:
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            return None, []
        statement = (
            select(Computo)
            .where(Computo.commessa_id == commessa_id)
            .order_by(Computo.created_at.desc())
        )
        computi = session.exec(statement).all()
        return commessa, list(computi)

    @staticmethod
    def create_commessa(session: Session, payload: CommessaCreate) -> Commessa:
        commessa = Commessa.model_validate(payload)
        session.add(commessa)
        session.commit()
        session.refresh(commessa)
        return commessa

    @staticmethod
    def update_commessa(session: Session, commessa_id: int, payload: CommessaCreate) -> Commessa | None:
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            return None
        
        commessa.nome = payload.nome
        commessa.codice = payload.codice
        commessa.descrizione = payload.descrizione
        commessa.note = payload.note
        commessa.business_unit = payload.business_unit
        commessa.revisione = payload.revisione
        commessa.stato = payload.stato
        
        session.add(commessa)
        session.commit()
        session.refresh(commessa)
        return commessa

    @staticmethod
    def add_computo(
        session: Session,
        commessa: Commessa,
        *,
        nome: str,
        tipo: ComputoTipo,
        impresa: str | None = None,
        impresa_id: int | None = None,
        round_number: int | None = None,
        file_nome: str | None = None,
        file_percorso: str | None = None,
    ) -> Computo:
        computo = Computo(
            commessa_id=commessa.id,
            commessa_code=commessa.codice,
            nome=nome,
            tipo=tipo,
            impresa=impresa,
            impresa_id=impresa_id,
            round_number=round_number,
            file_nome=file_nome,
            file_percorso=file_percorso,
        )
        session.add(computo)
        session.commit()
        session.refresh(computo)
        return computo

    @staticmethod
    def delete_computo(session: Session, commessa_id: int, computo_id: int) -> Computo | None:
        from app.db.models import VoceComputo
        
        computo = session.get(Computo, computo_id)
        if not computo or computo.commessa_id != commessa_id:
            return None
        file_path = computo.file_percorso
        
        # Delete associated voci first
        session.exec(
            VoceComputo.__table__.delete().where(VoceComputo.computo_id == computo_id)
        )
        
        session.delete(computo)
        session.commit()

        storage_service.delete_file(file_path)
        return computo

    @staticmethod
    def delete_commessa(session: Session, commessa_id: int) -> Commessa | None:
        from app.db.models import VoceComputo
        
        commessa = session.get(Commessa, commessa_id)
        if not commessa:
            return None
        
        # Get all computi for this commessa (needed to delete stored files)
        statement = select(Computo).where(Computo.commessa_id == commessa_id)
        computi = session.exec(statement).all()
        file_paths = [computo.file_percorso for computo in computi if computo.file_percorso]
        
        # Delete all voci for all computi
        for computo in computi:
            session.exec(
                VoceComputo.__table__.delete().where(VoceComputo.computo_id == computo.id)
            )
        
        # Delete all computi
        session.exec(
            Computo.__table__.delete().where(Computo.commessa_id == commessa_id)
        )
        
        # Finally delete the commessa
        session.delete(commessa)
        session.commit()

        for file_path in file_paths:
            storage_service.delete_file(file_path)
        storage_service.delete_commessa_dir(commessa_id)
        return commessa
