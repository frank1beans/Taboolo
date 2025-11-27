#!/usr/bin/env python
"""
Script di test per debug import LC/MC con analisi dettagliata dei warning
"""
import sys
from pathlib import Path

# Aggiungi backend al path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select
from app.db.session import engine
from app.db.models import Commessa, Computo, ComputoTipo, PriceListItem, VoceComputo
from app.services.importers.lc import LcImportService

def analyze_price_list(session: Session, commessa_id: int):
    """Analizza l'elenco prezzi per la commessa"""
    items = session.exec(
        select(PriceListItem).where(PriceListItem.commessa_id == commessa_id)
    ).all()

    print(f"\n📋 ELENCO PREZZI (Commessa {commessa_id})")
    print(f"   Totale voci: {len(items)}")

    if items:
        print(f"\n   Prime 5 voci:")
        for item in items[:5]:
            print(f"   - ID {item.id}: {item.item_code or 'NO CODE'} | {item.item_description[:50] if item.item_description else 'NO DESC'}")
    else:
        print("   ⚠️ NESSUN ELENCO PREZZI TROVATO! Import LC fallirà.")

    return items

def analyze_computo_progetto(session: Session, commessa_id: int):
    """Analizza il computo di progetto (MC base)"""
    computo = session.exec(
        select(Computo)
        .where(
            Computo.commessa_id == commessa_id,
            Computo.tipo == ComputoTipo.progetto,
        )
        .order_by(Computo.created_at.desc())
    ).first()

    print(f"\n📐 COMPUTO METRICO DI PROGETTO")
    if not computo:
        print("   ⚠️ NESSUN COMPUTO PROGETTO TROVATO! Import MC/ritorno fallirà.")
        return None, []

    print(f"   Computo ID: {computo.id}")
    print(f"   Nome: {computo.nome}")
    print(f"   File: {computo.file_nome}")

    voci = session.exec(
        select(VoceComputo)
        .where(VoceComputo.computo_id == computo.id)
        .order_by(VoceComputo.ordine)
    ).all()

    print(f"   Totale voci: {len(voci)}")

    with_progressivo = [v for v in voci if v.progressivo]
    print(f"   Voci con progressivo: {len(with_progressivo)}")

    if voci:
        print(f"\n   Prime 5 voci:")
        for voce in voci[:5]:
            prog = f"#{voce.progressivo}" if voce.progressivo else "NO PROG"
            print(f"   - {prog} | {voce.codice or 'NO CODE'} | {voce.descrizione[:50] if voce.descrizione else 'NO DESC'}")

    return computo, voci

def test_import(
    commessa_id: int,
    file_path: Path,
    impresa: str,
    mode: str,
    code_columns: list[str],
    description_columns: list[str],
    progressive_column: str | None,
    price_column: str,
    quantity_column: str | None,
):
    """Testa l'import e cattura tutti i warning"""

    session = Session(engine)

    try:
        print("="*80)
        print(f"🧪 TEST IMPORT {mode.upper()}")
        print("="*80)
        print(f"Commessa ID: {commessa_id}")
        print(f"File: {file_path.name}")
        print(f"Impresa: {impresa}")
        print(f"Mode: {mode}")
        print(f"\nColonne configurate:")
        print(f"  - Progressivo: {progressive_column}")
        print(f"  - Codice: {code_columns}")
        print(f"  - Descrizione: {description_columns}")
        print(f"  - Prezzo: {price_column}")
        print(f"  - Quantità: {quantity_column}")

        # Analisi pre-import
        price_items = analyze_price_list(session, commessa_id)
        computo_prog, prog_voci = analyze_computo_progetto(session, commessa_id)

        print("\n" + "="*80)
        print("🚀 AVVIO IMPORT...")
        print("="*80)

        service = LcImportService()

        computo = service.import_ritorno_gara(
            session=session,
            commessa_id=commessa_id,
            impresa=impresa,
            file=file_path,
            originale_nome=file_path.name,
            round_number=None,
            round_mode="auto",
            sheet_name=None,
            sheet_code_columns=code_columns if code_columns else None,
            sheet_description_columns=description_columns if description_columns else None,
            sheet_price_column=price_column if mode == "lc" else None,
            sheet_quantity_column=quantity_column,
            sheet_progressive_column=progressive_column,
            mode=mode,
        )

        print("\n" + "="*80)
        print("✅ IMPORT COMPLETATO")
        print("="*80)
        print(f"Computo ID: {computo.id}")
        print(f"Importo totale: €{computo.importo_totale:,.2f}" if computo.importo_totale else "Importo: N/A")
        print(f"Round: {computo.round_number}")

        if computo.note:
            print(f"\n⚠️ NOTE/WARNING:\n{computo.note}")

        if computo.matching_report:
            print(f"\n📊 MATCHING REPORT:")
            report = computo.matching_report
            if isinstance(report, dict):
                for key, value in report.items():
                    if isinstance(value, list):
                        print(f"   {key}: {len(value)} items")
                        if value and len(value) <= 5:
                            for item in value:
                                print(f"      - {item}")
                    else:
                        print(f"   {key}: {value}")

        # Analisi voci importate
        voci_importate = session.exec(
            select(VoceComputo)
            .where(VoceComputo.computo_id == computo.id)
            .order_by(VoceComputo.ordine)
        ).all()

        print(f"\n📦 VOCI IMPORTATE: {len(voci_importate)}")

        voci_con_prezzo = [v for v in voci_importate if v.prezzo_unitario and v.prezzo_unitario > 0]
        voci_senza_prezzo = [v for v in voci_importate if not v.prezzo_unitario or v.prezzo_unitario == 0]

        print(f"   ✅ Con prezzo: {len(voci_con_prezzo)}")
        print(f"   ❌ Senza prezzo: {len(voci_senza_prezzo)}")

        if voci_senza_prezzo:
            print(f"\n   Prime 10 voci SENZA PREZZO:")
            for voce in voci_senza_prezzo[:10]:
                prog = f"#{voce.progressivo}" if voce.progressivo else "NO PROG"
                print(f"      {prog} | {voce.codice or 'NO CODE'} | {voce.descrizione[:60] if voce.descrizione else 'NO DESC'}")

        if voci_con_prezzo:
            print(f"\n   Prime 5 voci CON PREZZO:")
            for voce in voci_con_prezzo[:5]:
                prog = f"#{voce.progressivo}" if voce.progressivo else "NO PROG"
                print(f"      {prog} | €{voce.prezzo_unitario:.2f} | {voce.descrizione[:50] if voce.descrizione else 'NO DESC'}")

        session.rollback()  # Non committiamo per mantenere il DB pulito

        return computo

    except Exception as e:
        print(f"\n❌ ERRORE DURANTE L'IMPORT:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Messaggio: {str(e)}")
        import traceback
        print(f"\nStack trace:")
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    # Configurazione test
    COMMESSA_ID = 8
    FILE_PATH = Path(r"c:\Users\f.biggi\Taboolo\backend\storage\commessa_0008\uploads\20251127T150324_3600_ES_E_EC_02b_-_Computo_metrico_estimativo_Opere_civili.xlsx")
    IMPRESA = "TEST_DEBUG"

    # Colonne specificate dall'utente
    MODE = "mc"  # Cambia in "lc" se vuoi testare modalità LC
    PROGRESSIVE_COLUMN = "N."
    CODE_COLUMNS = ["CODICE"]
    DESCRIPTION_COLUMNS = ["INDICAZIONE DEI LAVORI E DELLE PROVVISTE"]
    PRICE_COLUMN = "PU GARC"
    QUANTITY_COLUMN = "QUANTITA'"

    print("\n🔧 Configurazione test:")
    print(f"   Testando modalità: {MODE.upper()}")
    print(f"   File: {FILE_PATH.name}")

    if not FILE_PATH.exists():
        print(f"\n❌ ERRORE: File non trovato: {FILE_PATH}")
        sys.exit(1)

    test_import(
        commessa_id=COMMESSA_ID,
        file_path=FILE_PATH,
        impresa=IMPRESA,
        mode=MODE,
        code_columns=CODE_COLUMNS,
        description_columns=DESCRIPTION_COLUMNS,
        progressive_column=PROGRESSIVE_COLUMN,
        price_column=PRICE_COLUMN,
        quantity_column=QUANTITY_COLUMN,
    )
