from typing import Dict, List, Optional

from sqlmodel import Session

from app.db.models import Computo, VoceComputo
from app.schemas import (
    AnalisiCommessaSchema,
    AnalisiConfrontoImportoSchema,
    AnalisiFiltriSchema,
    AnalisiImpresaSchema,
    AnalisiRoundSchema,
    AnalisiThresholdsSchema,
    AnalisiWBS6CriticitaSchema,
    AnalisiWBS6TrendSchema,
    AnalisiWBS6VoceSchema,
)
from app.services.analysis.core import CoreAnalysisService


class AnalysisService:
    @staticmethod
    def get_commessa_analisi(
        session: Session,
        commessa_id: int,
        *,
        round_number: int | None = None,
        impresa: str | None = None,
    ) -> AnalisiCommessaSchema:
        data = CoreAnalysisService.prepare_commessa_data(session, commessa_id)
        computi: List[Computo] = data["computi"]
        progetto: Optional[Computo] = data["progetto"]
        ritorni: List[Computo] = data["ritorni"]
        entries: List[dict] = data["entries"]
        voci_by_computo: Dict[int, List[VoceComputo]] = data["voci_by_computo"]
        imprese_info: List[dict] = data["imprese"]
        label_by_id: Dict[int, str] = data["label_by_id"]

        normalized_imprese = CoreAnalysisService.normalize_imprese(imprese_info)
        thresholds = CoreAnalysisService.load_thresholds(session)

        (
            allowed_ids,
            allowed_labels,
            normalized_filter,
        ) = CoreAnalysisService.determine_allowed_offerte(
            normalized_imprese,
            round_number=round_number,
            impresa=impresa,
        )

        if allowed_ids is None:
            filtered_ritorni = ritorni
        else:
            filtered_ritorni = [item for item in ritorni if item.id in allowed_ids]

        filtered_entries = CoreAnalysisService.filter_entries(entries, allowed_labels)

        totale_imprese = len(normalized_imprese)
        if allowed_labels is None:
            imprese_attive = [item["nome"] for item in normalized_imprese]
        elif not allowed_labels:
            imprese_attive = []
        else:
            imprese_attive = sorted(allowed_labels)
        imprese_rilevanti = len(imprese_attive) or len(normalized_imprese)

        if not computi:
            return AnalisiCommessaSchema(
                confronto_importi=[],
                distribuzione_variazioni=[],
                voci_critiche=[],
                analisi_per_wbs6=[],
                rounds=[
                    AnalisiRoundSchema(
                        numero=round_info["numero"],
                        label=round_info["label"],
                        imprese=round_info["imprese"],
                        imprese_count=round_info["imprese_count"],
                    )
                    for round_info in CoreAnalysisService.build_rounds(normalized_imprese)
                ],
                imprese=[
                    AnalisiImpresaSchema(
                        computo_id=item["computo_id"],
                        nome=item["nome"],
                        impresa=item.get("impresa"),
                        etichetta=item.get("etichetta"),
                        round_number=item.get("round_number"),
                        round_label=item.get("round_label"),
                    )
                    for item in normalized_imprese
                ],
                filtri=AnalisiFiltriSchema(
                    round_number=round_number,
                    impresa=impresa,
                    impresa_normalizzata=normalized_filter,
                    offerte_totali=totale_imprese,
                    offerte_considerate=len(imprese_attive),
                    imprese_attive=imprese_attive,
                ),
                thresholds=AnalisiThresholdsSchema(
                    media_percent=thresholds["media"],
                    alta_percent=thresholds["alta"],
                ),
            )

        importi_by_computo: Dict[int, float] = {}
        for computo in computi:
            if computo.importo_totale is not None:
                importi_by_computo[computo.id] = float(computo.importo_totale)
            else:
                totale = sum((voce.importo or 0) for voce in voci_by_computo.get(computo.id, []))
                importi_by_computo[computo.id] = round(totale, 2)

        confronto_importi: List[AnalisiConfrontoImportoSchema] = []
        importo_progetto = importi_by_computo.get(progetto.id) if progetto else None

        if progetto and importo_progetto is not None:
            confronto_importi.append(
                AnalisiConfrontoImportoSchema(
                    nome=progetto.nome,
                    tipo=progetto.tipo,
                    importo=round(importo_progetto, 2),
                    delta_percentuale=0.0,
                    impresa=progetto.impresa,
                    round_number=progetto.round_number,
                )
            )

        for ritorno in filtered_ritorni:
            valore = importi_by_computo.get(ritorno.id, 0.0)
            delta = None
            if importo_progetto and abs(importo_progetto) > 1e-9:
                delta = round(((valore - importo_progetto) / importo_progetto) * 100, 2)
            confronto_importi.append(
                AnalisiConfrontoImportoSchema(
                    nome=label_by_id.get(ritorno.id, CoreAnalysisService._label_ritorno(ritorno)),
                    tipo=ritorno.tipo,
                    importo=round(valore, 2),
                    delta_percentuale=delta,
                    impresa=ritorno.impresa,
                    round_number=ritorno.round_number,
                )
            )

        distribuzione_variazioni = CoreAnalysisService.build_distribuzione(filtered_entries)
        voci_critiche = CoreAnalysisService.build_voci_critiche(filtered_entries, thresholds)

        wbs6_analysis = CoreAnalysisService.build_wbs6_analisi(
            filtered_entries,
            totale_imprese=imprese_rilevanti,
            thresholds=thresholds,
        )
        analisi_per_wbs6 = [
            AnalisiWBS6TrendSchema(
                wbs6_id=cat["wbs6_id"],
                wbs6_label=cat["wbs6_label"],
                wbs6_code=cat.get("wbs6_code"),
                wbs6_description=cat.get("wbs6_description"),
                progetto=cat["progetto"],
                media_ritorni=cat["media_ritorni"],
                delta_percentuale=cat["delta_percentuale"],
                delta_assoluto=cat["delta_assoluto"],
                conteggi_criticita=AnalisiWBS6CriticitaSchema(
                    **cat["conteggi_criticita"]
                ),
                offerte_considerate=cat["offerte_considerate"],
                offerte_totali=cat["offerte_totali"],
                voci=[
                    AnalisiWBS6VoceSchema(**voce)
                    for voce in cat["voci"]
                ],
            )
            for cat in wbs6_analysis
        ]

        return AnalisiCommessaSchema(
            confronto_importi=confronto_importi,
            distribuzione_variazioni=distribuzione_variazioni,
            voci_critiche=voci_critiche,
            analisi_per_wbs6=analisi_per_wbs6,
            rounds=[
                AnalisiRoundSchema(
                    numero=round_info["numero"],
                    label=round_info["label"],
                    imprese=round_info["imprese"],
                    imprese_count=round_info["imprese_count"],
                )
                for round_info in CoreAnalysisService.build_rounds(normalized_imprese)
            ],
            imprese=[
                AnalisiImpresaSchema(
                    computo_id=item["computo_id"],
                    nome=item["nome"],
                    impresa=item.get("impresa"),
                    etichetta=item.get("etichetta"),
                    round_number=item.get("round_number"),
                    round_label=item.get("round_label"),
                )
                for item in normalized_imprese
            ],
            filtri=AnalisiFiltriSchema(
                round_number=round_number,
                impresa=impresa,
                impresa_normalizzata=normalized_filter,
                offerte_totali=totale_imprese,
                offerte_considerate=len(imprese_attive),
                imprese_attive=imprese_attive,
            ),
            thresholds=AnalisiThresholdsSchema(
                media_percent=thresholds["media"],
                alta_percent=thresholds["alta"],
            ),
        )

    @staticmethod
    def get_commessa_wbs6_dettaglio(
        session: Session,
        commessa_id: int,
        wbs6_id: str,
        *,
        round_number: int | None = None,
        impresa: str | None = None,
    ) -> AnalisiWBS6TrendSchema:
        data = CoreAnalysisService.prepare_commessa_data(session, commessa_id)
        entries: List[dict] = data["entries"]
        imprese_info: List[dict] = data["imprese"]

        normalized_imprese = CoreAnalysisService.normalize_imprese(imprese_info)
        totale_imprese = len(normalized_imprese)
        thresholds = CoreAnalysisService.load_thresholds(session)

        (
            _allowed_ids,
            allowed_labels,
            _normalized_filter,
        ) = CoreAnalysisService.determine_allowed_offerte(
            normalized_imprese,
            round_number=round_number,
            impresa=impresa,
        )

        if allowed_labels is None:
            filtered_entries = entries
        else:
            filtered_entries = CoreAnalysisService.filter_entries(entries, allowed_labels)

        wbs6_analysis = CoreAnalysisService.build_wbs6_analisi(
            filtered_entries,
            totale_imprese=totale_imprese,
            thresholds=thresholds,
        )

        for categoria in wbs6_analysis:
            if categoria["wbs6_id"] == wbs6_id:
                return AnalisiWBS6TrendSchema(
                    wbs6_id=categoria["wbs6_id"],
                    wbs6_label=categoria["wbs6_label"],
                    wbs6_code=categoria.get("wbs6_code"),
                    wbs6_description=categoria.get("wbs6_description"),
                    progetto=categoria["progetto"],
                    media_ritorni=categoria["media_ritorni"],
                    delta_percentuale=categoria["delta_percentuale"],
                    delta_assoluto=categoria["delta_assoluto"],
                    conteggi_criticita=AnalisiWBS6CriticitaSchema(
                        **categoria["conteggi_criticita"]
                    ),
                    offerte_considerate=categoria["offerte_considerate"],
                    offerte_totali=categoria["offerte_totali"],
                    voci=[
                        AnalisiWBS6VoceSchema(**voce)
                        for voce in categoria["voci"]
                    ],
                )

        raise ValueError("Categoria WBS6 non trovata")
