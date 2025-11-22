from pathlib import Path
from app.db.session import session_scope
from app.services.importer import ImportService

service = ImportService()
file_path = Path("backend/storage/commessa_0001/uploads/20251116T201824_4440_ES_E_LC_01_-_Lista_delle_lavorazioni_per_appalto_opere_civili.xlsx")
with session_scope() as session:
    computo = service.import_computo_ritorno(
        session=session,
        commessa_id=1,
        impresa="CEV",
        file=file_path,
        originale_nome=file_path.name,
        sheet_name="4440 ES E LC 01",
        sheet_code_columns=["C"],
        sheet_description_columns=["E"],
        sheet_price_column="H",
        sheet_quantity_column="G",
        sheet_wbs6_code_column="A",
        sheet_wbs6_description_column="B",
    )
    print("Created computo", computo.id, computo.nome)
