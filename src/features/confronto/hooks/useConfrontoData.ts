import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useMemo } from "react";
import { ConfrontoData, ConfrontoRow, ImpresaView, OffertaRecord, VoceConfronto } from "../types";
import { getImpresaFieldPrefix, resolveOfferta } from "../utils";
import { ApiConfrontoOfferte } from "@/types/api";

const IMPRESA_COLORS = [
    "bg-blue-50 border-blue-200",
    "bg-amber-50 border-amber-200",
    "bg-green-50 border-green-200",
    "bg-purple-50 border-purple-200",
    "bg-slate-50 border-slate-200",
];

function mapConfrontoResponse(data: ApiConfrontoOfferte): ConfrontoData {
    const imprese = data.imprese.map((impresa, index) => {
        const roundNumber = impresa.round_number ?? null;
        const roundLabel = impresa.round_label ?? (roundNumber != null ? `Round ${roundNumber}` : null);

        return {
            nomeImpresa: impresa.nome,
            colore: IMPRESA_COLORS[index % IMPRESA_COLORS.length],
            roundNumber,
            roundLabel,
            impresaOriginale: impresa.impresa ?? null,
            normalizedLabel: impresa.etichetta ?? null,
        };
    });

    const rounds = (data.rounds ?? []).map((round) => ({
        numero: round.numero,
        label: round.label,
        imprese: [...round.imprese],
        impreseCount: round.imprese_count ?? round.imprese.length,
    }));

    const voci = data.voci.map<VoceConfronto>((voce) => {
        const codice =
            voce.codice ??
            voce.wbs7_code ??
            voce.wbs6_code ??
            voce.descrizione ??
            "";
        const descrizione =
            voce.descrizione ??
            voce.wbs7_description ??
            voce.wbs6_description ??
            voce.codice ??
            "";
        const descrizioneEstesa =
            voce.descrizione_estesa ??
            voce.descrizione ??
            voce.wbs7_description ??
            voce.wbs6_description ??
            voce.codice ??
            "";

        return {
            progressivo: voce.progressivo ?? null,
            codice,
            descrizione,
            descrizione_estesa: descrizioneEstesa || undefined,
            um: voce.unita_misura ?? "",
            quantita: voce.quantita ?? 0,
            prezzoUnitarioProgetto: voce.prezzo_unitario_progetto ?? 0,
            importoTotaleProgetto: voce.importo_totale_progetto ?? 0,
            wbs6Code: voce.wbs6_code ?? null,
            wbs6Description: voce.wbs6_description ?? null,
            wbs7Code: voce.wbs7_code ?? null,
            wbs7Description: voce.wbs7_description ?? null,
            offerte: Object.fromEntries(
                Object.entries(voce.offerte ?? {}).map(([impresa, offerta]) => [
                    impresa,
                    {
                        quantita: offerta.quantita ?? 0,
                        prezzoUnitario: offerta.prezzo_unitario ?? 0,
                        importoTotale: offerta.importo_totale ?? 0,
                        deltaQuantita: offerta.delta_quantita ?? null,
                        criticita: offerta.criticita ?? undefined,
                        note: offerta.note ?? undefined,
                    },
                ]),
            ),
        };
    });

    return { voci, imprese, rounds };
}

export function useConfrontoData(commessaId: string, selectedRound: number | "all" = "all") {
    const { data, isLoading, error, refetch } = useQuery<ConfrontoData>({
        queryKey: ["confronto", commessaId],
        queryFn: async () => {
            const response = await api.getCommessaConfronto(commessaId);
            return mapConfrontoResponse(response);
        },
        enabled: !!commessaId,
        staleTime: 5 * 60 * 1000,
        gcTime: 15 * 60 * 1000,
    });

    const filteredImprese = useMemo<ImpresaView[]>(() => {
        const list = (data?.imprese ?? []) as ImpresaView[];
        if (selectedRound === "all") return list;
        return list.filter((imp) => imp.roundNumber === selectedRound);
    }, [data?.imprese, selectedRound]);

    const rowData = useMemo<ConfrontoRow[]>(() => {
        if (!data?.voci) return [];

        return data.voci.map((voce, index) => {
            const offerteByLabel: Record<string, OffertaRecord> = voce.offerte ?? {};
            const normalizedOffers = new Map<string, OffertaRecord>();
            Object.entries(offerteByLabel).forEach(([label, offerta]) => {
                normalizedOffers.set(label.trim().toLowerCase(), offerta);
            });

            const row: ConfrontoRow = {
                id: `${voce.codice}-${index}`,
                progressivo: voce.progressivo ?? null,
                codice: voce.codice,
                descrizione: voce.descrizione,
                descrizione_estesa: voce.descrizione_estesa,
                um: voce.um,
                quantita: voce.quantita,
                prezzoUnitarioProgetto: voce.prezzoUnitarioProgetto,
                importoTotaleProgetto: voce.importoTotaleProgetto,
                wbs6Code: voce.wbs6Code,
                wbs6Description: voce.wbs6Description,
                wbs7Code: voce.wbs7Code,
                wbs7Description: voce.wbs7Description,
            };

            const prezziVisibili: number[] = [];
            const offerCache = new Map<string, OffertaRecord | null>();
            let hasQuantityMismatch = false;

            filteredImprese.forEach((impresa) => {
                const fieldPrefix = getImpresaFieldPrefix(impresa);
                const offerta = resolveOfferta(impresa, offerteByLabel, normalizedOffers);
                offerCache.set(fieldPrefix, offerta);

                if (offerta && typeof offerta.prezzoUnitario === "number") {
                    row[`${fieldPrefix}_prezzoUnitario`] = offerta.prezzoUnitario;
                    prezziVisibili.push(offerta.prezzoUnitario);
                } else {
                    row[`${fieldPrefix}_prezzoUnitario`] = null;
                }

                row[`${fieldPrefix}_importoTotale`] =
                    offerta && typeof offerta.importoTotale === "number" ? offerta.importoTotale : null;
                row[`${fieldPrefix}_quantita`] =
                    offerta && typeof offerta.quantita === "number" ? offerta.quantita : null;
                row[`${fieldPrefix}_deltaQuantita`] =
                    offerta && typeof offerta.deltaQuantita === "number" ? offerta.deltaQuantita : null;

                if (offerta && offerta.prezzoUnitario != null && voce.prezzoUnitarioProgetto) {
                    row[`${fieldPrefix}_deltaPerc`] =
                        ((offerta.prezzoUnitario - voce.prezzoUnitarioProgetto) /
                            voce.prezzoUnitarioProgetto) *
                        100;
                } else {
                    row[`${fieldPrefix}_deltaPerc`] = null;
                }

                if (
                    offerta &&
                    typeof offerta.deltaQuantita === "number" &&
                    Math.abs(offerta.deltaQuantita) > 1e-6
                ) {
                    hasQuantityMismatch = true;
                }
            });

            if (prezziVisibili.length) {
                const somma = prezziVisibili.reduce((acc, curr) => acc + curr, 0);
                const media = somma / prezziVisibili.length;
                const minimo = Math.min(...prezziVisibili);
                const massimo = Math.max(...prezziVisibili);
                const deviazione =
                    prezziVisibili.length > 1
                        ? Math.sqrt(
                            prezziVisibili.reduce((acc, curr) => acc + Math.pow(curr - media, 2), 0) /
                            prezziVisibili.length,
                        )
                        : 0;
                row.mediaPrezzi = media;
                row.minimoPrezzi = minimo;
                row.massimoPrezzi = massimo;
                row.deviazionePrezzi = deviazione;

                filteredImprese.forEach((impresa) => {
                    const fieldPrefix = getImpresaFieldPrefix(impresa);
                    const offerta = offerCache.get(fieldPrefix);
                    if (!offerta || offerta.prezzoUnitario == null || Math.abs(media) < 1e-9) {
                        row[`${fieldPrefix}_deltaMedia`] = null;
                        return;
                    }
                    row[`${fieldPrefix}_deltaMedia`] = ((offerta.prezzoUnitario - media) / media) * 100;
                });
            } else {
                row.mediaPrezzi = null;
                row.minimoPrezzi = null;
                row.massimoPrezzi = null;
                row.deviazionePrezzi = null;
                filteredImprese.forEach((impresa) => {
                    const fieldPrefix = getImpresaFieldPrefix(impresa);
                    row[`${fieldPrefix}_deltaMedia`] = null;
                });
            }

            row.hasQuantityMismatch = hasQuantityMismatch;
            return row;
        });
    }, [data?.voci, filteredImprese]);

    return {
        data,
        isLoading,
        error,
        refetch,
        rowData,
        filteredImprese,
        rounds: data?.rounds ?? [],
    };
}
