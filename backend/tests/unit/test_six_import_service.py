from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile
import unittest

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.db.models import (
    Commessa,
    CommessaStato,
    Computo,
    ComputoTipo,
    PriceListItem,
    VoceComputo,
)  # noqa: E402
from app.db.models_wbs import Voce as VoceNorm, VoceProgetto, Wbs6, WbsSpaziale  # noqa: E402
from app.services.six_import_service import (
    PreventivoSelectionError,
    six_import_service,
)  # noqa: E402


SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 01 - Lotto/Edificio">
    <grpValore grpValoreId="w1" vlrId="A">
      <vlrDescrizione lingua="it" breve="Edificio A" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 02 - Livelli">
    <grpValore grpValoreId="w2" vlrId="P00">
      <vlrDescrizione lingua="it" breve="Piano Terra" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 03 - Ambiti Omogenei">
    <grpValore grpValoreId="w3" vlrId="UFF">
      <vlrDescrizione lingua="it" breve="Uffici" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 04 - Appalto/Fase">
    <grpValore grpValoreId="w4" vlrId="0">
      <vlrDescrizione lingua="it" breve="Appalto base" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A001">
      <vlrDescrizione lingua="it" breve="Cantierizzazioni" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A001.010">
      <vlrDescrizione lingua="it" breve="Noli" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <unitaDiMisura unitaDiMisuraId="1" udmId="mq" simbolo="m²">
      <udmDescrizione lingua="it" breve="metri quadrati" />
    </unitaDiMisura>
    <prodotto prodottoId="p1" prdId="A001.010.01" unitaDiMisuraId="1">
      <prdDescrizione lingua="it" breve="Voce breve" estesa="Voce estesa di prova" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="25.00" listaQuotazioneId="L1" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="CME001" prezzarioId="1">
    <prvDescrizione lingua="it" breve="CME Test" />
    <prvRilevazione prvRilevazioneId="100" rilevazione="Misura" progressivo="1" prodottoId="p1" listaQuotazioneId="L1">
      <prvGrpValore grpValoreId="w1" />
      <prvGrpValore grpValoreId="w2" />
      <prvGrpValore grpValoreId="w3" />
      <prvGrpValore grpValoreId="w4" />
      <prvMisura>
        <prvCella testo="5" posizione="1" />
        <prvCella testo="2" posizione="3" />
        <prvCommento lingua="it" estesa="Area A" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_MULTI = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A001">
      <vlrDescrizione lingua="it" breve="Cantierizzazioni" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A001.010">
      <vlrDescrizione lingua="it" breve="Noli" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <unitaDiMisura unitaDiMisuraId="1" udmId="mq" simbolo="m²">
      <udmDescrizione lingua="it" breve="metri quadrati" />
    </unitaDiMisura>
    <prodotto prodottoId="p1" prdId="A001.010.01" unitaDiMisuraId="1">
      <prdDescrizione lingua="it" breve="Voce breve" estesa="Voce estesa" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="25.00" listaQuotazioneId="L1" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="CME001" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Preventivo P1" />
    <prvRilevazione prvRilevazioneId="100" rilevazione="Misura" progressivo="1" prodottoId="p1" listaQuotazioneId="L1">
      <prvMisura>
        <prvCella testo="5" posizione="1" />
        <prvCella testo="2" posizione="3" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
  <preventivo preventivoId="20" prvId="CME002" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Preventivo P2" />
    <prvRilevazione prvRilevazioneId="200" rilevazione="Misura" progressivo="1" prodottoId="p1" listaQuotazioneId="L1">
      <prvMisura>
        <prvCella testo="3" posizione="1" />
        <prvCella testo="4" posizione="3" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_SPATIAL_SPLIT = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 01 - Lotto/Edificio">
    <grpValore grpValoreId="w1a" vlrId="A">
      <vlrDescrizione lingua="it" breve="Edificio A" />
    </grpValore>
    <grpValore grpValoreId="w1b" vlrId="B">
      <vlrDescrizione lingua="it" breve="Edificio B" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A050">
      <vlrDescrizione lingua="it" breve="Strutture" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A050.010">
      <vlrDescrizione lingua="it" breve="Solai" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <unitaDiMisura unitaDiMisuraId="udm" udmId="mq" simbolo="mq" />
    <prodotto prodottoId="p1" prdId="A050.010.01" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Solaio" estesa="Getto di solaio" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="15.00" listaQuotazioneId="L1" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="CME001" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Preventivo WBS spaziali" />
    <prvRilevazione prvRilevazioneId="10" rilevazione="Misura" progressivo="10" prodottoId="p1" listaQuotazioneId="L1">
      <prvGrpValore grpValoreId="w1a" />
      <prvMisura>
        <prvCella testo="5" posizione="1" />
        <prvCella testo="2" posizione="3" />
      </prvMisura>
    </prvRilevazione>
    <prvRilevazione prvRilevazioneId="20" rilevazione="Misura" progressivo="20" prodottoId="p1" listaQuotazioneId="L1">
      <prvGrpValore grpValoreId="w1b" />
      <prvMisura>
        <prvCella testo="4" posizione="0" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_DUPLICATE_PRICE_LISTS = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A001">
      <vlrDescrizione lingua="it" breve="Categoria base" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A001.010">
      <vlrDescrizione lingua="it" breve="Sottocategoria" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <listaQuotazione listaQuotazioneId="L100" lqtId="01">
      <lqtDescrizione lingua="it" breve="Prezzi Base" />
    </listaQuotazione>
    <listaQuotazione listaQuotazioneId="L200" lqtId="02">
      <lqtDescrizione lingua="it" breve="Prezzi Base" />
    </listaQuotazione>
    <unitaDiMisura unitaDiMisuraId="udm" udmId="pz" simbolo="pz" />
    <prodotto prodottoId="dup-1" prdId="A001.010.001" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Articolo duplicato 1" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="10.00" listaQuotazioneId="L100" />
    </prodotto>
    <prodotto prodottoId="dup-2" prdId="A001.010.002" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Articolo duplicato 2" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="20.00" listaQuotazioneId="L200" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="DUP-PL" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Listini duplicati" />
    <prvRilevazione prvRilevazioneId="10" rilevazione="Misura" progressivo="10" prodottoId="dup-1" listaQuotazioneId="L100">
      <prvGrpValore grpValoreId="w6" />
      <prvGrpValore grpValoreId="w7" />
      <prvMisura>
        <prvCella testo="1" posizione="0" />
      </prvMisura>
    </prvRilevazione>
    <prvRilevazione prvRilevazioneId="20" rilevazione="Misura" progressivo="20" prodottoId="dup-2" listaQuotazioneId="L200">
      <prvGrpValore grpValoreId="w6" />
      <prvGrpValore grpValoreId="w7" />
      <prvMisura>
        <prvCella testo="1" posizione="0" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_PRICE_DUPLICATES = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="B100">
      <vlrDescrizione lingua="it" breve="Categoria test" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="B100.010">
      <vlrDescrizione lingua="it" breve="Sottocategoria test" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <listaQuotazione listaQuotazioneId="603" lqtId="01">
      <lqtDescrizione lingua="it" breve="Prezzi Base" />
    </listaQuotazione>
    <unitaDiMisura unitaDiMisuraId="udm" udmId="pz" simbolo="pz" />
    <prodotto prodottoId="dup-a" prdId="B100.010.01" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Articolo duplicato" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="10.00" listaQuotazioneId="603" />
    </prodotto>
    <prodotto prodottoId="dup-b" prdId="B100.010.01" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Articolo duplicato" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="12.00" listaQuotazioneId="603" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="DUP-CAT" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Preventivo duplicati" />
    <prvRilevazione prvRilevazioneId="10" rilevazione="Misura" progressivo="10" prodottoId="dup-a" listaQuotazioneId="603">
      <prvMisura>
        <prvCella testo="2" posizione="0" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_REFERENCES = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A020">
      <vlrDescrizione lingua="it" breve="Controsoffitti" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A020.030">
      <vlrDescrizione lingua="it" breve="Pannelli" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <unitaDiMisura unitaDiMisuraId="udm" udmId="mq" simbolo="mq">
      <udmDescrizione lingua="it" breve="Metri quadrati" />
    </unitaDiMisura>
    <prodotto prodottoId="p-base" prdId="A020.030.01" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Smontaggio" estesa="Smontaggio pannelli" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="20.00" listaQuotazioneId="L1" />
    </prodotto>
    <prodotto prodottoId="p-ded" prdId="A020.030.02" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Deduzione" estesa="Deduzione CE01" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="5.00" listaQuotazioneId="L1" />
    </prodotto>
    <prodotto prodottoId="p-ref" prdId="A020.030.07" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Rimontaggio" estesa="Rimontaggio pannelli" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="16.00" listaQuotazioneId="L1" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="CME001" prezzarioId="1">
    <prvDescrizione lingua="it" breve="CME Test" />
    <prvRilevazione prvRilevazioneId="100" rilevazione="Misura" progressivo="100" prodottoId="p-base" listaQuotazioneId="L1">
      <prvMisura>
        <prvCella testo="10" posizione="0" />
      </prvMisura>
    </prvRilevazione>
    <prvRilevazione prvRilevazioneId="110" rilevazione="Misura" progressivo="110" prodottoId="p-ded" listaQuotazioneId="L1">
      <prvMisura>
        <prvCella testo="2" posizione="0" />
      </prvMisura>
    </prvRilevazione>
    <prvRilevazione prvRilevazioneId="120" rilevazione="Misura" progressivo="120" prodottoId="p-ref" listaQuotazioneId="L1">
      <prvMisura>
        <prvCommento lingua="it" estesa="Rimontaggio pannelli" />
      </prvMisura>
      <prvMisura>
        <prvCommento lingua="it" estesa="vedi voce n. 100" />
      </prvMisura>
      <prvMisura operazione="-">
        <prvCommento lingua="it" estesa="A DEDURRE" />
      </prvMisura>
      <prvMisura>
        <prvCommento lingua="it" estesa="vedi voce n. 110" />
      </prvMisura>
    </prvRilevazione>
  </preventivo>
</Documento>
"""

SAMPLE_XML_ZERO = """<?xml version="1.0" encoding="utf-8"?>
<Documento xmlns="six.xsd">
  <gruppo tipo="WBS 01 - Lotto/Edificio">
    <grpValore grpValoreId="w1" vlrId="A">
      <vlrDescrizione lingua="it" breve="Edificio A" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 06 - Categorie merceologiche">
    <grpValore grpValoreId="w6" vlrId="A100">
      <vlrDescrizione lingua="it" breve="Mark up GC" />
    </grpValore>
  </gruppo>
  <gruppo tipo="WBS 07 -Subcategorie merceologiche">
    <grpValore grpValoreId="w7" vlrId="A100.010">
      <vlrDescrizione lingua="it" breve="Subappalti" />
    </grpValore>
  </gruppo>
  <prezzario prezzarioId="1" przId="TEST">
    <unitaDiMisura unitaDiMisuraId="udm" udmId="mq" simbolo="mq" />
    <prodotto prodottoId="pz" prdId="A100.010.01" unitaDiMisuraId="udm">
      <prdDescrizione lingua="it" breve="Mark up GC" estesa="Mark up fee" />
      <prdGrpValore grpValoreId="w6" />
      <prdGrpValore grpValoreId="w7" />
      <prdQuotazione valore="0.25" listaQuotazioneId="L1" />
    </prodotto>
  </prezzario>
  <preventivo preventivoId="10" prvId="CME001" prezzarioId="1">
    <prvDescrizione lingua="it" breve="Preventivo zero" />
    <prvRilevazione prvRilevazioneId="200" rilevazione="Misura" progressivo="1" prodottoId="pz" listaQuotazioneId="L1">
      <prvGrpValore grpValoreId="w1" />
    </prvRilevazione>
  </preventivo>
</Documento>
"""


class SixImportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            commessa = Commessa(
                nome="Test",
                codice="C001",
                stato=CommessaStato.setup,
            )
            session.add(commessa)
            session.commit()
            session.refresh(commessa)
            self.commessa_id = commessa.id
        self._temp_files: list[Path] = []

    def tearDown(self) -> None:
        for path in self._temp_files:
            if path.exists():
                path.unlink()

    def _write_xml_file(self, content: str, suffix: str) -> Path:
        tmp = NamedTemporaryFile(delete=False, suffix=suffix)
        with open(tmp.name, "w", encoding="utf-8") as handle:
            handle.write(content)
        path = Path(tmp.name)
        self._temp_files.append(path)
        return path

    def _write_six_file(self, content: str) -> Path:
        tmp = NamedTemporaryFile(delete=False, suffix=".six")
        with ZipFile(tmp.name, "w") as archive:
            archive.writestr("documento.xml", content)
        path = Path(tmp.name)
        self._temp_files.append(path)
        return path

    def test_inspect_details_returns_structure(self) -> None:
        details = six_import_service.inspect_details(SAMPLE_XML.encode("utf-8"), "test.xml")
        self.assertEqual(details["products_total"], 1)
        self.assertEqual(len(details["preventivi"]), 1)
        preventivo = details["preventivi"][0]
        self.assertEqual(preventivo["internal_id"], "10")
        self.assertEqual(preventivo["rilevazioni"], 1)
        self.assertEqual(preventivo["items"], 1)
        price_list_ids = {entry["canonical_id"] for entry in details["price_lists"]}
        self.assertIn("l1", price_list_ids)
        self.assertEqual(len(details["wbs_spaziali"]), 4)
        self.assertEqual(len(details["wbs6"]), 1)
        self.assertEqual(len(details["wbs7"]), 1)

    def test_imports_plain_xml_file(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["commessa_id"], self.commessa_id)
            self.assertEqual(report["voci"], 1)
            self.assertEqual(report["wbs_spaziali"], 4)
            self.assertEqual(report["wbs6"], 1)
            self.assertEqual(report["wbs7"], 1)
            self.assertAlmostEqual(report["importo_totale"], 250.0)
            wbs6 = session.exec(select(Wbs6)).first()
            self.assertIsNotNone(wbs6)
            self.assertEqual(wbs6.code, "A001")
            spaziali = session.exec(select(WbsSpaziale)).all()
            self.assertEqual(len(spaziali), 4)
            voce_norm = session.exec(select(VoceNorm)).first()
            self.assertEqual(voce_norm.descrizione, "Voce estesa di prova")
            voce_proj = session.exec(select(VoceProgetto)).first()
            self.assertAlmostEqual(voce_proj.quantita or 0, 10.0)
            self.assertAlmostEqual(voce_proj.importo or 0, 250.0)
            computo = session.exec(
                select(Computo).where(
                    Computo.commessa_id == self.commessa_id,
                    Computo.tipo == ComputoTipo.progetto,
                )
            ).first()
            self.assertIsNotNone(computo)
            self.assertEqual(computo.nome, "CME Test")
            catalog_items = session.exec(select(PriceListItem)).all()
            self.assertEqual(len(catalog_items), 1)
            catalog_item = catalog_items[0]
            self.assertEqual(catalog_item.commessa_code, "C001")
            self.assertEqual(catalog_item.item_code, "A001.010.01")
            self.assertIsNotNone(catalog_item.extra_metadata)
            self.assertIsNotNone(catalog_item.price_lists)
            self.assertEqual(catalog_item.price_lists.get("l1"), 25.0)
            metadata = catalog_item.extra_metadata or {}
            self.assertEqual(metadata.get("source"), "six")
            labels = metadata.get("price_list_labels") or {}
            self.assertEqual(labels.get("l1"), "L1")

    def test_preserves_spatial_wbs_quantities(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_SPATIAL_SPLIT, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["voci"], 2)
            self.assertAlmostEqual(report["importo_totale"], 210.0)
            voci = session.exec(
                select(VoceComputo).order_by(VoceComputo.progressivo)
            ).all()
            self.assertEqual(len(voci), 2)
            self.assertEqual(voci[0].wbs_1_code, "A")
            self.assertEqual(voci[1].wbs_1_code, "B")
            self.assertAlmostEqual(voci[0].quantita or 0, 10.0)
            self.assertEqual(voci[0].commessa_code, "C001")
            self.assertIsNotNone(voci[0].extra_metadata)
            self.assertEqual(voci[0].extra_metadata.get("source"), "six")
            self.assertAlmostEqual(voci[1].quantita or 0, 4.0)
            self.assertAlmostEqual(voci[0].importo or 0, 150.0)
            self.assertAlmostEqual(voci[1].importo or 0, 60.0)

    def test_imports_from_six_archive(self) -> None:
        six_path = self._write_six_file(SAMPLE_XML)
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, six_path)
            self.assertEqual(report["voci"], 1)
            self.assertAlmostEqual(report["importo_totale"], 250.0)

    def test_collapses_duplicate_price_lists(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_DUPLICATE_PRICE_LISTS, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["voci"], 2)
            items = session.exec(
                select(PriceListItem).order_by(PriceListItem.item_code)
            ).all()
            self.assertEqual(len(items), 2)
            key_sets = []
            for item in items:
                self.assertIsNotNone(item.price_lists)
                key_sets.append(tuple(sorted(item.price_lists.keys())))
            self.assertEqual(len(set(key_sets)), 1)
            canonical_key = key_sets[0][0]
            self.assertEqual(canonical_key, "prezzi_base")
            values = sorted(item.price_lists.get(canonical_key) for item in items)
            self.assertEqual(values, [10.0, 20.0])
            labels = items[0].extra_metadata.get("price_list_labels", {})
            self.assertEqual(labels.get(canonical_key), "Prezzi Base")

    def test_deduplicates_identical_price_catalog_entries(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_PRICE_DUPLICATES, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["voci"], 1)
            items = session.exec(select(PriceListItem)).all()
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertEqual(item.item_code, "B100.010.01")
            self.assertEqual(item.price_lists.get("prezzi_base"), 10.0)
            self.assertEqual(item.extra_metadata.get("price_list_labels", {}).get("prezzi_base"), "Prezzi Base")

    def test_requires_preventivo_selection_when_multiple(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_MULTI, ".xml")
        with Session(self.engine) as session:
            with self.assertRaises(PreventivoSelectionError):
                six_import_service.import_six_file(session, self.commessa_id, xml_path)
            report = six_import_service.import_six_file(
                session,
                self.commessa_id,
                xml_path,
                preventivo_id="20",
            )
            self.assertEqual(report["voci"], 1)
            self.assertAlmostEqual(report["importo_totale"], 12.0 * 25.0)

    def test_inspect_content_lists_preventivi(self) -> None:
        options = six_import_service.inspect_content(SAMPLE_XML_MULTI.encode("utf-8"), "test.xml")
        self.assertEqual(len(options), 2)
        codes = sorted(opt.code for opt in options)
        self.assertEqual(codes, ["CME001", "CME002"])

    def test_infers_quantity_from_reference_notes(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_REFERENCES, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["voci"], 3)
            self.assertAlmostEqual(report["importo_totale"], 338.0)
            reassembly = session.exec(
                select(VoceComputo).where(VoceComputo.progressivo == 120)
            ).first()
            self.assertIsNotNone(reassembly)
            self.assertAlmostEqual(reassembly.quantita or 0, 8.0)
            self.assertAlmostEqual(reassembly.importo or 0, 128.0)

    def test_preserves_zero_quantity_voci(self) -> None:
        xml_path = self._write_xml_file(SAMPLE_XML_ZERO, ".xml")
        with Session(self.engine) as session:
            report = six_import_service.import_six_file(session, self.commessa_id, xml_path)
            self.assertEqual(report["voci"], 1)
            voce = session.exec(
                select(VoceComputo).where(VoceComputo.codice == "A100.010.01")
            ).first()
            self.assertIsNotNone(voce)
            self.assertAlmostEqual(voce.quantita or 0, 0.0)
            self.assertAlmostEqual(voce.importo or 0, 0.0)



if __name__ == "__main__":
    unittest.main()
