import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { ApiConfrontoOfferte } from "@/types/api";

interface VoceConfronto {
  codice: string;
  descrizione: string;
  descrizione_estesa?: string | null;
  um: string;
  quantita: number;
  prezzoUnitarioProgetto: number;
  importoTotaleProgetto: number;
  wbs6Code?: string | null;
  wbs6Description?: string | null;
  wbs7Code?: string | null;
  wbs7Description?: string | null;
  offerte: Record<
    string,
    {
      quantita: number;
      prezzoUnitario: number;
      importoTotale: number;
      deltaQuantita?: number | null;
      criticita?: string;
      note?: string;
    }
  >;
}

interface ConfrontoData {
  voci: VoceConfronto[];
  imprese: Array<{
    nomeImpresa: string;
    colore: string;
    roundNumber: number | null;
    roundLabel: string | null;
    impresaOriginale: string | null;
    normalizedLabel: string | null;
  }>;
  rounds: Array<{
    numero: number;
    label: string;
    imprese: string[];
    impreseCount: number;
  }>;
}

const IMPRESA_COLORS = [
  "bg-blue-50 border-blue-200",
  "bg-amber-50 border-amber-200",
  "bg-green-50 border-green-200",
  "bg-purple-50 border-purple-200",
  "bg-slate-50 border-slate-200",
];

export function useConfrontoData(commessaId: string) {
  return useQuery<ConfrontoData>({
    queryKey: ["confronto", commessaId],
    queryFn: async () => {
      const response = await api.getCommessaConfronto(commessaId);
      return mapConfrontoResponse(response);
    },
    enabled: !!commessaId,
    staleTime: 5 * 60 * 1000, // 5 minuti - evita refetch inutili
    gcTime: 15 * 60 * 1000,   // 15 minuti - mantiene in cache
  });
}

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
