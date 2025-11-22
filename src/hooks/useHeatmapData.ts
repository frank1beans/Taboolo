import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { ApiHeatmapCompetitivita } from "@/types/api";
import { HeatmapData } from "@/lib/grafici-utils";

interface HeatmapFilters {
  round?: number | null;
}

interface HeatmapResult {
  data: HeatmapData;
  filtri: {
    roundNumber: number | null;
    impresa: string | null;
    impresaNormalizzata: string | null;
    offerteTotali: number;
    offerteConsiderate: number;
    impreseAttive: string[];
  };
}

export function useHeatmapData(commessaId: string, filters?: HeatmapFilters) {
  return useQuery<HeatmapResult>({
    queryKey: ["heatmap-competitivita", commessaId, filters?.round ?? null],
    queryFn: async () => {
      const data = await api.getCommessaHeatmapCompetitivita(commessaId, {
        round_number: filters?.round ?? null,
      });
      return mapHeatmapResponse(data);
    },
    enabled: !!commessaId,
  });
}

function mapHeatmapResponse(data: ApiHeatmapCompetitivita): HeatmapResult {
  const categorie = (data.categorie ?? []).map((cat) => ({
    categoria: cat.categoria,
    importoProgetto: roundNumber(cat.importo_progetto),
  }));

  const imprese = (data.imprese ?? []).map((impresa) => ({
    impresa: impresa.impresa,
    categorie: (impresa.categorie ?? []).map((cat) => ({
      categoria: cat.categoria,
      importoOfferta: roundNumber(cat.importo_offerta),
      delta: roundNumber(cat.delta, 2),
    })),
  }));

  const heatmapData: HeatmapData = {
    categorie,
    imprese,
  };

  const filtri = {
    roundNumber: data.filtri?.round_number ?? null,
    impresa: data.filtri?.impresa ?? null,
    impresaNormalizzata: data.filtri?.impresa_normalizzata ?? null,
    offerteTotali: data.filtri?.offerte_totali ?? 0,
    offerteConsiderate: data.filtri?.offerte_considerate ?? 0,
    impreseAttive: data.filtri?.imprese_attive ?? [],
  };

  return {
    data: heatmapData,
    filtri,
  };
}

function roundNumber(value: number, decimals = 2): number {
  const factor = 10 ** decimals;
  return Math.round((value ?? 0) * factor) / factor;
}
