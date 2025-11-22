import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { ApiTrendEvoluzione } from "@/types/api";
import { TrendEvoluzioneData } from "@/lib/grafici-utils";

interface TrendEvoluzioneFilters {
  impresa?: string | null;
}

interface TrendEvoluzioneResult {
  data: TrendEvoluzioneData[];
  rounds: Array<{
    numero: number;
    label: string;
    imprese: string[];
    impreseCount: number;
  }>;
  filtri: {
    roundNumber: number | null;
    impresa: string | null;
    impresaNormalizzata: string | null;
    offerteTotali: number;
    offerteConsiderate: number;
    impreseAttive: string[];
  };
}

export function useTrendEvoluzioneData(
  commessaId: string,
  filters?: TrendEvoluzioneFilters,
) {
  return useQuery<TrendEvoluzioneResult>({
    queryKey: ["trend-round", commessaId, filters?.impresa ?? null],
    queryFn: async () => {
      const data = await api.getCommessaTrendRound(commessaId, {
        impresa: filters?.impresa ?? null,
      });
      return mapTrendEvoluzioneResponse(data);
    },
    enabled: !!commessaId,
  });
}

function mapTrendEvoluzioneResponse(
  data: ApiTrendEvoluzione,
): TrendEvoluzioneResult {
  const trendData: TrendEvoluzioneData[] = (data.imprese ?? []).map((impresa) => ({
    impresa: impresa.impresa,
    color: impresa.color,
    offerte: (impresa.offerte ?? []).map((offerta) => ({
      round: offerta.round,
      roundLabel: offerta.round_label ?? `Round ${offerta.round}`,
      importo: roundNumber(offerta.importo),
      delta: offerta.delta != null ? roundNumber(offerta.delta, 2) : undefined,
    })),
    deltaComplessivo:
      impresa.delta_complessivo != null
        ? roundNumber(impresa.delta_complessivo, 2)
        : undefined,
  }));

  const rounds = (data.rounds ?? []).map((round) => ({
    numero: round.numero,
    label: round.label,
    imprese: [...(round.imprese ?? [])],
    impreseCount: round.imprese_count ?? 0,
  }));

  const filtri = {
    roundNumber: data.filtri?.round_number ?? null,
    impresa: data.filtri?.impresa ?? null,
    impresaNormalizzata: data.filtri?.impresa_normalizzata ?? null,
    offerteTotali: data.filtri?.offerte_totali ?? 0,
    offerteConsiderate: data.filtri?.offerte_considerate ?? 0,
    impreseAttive: data.filtri?.imprese_attive ?? [],
  };

  return {
    data: trendData,
    rounds,
    filtri,
  };
}

function roundNumber(value: number, decimals = 2): number {
  const factor = 10 ** decimals;
  return Math.round((value ?? 0) * factor) / factor;
}
