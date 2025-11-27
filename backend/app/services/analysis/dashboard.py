from sqlalchemy import func
from sqlmodel import Session, select

from app.db.models import (
    Commessa,
    Computo,
    ComputoTipo,
)
from app.schemas import (
    DashboardActivitySchema,
    DashboardStatsSchema,
)


class DashboardService:
    @staticmethod
    def get_dashboard_stats(session: Session) -> DashboardStatsSchema:
        commesse_count = session.exec(select(func.count(Commessa.id))).one()
        computi_count = session.exec(select(func.count(Computo.id))).one()
        ritorni_count = session.exec(
            select(func.count(Computo.id)).where(Computo.tipo == ComputoTipo.ritorno)
        ).one()

        recent_rows = session.exec(
            select(Computo, Commessa)
            .join(Commessa, Computo.commessa_id == Commessa.id)
            .order_by(Computo.created_at.desc())
            .limit(5)
        ).all()

        attivita = [
            DashboardActivitySchema(
                computo_id=computo.id,
                computo_nome=computo.nome,
                tipo=computo.tipo,
                commessa_id=commessa.id,
                commessa_codice=commessa.codice,
                commessa_nome=commessa.nome,
                created_at=computo.created_at,
            )
            for computo, commessa in recent_rows
        ]

        return DashboardStatsSchema(
            commesse_attive=commesse_count or 0,
            computi_caricati=computi_count or 0,
            ritorni=ritorni_count or 0,
            report_generati=0,
            attivita_recente=attivita,
        )
