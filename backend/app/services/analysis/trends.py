from collections import defaultdict
from typing import Dict, List, Optional

from sqlmodel import Session

from app.db.models import Computo, VoceComputo
from app.schemas import (
    AnalisiFiltriSchema,
    AnalisiRoundSchema,
    HeatmapCategoriaSchema,
    HeatmapCompetitivitaSchema,
    HeatmapImpresaCategoriaSchema,
    HeatmapImpresaSchema,
    TrendEvoluzioneImpresaSchema,
    TrendEvoluzioneOffertaSchema,
    TrendEvoluzioneSchema,
)
from app.services.analysis.core import CoreAnalysisService


class TrendsService:
    @staticmethod
    def get_commessa_trend_round(
        session: Session,
        commessa_id: int,
        *,
        impresa: str | None = None,
    ) -> TrendEvoluzioneSchema:
        """Ottiene i dati per il grafico Trend Evoluzione Prezzi tra Round."""

        data = CoreAnalysisService.prepare_commessa_data(session, commessa_id)
        computi: List[Computo] = data["computi"]
        ritorni: List[Computo] = data["ritorni"]
        voci_by_computo: Dict[int, List[VoceComputo]] = data["voci_by_computo"]
        imprese_info: List[dict] = data["imprese"]

        normalized_imprese = CoreAnalysisService.normalize_imprese(imprese_info)

        # Applica filtro impresa se specificato
        (
            allowed_ids,
            allowed_labels,
            normalized_filter,
        ) = CoreAnalysisService.determine_allowed_offerte(
            normalized_imprese,
            round_number=None,  # Non filtriamo per round nel trend
            impresa=impresa,
        )

        if allowed_ids is not None:
            filtered_imprese = [imp for imp in normalized_imprese if imp["nome"] in (allowed_labels or [])]
        else:
            filtered_imprese = normalized_imprese

        # Calcola importi per computo
        importi_by_computo: Dict[int, float] = {}
        for computo in computi:
            if computo.importo_totale is not None:
                importi_by_computo[computo.id] = float(computo.importo_totale)
            else:
                totale = sum((voce.importo or 0) for voce in voci_by_computo.get(computo.id, []))
                importi_by_computo[computo.id] = round(totale, 2)

        # Raggruppa per round e impresa
        rounds_data: Dict[int, dict] = {}
        imprese_data: Dict[str, dict] = {}

        # Colori per le imprese (palette)
        colors = [
            "hsl(217 91% 60%)",  # Blu
            "hsl(142 71% 45%)",  # Verde
            "hsl(38 92% 55%)",   # Arancione
            "hsl(0 84% 60%)",    # Rosso
            "hsl(260 80% 65%)",  # Viola
            "hsl(180 80% 50%)",  # Ciano
            "hsl(300 70% 60%)",  # Magenta
            "hsl(45 100% 51%)",  # Giallo
        ]

        # Traccia indice colore per impresa base (per assegnare stesso colore a stessa impresa)
        color_by_base: Dict[str, str] = {}
        color_idx = 0

        for impresa_info in filtered_imprese:
            # Usa base_label per raggruppare la stessa impresa tra round diversi
            base_label = impresa_info.get("base_label") or impresa_info["nome"]
            computo_id = impresa_info["computo_id"]
            round_number = impresa_info.get("round_number") or 0
            round_label = impresa_info.get("round_label") or f"Round {round_number}"

            importo = importi_by_computo.get(computo_id, 0.0)

            if base_label not in imprese_data:
                # Assegna colore alla prima occorrenza dell'impresa
                if base_label not in color_by_base:
                    color_by_base[base_label] = colors[color_idx % len(colors)]
                    color_idx += 1
                imprese_data[base_label] = {
                    "impresa": base_label,
                    "color": color_by_base[base_label],
                    "offerte_by_round": {}
                }

            imprese_data[base_label]["offerte_by_round"][round_number] = {
                "round": round_number,
                "round_label": round_label,
                "importo": importo,
            }

            if round_number not in rounds_data:
                rounds_data[round_number] = {
                    "numero": round_number,
                    "label": round_label,
                    "imprese": [],
                }
            if base_label not in rounds_data[round_number]["imprese"]:
                rounds_data[round_number]["imprese"].append(base_label)

        # Costruisci lista imprese con calcolo delta
        imprese_list = []
        for impresa_info in imprese_data.values():
            offerte_sorted = sorted(
                impresa_info["offerte_by_round"].values(),
                key=lambda x: x["round"]
            )

            # Calcola delta per ogni offerta rispetto al round precedente
            for i, offerta in enumerate(offerte_sorted):
                if i == 0:
                    offerta["delta"] = 0.0
                else:
                    prev_importo = offerte_sorted[i - 1]["importo"]
                    if prev_importo and abs(prev_importo) > 1e-9:
                        offerta["delta"] = round(
                            ((offerta["importo"] - prev_importo) / prev_importo) * 100, 2
                        )
                    else:
                        offerta["delta"] = 0.0

            # Calcola delta complessivo (primo vs ultimo)
            delta_complessivo = None
            if len(offerte_sorted) > 1:
                primo_importo = offerte_sorted[0]["importo"]
                ultimo_importo = offerte_sorted[-1]["importo"]
                if primo_importo and abs(primo_importo) > 1e-9:
                    delta_complessivo = round(
                        ((ultimo_importo - primo_importo) / primo_importo) * 100, 2
                    )

            imprese_list.append(
                TrendEvoluzioneImpresaSchema(
                    impresa=impresa_info["impresa"],
                    color=impresa_info["color"],
                    offerte=[
                        TrendEvoluzioneOffertaSchema(**off) for off in offerte_sorted
                    ],
                    delta_complessivo=delta_complessivo,
                )
            )

        # Costruisci lista rounds
        rounds_list = [
            AnalisiRoundSchema(
                numero=rd["numero"],
                label=rd["label"],
                imprese=rd["imprese"],
                imprese_count=len(rd["imprese"]),
            )
            for rd in sorted(rounds_data.values(), key=lambda x: x["numero"])
        ]

        # Costruisci filtri
        totale_imprese = len(normalized_imprese)
        imprese_attive = [imp.impresa for imp in imprese_list]

        filtri = AnalisiFiltriSchema(
            round_number=None,
            impresa=impresa,
            impresa_normalizzata=normalized_filter,
            offerte_totali=totale_imprese,
            offerte_considerate=len(imprese_attive),
            imprese_attive=imprese_attive,
        )

        return TrendEvoluzioneSchema(
            imprese=imprese_list,
            rounds=rounds_list,
            filtri=filtri,
        )

    @staticmethod
    def get_commessa_heatmap_competitivita(
        session: Session,
        commessa_id: int,
        *,
        round_number: int | None = None,
    ) -> HeatmapCompetitivitaSchema:
        """Ottiene i dati per il grafico Heatmap Competitività."""

        data = CoreAnalysisService.prepare_commessa_data(session, commessa_id)
        entries: List[dict] = data["entries"]
        imprese_info: List[dict] = data["imprese"]

        normalized_imprese = CoreAnalysisService.normalize_imprese(imprese_info)
        thresholds = CoreAnalysisService.load_thresholds(session)

        # Applica filtro round se specificato
        (
            _allowed_ids,
            allowed_labels,
            normalized_filter,
        ) = CoreAnalysisService.determine_allowed_offerte(
            normalized_imprese,
            round_number=round_number,
            impresa=None,
        )

        filtered_entries = CoreAnalysisService.filter_entries(entries, allowed_labels)

        # Costruisci analisi WBS6 per avere i dati aggregati
        totale_imprese = len(normalized_imprese)
        wbs6_analysis = CoreAnalysisService.build_wbs6_analisi(
            filtered_entries,
            totale_imprese=totale_imprese,
            thresholds=thresholds,
        )

        # Mappa per raccogliere dati per impresa e categoria
        imprese_categorie_map: Dict[str, Dict[str, dict]] = defaultdict(lambda: {})
        categorie_progetto: Dict[str, float] = {}

        # Per ogni categoria WBS6, estraiamo i dati per ogni impresa
        for wbs6_cat in wbs6_analysis:
            wbs6_label = wbs6_cat["wbs6_label"]
            progetto = wbs6_cat["progetto"]
            categorie_progetto[wbs6_label] = progetto

            # Per ogni voce nella categoria, raccogliamo le offerte per impresa
            ritorni_per_impresa: Dict[str, float] = defaultdict(float)
            for voce in wbs6_cat["voci"]:
                # Cerchiamo la voce originale in entries per ottenere le offerte
                voce_entry = next(
                    (e for e in filtered_entries if e.get("codice") == voce.get("codice")),
                    None
                )
                if voce_entry:
                    offerte = voce_entry.get("offerte") or {}
                    for impresa_nome, off_data in offerte.items():
                        importo_totale = float(off_data.get("importo_totale") or 0.0)
                        ritorni_per_impresa[impresa_nome] += importo_totale

            # Ora popoliamo la mappa imprese-categorie
            for impresa_nome, importo_offerta in ritorni_per_impresa.items():
                delta = 0.0
                if progetto and abs(progetto) > 1e-9:
                    delta = round(((importo_offerta - progetto) / progetto) * 100, 2)

                imprese_categorie_map[impresa_nome][wbs6_label] = {
                    "categoria": wbs6_label,
                    "importo_offerta": importo_offerta,
                    "delta": delta,
                }

        # Costruisci lista categorie
        categorie_list = [
            HeatmapCategoriaSchema(
                categoria=cat_label,
                importo_progetto=importo_prog,
            )
            for cat_label, importo_prog in sorted(
                categorie_progetto.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

        # Costruisci lista imprese
        imprese_list = []
        for impresa_nome in sorted(imprese_categorie_map.keys()):
            categorie_impresa = imprese_categorie_map[impresa_nome]

            # Crea lista categorie per questa impresa (in ordine delle categorie globali)
            categorie_ordinate = []
            for cat in categorie_list:
                cat_label = cat.categoria
                if cat_label in categorie_impresa:
                    categorie_ordinate.append(
                        HeatmapImpresaCategoriaSchema(**categorie_impresa[cat_label])
                    )
                else:
                    # Impresa non ha offerto per questa categoria
                    categorie_ordinate.append(
                        HeatmapImpresaCategoriaSchema(
                            categoria=cat_label,
                            importo_offerta=0.0,
                            delta=0.0,
                        )
                    )

            imprese_list.append(
                HeatmapImpresaSchema(
                    impresa=impresa_nome,
                    categorie=categorie_ordinate,
                )
            )

        # Costruisci filtri
        imprese_attive = list(imprese_categorie_map.keys())

        filtri = AnalisiFiltriSchema(
            round_number=round_number,
            impresa=None,
            impresa_normalizzata=normalized_filter,
            offerte_totali=totale_imprese,
            offerte_considerate=len(imprese_attive),
            imprese_attive=sorted(imprese_attive),
        )

        return HeatmapCompetitivitaSchema(
            categorie=categorie_list,
            imprese=imprese_list,
            filtri=filtri,
        )
