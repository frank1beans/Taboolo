import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { ApiAnalisiCommessa, ApiAnalisiWBS6Trend } from "@/types/api";

interface AnalisiFilters {
  round?: number | null;
  impresa?: string | null;
}

interface AnalisiFiltriState {
  roundNumber: number | null;
  impresa: string | null;
  impresaNormalizzata: string | null;
  offerteTotali: number;
  offerteConsiderate: number;
  impreseAttive: string[];
}

interface AnalisiImpresaOption {
  key: string;
  nome: string;
  label: string;
  normalized: string | null;
  impresaOriginale: string | null;
  roundNumber: number | null;
  roundLabel: string | null;
  computoId: number;
}

interface AnalisiRoundOption {
  numero: number;
  label: string;
  imprese: string[];
  impreseCount: number;
}

interface AnalisiWbs6Voce {
  codice: string | null;
  descrizione: string | null;
  descrizioneEstesa: string | null;
  unitaMisura: string | null;
  quantita: number | null;
  prezzoUnitarioProgetto: number | null;
  importoTotaleProgetto: number | null;
  mediaPrezzoUnitario: number | null;
  mediaImportoTotale: number | null;
  deltaPercentuale: number | null;
  deltaAssoluto: number | null;
  offerteConsiderate: number;
  importoMinimo: number | null;
  importoMassimo: number | null;
  impresaMin: string | null;
  impresaMax: string | null;
  deviazioneStandard: number | null;
  criticita: string | null;
  direzione: string | null;
}

export interface AnalisiVoceCriticaItem {
  codice: string;
  descrizione: string;
  descrizioneEstesa: string | null;
  progetto: number;
  delta: number;
  criticita: string;
  deltaAssoluto: number;
  mediaPrezzoUnitario: number | null;
  mediaImportoTotale: number | null;
  minOfferta: number | null;
  maxOfferta: number | null;
  impresaMin: string | null;
  impresaMax: string | null;
  deviazioneStandard: number | null;
  direzione: string;
  imprese: Record<string, number>;
}

export interface AnalisiWbs6 {
  wbs6Id: string;
  wbs6Label: string;
  wbs6Code: string | null;
  wbs6Description: string | null;
  progetto: number;
  media: number;
  delta: number;
  deltaAssoluto: number;
  conteggiCriticita: {
    alta: number;
    media: number;
    bassa: number;
  };
  offerteConsiderate: number;
  offerteTotali: number;
  voci: AnalisiWbs6Voce[];
}

interface AnalisiData {
  confrontoImporti: Array<{
    impresa: string;
    importo: number;
    delta: number;
    colore: string;
    tipo: string;
    roundNumber: number | null;
    impresaOriginale: string | null;
    impresaNormalized: string | null;
  }>;
  distribuzioneVariazioni: Array<{
    nome: string;
    valore: number;
    colore: string;
  }>;
  vociCritiche: AnalisiVoceCriticaItem[];
  analisiPerWbs6: AnalisiWbs6[];
  rounds: AnalisiRoundOption[];
  imprese: AnalisiImpresaOption[];
  filtri: AnalisiFiltriState;
  thresholds: {
    mediaPercent: number;
    altaPercent: number;
  };
}

const BAR_COLORS = ["#6b7280", "#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

const normalizeImpresaLabel = (value: string | null | undefined, round?: number | null): string | null => {
  if (!value) return null;
  const clean = value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "")
    .toLowerCase();
  if (round && round > 0) {
    return `${clean}-r${round}`;
  }
  return clean;
};

export function useAnalisiData(commessaId: string, filters?: AnalisiFilters) {
  return useQuery<AnalisiData>({
    queryKey: ["analisi", commessaId, filters?.round ?? null, filters?.impresa ?? null],
    queryFn: async () => {
      const data = await api.getCommessaAnalisi(commessaId, {
        round_number: filters?.round ?? null,
        impresa: filters?.impresa ?? null,
      });
      return mapAnalisiResponse(data);
    },
    enabled: !!commessaId,
    staleTime: 5 * 60 * 1000, // 5 minuti - evita refetch inutili
    gcTime: 15 * 60 * 1000,   // 15 minuti - mantiene in cache
  });
}

export function useAnalisiWbs6Dettaglio(
  commessaId: string,
  wbs6Id: string | null,
  filters?: AnalisiFilters,
) {
  return useQuery<AnalisiWbs6 | null>({
    queryKey: [
      "analisi",
      "wbs6",
      commessaId,
      wbs6Id,
      filters?.round ?? null,
      filters?.impresa ?? null,
    ],
    queryFn: async () => {
      if (!wbs6Id) {
        return null;
      }

      const response = await api.getCommessaAnalisiWbs6(commessaId, wbs6Id, {
        round_number: filters?.round ?? null,
        impresa: filters?.impresa ?? null,
      });

      return mapWbs6Trend(response, response.offerte_totali ?? 0);
    },
    enabled: Boolean(commessaId && wbs6Id),
    staleTime: 5 * 60 * 1000, // 5 minuti
    gcTime: 15 * 60 * 1000,   // 15 minuti
  });
}

function mapAnalisiResponse(data: ApiAnalisiCommessa): AnalisiData {
  const rounds = (data.rounds ?? []).map<AnalisiRoundOption>((round) => ({
    numero: round.numero,
    label: round.label,
    imprese: [...(round.imprese ?? [])],
    impreseCount: round.imprese_count ?? 0,
  }));

  const imprese = (data.imprese ?? []).map<AnalisiImpresaOption>((impresa) => {
    const normalized = normalizeImpresaLabel(impresa.etichetta ?? impresa.nome, impresa.round_number);
    const baseLabel = impresa.etichetta ?? impresa.nome;
    const roundLabel = impresa.round_number ? `Round ${impresa.round_number}` : null;
    const compositeLabel = roundLabel ? `${baseLabel} (${roundLabel})` : baseLabel;
    const key = `${normalized ?? baseLabel}-${impresa.round_number ?? "all"}`;
    return {
      key,
      nome: compositeLabel,
      label: compositeLabel,
      normalized,
      impresaOriginale: impresa.impresa ?? null,
      roundNumber: impresa.round_number ?? null,
      roundLabel,
      computoId: impresa.computo_id,
    };
  });

  const filtri: AnalisiFiltriState = {
    roundNumber: data.filtri?.round_number ?? null,
    impresa: data.filtri?.impresa ?? null,
    impresaNormalizzata: data.filtri?.impresa_normalizzata ?? null,
    offerteTotali: data.filtri?.offerte_totali ?? imprese.length,
    offerteConsiderate: data.filtri?.offerte_considerate ?? imprese.length,
    impreseAttive: data.filtri?.imprese_attive ?? imprese.map((i) => i.label),
  };

  const confrontoImporti = (data.confronto_importi ?? []).map((item, index) => ({
    impresa: item.nome,
    importo: roundNumber(item.importo),
    delta: roundNumber(item.delta_percentuale ?? 0, 1),
    colore: BAR_COLORS[index % BAR_COLORS.length],
    tipo: item.tipo,
    roundNumber: item.round_number ?? null,
    impresaOriginale: item.impresa ?? null,
    impresaNormalized: normalizeImpresaLabel(item.impresa ?? item.nome),
  }));

  const distribuzioneVariazioni = (data.distribuzione_variazioni ?? []).map((entry) => ({
    nome: entry.nome,
    valore: entry.valore,
    colore: entry.colore,
  }));

  const vociCritiche = (data.voci_critiche ?? []).map<AnalisiVoceCriticaItem>((voce) => ({
    codice: voce.codice ?? "",
    descrizione: voce.descrizione ?? "",
    descrizioneEstesa: voce.descrizione_estesa ?? voce.descrizione ?? null,
    progetto: roundNumber(voce.progetto ?? 0),
    delta: roundNumber(voce.delta ?? 0, 1),
    criticita: voce.criticita ?? "bassa",
    deltaAssoluto: roundNumber(voce.delta_assoluto ?? 0),
    mediaPrezzoUnitario:
      voce.media_prezzo_unitario !== undefined && voce.media_prezzo_unitario !== null
        ? roundNumber(voce.media_prezzo_unitario)
        : null,
    mediaImportoTotale:
      voce.media_importo_totale !== undefined && voce.media_importo_totale !== null
        ? roundNumber(voce.media_importo_totale)
        : null,
    minOfferta:
      voce.min_offerta !== undefined && voce.min_offerta !== null
        ? roundNumber(voce.min_offerta)
        : null,
    maxOfferta:
      voce.max_offerta !== undefined && voce.max_offerta !== null
        ? roundNumber(voce.max_offerta)
        : null,
    impresaMin: voce.impresa_min ?? null,
    impresaMax: voce.impresa_max ?? null,
    deviazioneStandard:
      voce.deviazione_standard !== undefined && voce.deviazione_standard !== null
        ? roundNumber(voce.deviazione_standard)
        : null,
    direzione: voce.direzione ?? "neutro",
    imprese: Object.fromEntries(
      Object.entries(voce.imprese ?? {}).map(([nome, valore]) => [nome, roundNumber(valore ?? 0)]),
    ),
  }));

  const wbs6Trends = (data.analisi_per_wbs6 ?? []).map((item) =>
    mapWbs6Trend(item, data.imprese?.length ?? 0),
  );

  const thresholds = {
    mediaPercent: data.thresholds?.media_percent ?? 25,
    altaPercent: data.thresholds?.alta_percent ?? 50,
  };

  return {
    confrontoImporti,
    distribuzioneVariazioni,
    vociCritiche,
    analisiPerWbs6: wbs6Trends,
    rounds,
    imprese,
    filtri,
    thresholds,
  };
}

function mapWbs6Trend(
  item: ApiAnalisiWBS6Trend,
  fallbackTotaleImprese: number,
): AnalisiWbs6 {
  const progetto = roundNumber(item.progetto ?? 0);
  const media = roundNumber(item.media_ritorni ?? 0);
  const delta = roundNumber(item.delta_percentuale ?? 0, 1);
  const deltaAssoluto = roundNumber(item.delta_assoluto ?? media - progetto);
  const offerteTotali = item.offerte_totali ?? fallbackTotaleImprese;

  return {
    wbs6Id: item.wbs6_id,
    wbs6Label: item.wbs6_label,
    wbs6Code: item.wbs6_code ?? null,
    wbs6Description: item.wbs6_description ?? null,
    progetto,
    media,
    delta,
    deltaAssoluto,
    conteggiCriticita: {
      alta: item.conteggi_criticita?.alta ?? 0,
      media: item.conteggi_criticita?.media ?? 0,
      bassa: item.conteggi_criticita?.bassa ?? 0,
    },
    offerteConsiderate: item.offerte_considerate ?? 0,
    offerteTotali,
    voci: (item.voci ?? []).map<AnalisiWbs6Voce>((voce) => ({
      codice: voce.codice ?? null,
    descrizione: voce.descrizione ?? null,
    descrizioneEstesa: voce.descrizione_estesa ?? voce.descrizione ?? null,
      unitaMisura: voce.unita_misura ?? null,
      quantita:
        voce.quantita !== undefined && voce.quantita !== null
          ? roundNumber(voce.quantita)
          : null,
      prezzoUnitarioProgetto:
        voce.prezzo_unitario_progetto !== undefined &&
        voce.prezzo_unitario_progetto !== null
          ? roundNumber(voce.prezzo_unitario_progetto)
          : null,
      importoTotaleProgetto:
        voce.importo_totale_progetto !== undefined &&
        voce.importo_totale_progetto !== null
          ? roundNumber(voce.importo_totale_progetto)
          : null,
      mediaPrezzoUnitario:
        voce.media_prezzo_unitario !== undefined &&
        voce.media_prezzo_unitario !== null
          ? roundNumber(voce.media_prezzo_unitario)
          : null,
      mediaImportoTotale:
        voce.media_importo_totale !== undefined &&
        voce.media_importo_totale !== null
          ? roundNumber(voce.media_importo_totale)
          : null,
      deltaPercentuale:
        voce.delta_percentuale !== undefined && voce.delta_percentuale !== null
          ? roundNumber(voce.delta_percentuale, 1)
          : null,
      deltaAssoluto:
        voce.delta_assoluto !== undefined && voce.delta_assoluto !== null
          ? roundNumber(voce.delta_assoluto)
          : null,
      offerteConsiderate: voce.offerte_considerate ?? 0,
      importoMinimo:
        voce.importo_minimo !== undefined && voce.importo_minimo !== null
          ? roundNumber(voce.importo_minimo)
          : null,
      importoMassimo:
        voce.importo_massimo !== undefined && voce.importo_massimo !== null
          ? roundNumber(voce.importo_massimo)
          : null,
      impresaMin: voce.impresa_min ?? null,
      impresaMax: voce.impresa_max ?? null,
      deviazioneStandard:
        voce.deviazione_standard !== undefined && voce.deviazione_standard !== null
          ? roundNumber(voce.deviazione_standard)
          : null,
      criticita: voce.criticita ?? null,
      direzione: voce.direzione ?? null,
    })),
  };
}

function roundNumber(value: number, decimals = 2): number {
  const factor = 10 ** decimals;
  return Math.round((value ?? 0) * factor) / factor;
}
