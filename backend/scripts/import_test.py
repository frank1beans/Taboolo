import sys
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy import func

sys.path.append('backend')

from app.db import init_db, engine
from app.schemas import CommessaCreate
from app.services import AnalysisService, CommesseService, import_service
from app.db.models import VoceComputo


def main() -> None:
    init_db()
    with Session(engine) as session:
        commessa = CommesseService.create_commessa(
            session, CommessaCreate(nome='Test', codice='TEST')
        )
        session.refresh(commessa)
        computo = import_service.import_computo_progetto(
            session=session,
            commessa_id=commessa.id,
            file=Path(r'4345 ES E EC 01 - Computo metrico estimativo opere civili.xlsx'),
            originale_nome='computo.xlsx',
        )
        session.refresh(computo)
        count = session.exec(
            select(func.count()).select_from(VoceComputo).where(VoceComputo.computo_id == computo.id)
        ).one()
        summary = AnalysisService.get_wbs_summary(session, computo.id)
        print(
            {
                'commessa_id': commessa.id,
                'computo_id': computo.id,
                'voci_salvate': count,
                'wbs_nodes': len(summary.tree),
                'voci_aggregate': len(summary.voci),
            }
        )
        sample = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == computo.id)
            .order_by(VoceComputo.ordine)
            .limit(3)
        ).all()
        for voce in sample:
            print(
                'Voce',
                voce.codice,
                'Q',
                voce.quantita,
                'P',
                voce.prezzo_unitario,
                'Importo',
                voce.importo,
            )
        if summary.tree:
            first_node = summary.tree[0]
            print('Primo nodo WBS:', first_node.code, first_node.description, first_node.importo)
        if summary.voci:
            first_voice = summary.voci[0]
            print('Prima voce aggregata:', first_voice.codice, first_voice.quantita_totale, first_voice.importo_totale)


if __name__ == "__main__":
    main()
