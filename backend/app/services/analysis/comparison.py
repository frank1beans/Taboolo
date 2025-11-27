from sqlmodel import Session

from app.schemas import (
    ConfrontoImpresaSchema,
    ConfrontoOfferteSchema,
    ConfrontoRoundSchema,
    ConfrontoVoceOffertaSchema,
    ConfrontoVoceSchema,
)
from app.services.analysis.core import CoreAnalysisService


class ComparisonService:
    @staticmethod
    def get_commessa_confronto(session: Session, commessa_id: int) -> ConfrontoOfferteSchema:
        data = CoreAnalysisService.prepare_commessa_data(session, commessa_id)
        normalized_imprese = CoreAnalysisService.normalize_imprese(data["imprese"])

        voci_schema = [
            ConfrontoVoceSchema(
                codice=item["codice"],
                descrizione=item["descrizione"],
                descrizione_estesa=item.get("descrizione_originale") or item.get("descrizione"),
                unita_misura=item["unita_misura"],
                quantita=item["quantita"],
                prezzo_unitario_progetto=item["prezzo_unitario_progetto"],
                importo_totale_progetto=item["importo_totale_progetto"],
                offerte={
                    nome: ConfrontoVoceOffertaSchema(
                        quantita=offerta.get("quantita"),
                        prezzo_unitario=offerta.get("prezzo_unitario"),
                        importo_totale=offerta.get("importo_totale"),
                        note=offerta.get("note"),
                        criticita=offerta.get("criticita"),
                    )
                    for nome, offerta in item["offerte"].items()
                },
                wbs6_code=item["wbs6_code"],
                wbs6_description=item["wbs6_description"],
                wbs7_code=item["wbs7_code"],
                wbs7_description=item["wbs7_description"],
            )
            for item in data["entries"]
        ]

        imprese_schema = [
            ConfrontoImpresaSchema(
                nome=impresa["nome"],
                computo_id=impresa["computo_id"],
                impresa=impresa.get("impresa"),
                round_number=impresa.get("round_number"),
                etichetta=impresa.get("etichetta"),
                round_label=impresa.get("round_label"),
            )
            for impresa in normalized_imprese
        ]

        rounds_schema = [
            ConfrontoRoundSchema(
                numero=round_info["numero"],
                label=round_info["label"],
                imprese=round_info["imprese"],
                imprese_count=round_info["imprese_count"],
            )
            for round_info in CoreAnalysisService.build_rounds(normalized_imprese)
        ]

        return ConfrontoOfferteSchema(
            voci=voci_schema,
            imprese=imprese_schema,
            rounds=rounds_schema,
        )
