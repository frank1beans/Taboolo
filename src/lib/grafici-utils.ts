/**
 * Utilità per trasformare i dati dell'analisi nei formati richiesti dai nuovi grafici
 */

// Tipo base per i dati di analisi (da useAnalisiData)
export interface AnalisiData {
  confrontoImporti: {
    impresa: string;
    importo: number;
    delta: number;
    colore: string;
  }[];
  analisiPerWbs6: {
    wbs6Id: string;
    wbs6Label: string;
    wbs6Code?: string;
    wbs6Description?: string;
    progetto: number;
    media: number;
    delta: number;
    deltaAssoluto: number;
  }[];
  rounds: {
    numero: number;
    label?: string;
  }[];
  imprese: {
    nome: string;
    label?: string;
    normalized?: string;
  }[];
}

// Dati per il trend evoluzione
export interface TrendEvoluzioneData {
  impresa: string;
  color: string;
  offerte: {
    round: number;
    roundLabel?: string;
    importo: number;
    delta?: number;
  }[];
  deltaComplessivo?: number;
}

// Dati per waterfall
export interface WaterfallData {
  categoria: string;
  importoProgetto: number;
  importoOfferta: number;
  delta: number;
  deltaPercentuale: number;
}

// Dati per heatmap
export interface HeatmapData {
  categorie: {
    categoria: string;
    importoProgetto: number;
  }[];
  imprese: {
    impresa: string;
    categorie: {
      categoria: string;
      importoOfferta: number;
      delta: number;
    }[];
  }[];
}

/**
 * Prepara i dati per il grafico Trend Evoluzione Prezzi tra Round
 * Nota: Questa funzione richiede dati dettagliati per round che potrebbero
 * non essere disponibili nell'hook attuale. Potrebbe essere necessario
 * creare un hook specifico o estendere l'API.
 */
export function prepareTrendEvoluzioneData(
  confrontoImportiPerRound: {
    round: number;
    roundLabel?: string;
    offerte: {
      impresa: string;
      importo: number;
      color: string;
    }[];
  }[]
): TrendEvoluzioneData[] {
  if (!confrontoImportiPerRound || confrontoImportiPerRound.length === 0) {
    return [];
  }

  // Raccoglie tutte le imprese uniche
  const impreseMap = new Map<string, { color: string; offerte: any[] }>();

  confrontoImportiPerRound.forEach((roundData) => {
    roundData.offerte.forEach((offerta) => {
      if (!impreseMap.has(offerta.impresa)) {
        impreseMap.set(offerta.impresa, {
          color: offerta.color,
          offerte: [],
        });
      }

      const impresaData = impreseMap.get(offerta.impresa)!;
      const prevOfferta =
        impresaData.offerte.length > 0
          ? impresaData.offerte[impresaData.offerte.length - 1]
          : null;

      const delta = prevOfferta
        ? ((offerta.importo - prevOfferta.importo) / prevOfferta.importo) * 100
        : 0;

      impresaData.offerte.push({
        round: roundData.round,
        roundLabel: roundData.roundLabel || `Round ${roundData.round}`,
        importo: offerta.importo,
        delta,
      });
    });
  });

  // Converte in array
  return Array.from(impreseMap.entries()).map(([impresa, data]) => {
    const offerte = data.offerte.sort((a, b) => a.round - b.round);
    const deltaComplessivo =
      offerte.length > 1
        ? ((offerte[offerte.length - 1].importo - offerte[0].importo) /
            offerte[0].importo) *
          100
        : 0;

    return {
      impresa,
      color: data.color,
      offerte,
      deltaComplessivo,
    };
  });
}

/**
 * Prepara i dati per il Waterfall Chart
 */
export function prepareWaterfallData(
  analisiPerWbs6: AnalisiData["analisiPerWbs6"],
  importoProgettoTotale: number,
  importoOffertaTotale: number
): {
  data: WaterfallData[];
  importoProgettoTotale: number;
  importoOffertaTotale: number;
} {
  if (!analisiPerWbs6 || analisiPerWbs6.length === 0) {
    return {
      data: [],
      importoProgettoTotale: 0,
      importoOffertaTotale: 0,
    };
  }

  const data: WaterfallData[] = analisiPerWbs6.map((wbs) => ({
    categoria: wbs.wbs6Label || wbs.wbs6Code || "N/A",
    importoProgetto: wbs.progetto,
    importoOfferta: wbs.media,
    delta: wbs.deltaAssoluto,
    deltaPercentuale: wbs.delta,
  }));

  return {
    data,
    importoProgettoTotale,
    importoOffertaTotale,
  };
}

/**
 * Prepara i dati per la Heatmap Competitività
 * Nota: Richiede dati dettagliati per impresa/categoria che potrebbero
 * non essere disponibili. Potrebbe essere necessario estendere l'API.
 */
export function prepareHeatmapData(
  analisiPerWbs6PerImpresa: {
    impresa: string;
    wbs6: {
      wbs6Id: string;
      wbs6Label: string;
      progetto: number;
      offerta: number;
      delta: number;
    }[];
  }[]
): HeatmapData {
  if (
    !analisiPerWbs6PerImpresa ||
    analisiPerWbs6PerImpresa.length === 0
  ) {
    return { categorie: [], imprese: [] };
  }

  // Raccoglie tutte le categorie uniche
  const categorieMap = new Map<
    string,
    { categoria: string; importoProgetto: number }
  >();

  analisiPerWbs6PerImpresa.forEach((impresa) => {
    impresa.wbs6.forEach((cat) => {
      if (!categorieMap.has(cat.wbs6Id)) {
        categorieMap.set(cat.wbs6Id, {
          categoria: cat.wbs6Label,
          importoProgetto: cat.progetto,
        });
      }
    });
  });

  const categorie = Array.from(categorieMap.values());

  // Prepara i dati per impresa
  const imprese = analisiPerWbs6PerImpresa.map((imp) => ({
    impresa: imp.impresa,
    categorie: imp.wbs6.map((cat) => ({
      categoria: cat.wbs6Label,
      importoOfferta: cat.offerta,
      delta: cat.delta,
    })),
  }));

  return { categorie, imprese };
}

/**
 * Genera dati di esempio per il Trend Evoluzione
 * Usare solo per demo/testing
 */
export function generateMockTrendData(
  imprese: string[],
  numRounds: number = 3
): TrendEvoluzioneData[] {
  const colors = [
    "hsl(217 91% 60%)",
    "hsl(142 71% 45%)",
    "hsl(38 92% 55%)",
    "hsl(0 84% 60%)",
    "hsl(260 80% 65%)",
  ];

  return imprese.map((impresa, idx) => {
    const baseImporto = 1000000 + Math.random() * 500000;
    const offerte = [];

    for (let round = 1; round <= numRounds; round++) {
      const reduction = round === 1 ? 0 : Math.random() * 0.1; // 0-10% riduzione
      const importo = baseImporto * (1 - reduction * (round - 1));
      const prevImporto = round > 1 ? offerte[round - 2].importo : baseImporto;
      const delta = ((importo - prevImporto) / prevImporto) * 100;

      offerte.push({
        round,
        roundLabel: `Round ${round}`,
        importo,
        delta,
      });
    }

    const deltaComplessivo =
      ((offerte[offerte.length - 1].importo - offerte[0].importo) /
        offerte[0].importo) *
      100;

    return {
      impresa,
      color: colors[idx % colors.length],
      offerte,
      deltaComplessivo,
    };
  });
}
