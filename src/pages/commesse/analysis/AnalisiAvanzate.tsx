import { useMemo, useState, type ReactNode } from "react";
import { useParams } from "react-router-dom";
import { Loader2, TrendingUp, Grid3x3, GitCompare } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { useAnalisiData } from "@/hooks/useAnalisiData";
import { useTrendEvoluzioneData } from "@/hooks/useTrendEvoluzioneData";
import { useHeatmapData } from "@/hooks/useHeatmapData";
import { TrendEvoluzioneRound } from "@/components/charts/TrendEvoluzioneRound";
import { HeatmapCompetitivita } from "@/components/charts/HeatmapCompetitivita";
import { OverlayBarChart, type OverlaySeries } from "@/components/charts/OverlayBarChart";

type ChartCardProps = {
  title: string;
  description: string;
  isLoading: boolean;
  hasData: boolean;
  emptyMessage: string;
  children: ReactNode;
};

const ChartCard = ({ title, description, isLoading, hasData, emptyMessage, children }: ChartCardProps) => (
  <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
    <CardHeader>
      <CardTitle>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <div className="flex h-96 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : hasData ? (
        children
      ) : (
        <div className="flex h-96 items-center justify-center text-muted-foreground">{emptyMessage}</div>
      )}
    </CardContent>
  </Card>
);

type WaterfallScenarioId = "media" | "minCategoria" | "maxCategoria" | "migliorOfferta";

type WaterfallScenarioDataset = {
  id: WaterfallScenarioId;
  label: string;
  description: string;
  offertaLabel?: string;
  data: {
    categoria: string;
    importoProgetto: number;
    importoOfferta: number;
    delta: number;
    deltaPercentuale?: number;
  }[];
  importoProgettoTotale: number;
  importoOffertaTotale: number;
};

const WATERFALL_SCENARIOS: { id: WaterfallScenarioId; label: string; description: string }[] = [
  {
    id: "media",
    label: "Media round",
    description: "Confronto vs media dei ritorni del round",
  },
  {
    id: "minCategoria",
    label: "Prezzi minimi per categoria",
    description: "Per ogni WBS usa il prezzo più basso del round",
  },
  {
    id: "maxCategoria",
    label: "Prezzi massimi per categoria",
    description: "Per ogni WBS usa il prezzo più alto del round",
  },
  {
    id: "migliorOfferta",
    label: "Miglior offerta",
    description: "Offerta complessiva più bassa del round",
  },
];

const SERIES_COLORS: Record<"progetto" | WaterfallScenarioId, string> = {
  progetto: "#3b82f6", // blue
  maxCategoria: "#ef4444", // red
  media: "#94a3b8", // gray
  minCategoria: "#22c55e", // green
  migliorOfferta: "#f59e0b", // yellow/orange
};

const getImpresaOption = (impresa: unknown) => {
  if (typeof impresa === "string") {
    return { key: impresa, label: impresa };
  }
  if (impresa && typeof impresa === "object") {
    const obj = impresa as Record<string, unknown>;
    const key = (obj.key ?? obj.nome ?? obj.label ?? "") as string;
    const label = (obj.label ?? obj.nome ?? obj.key ?? "Impresa") as string;
    return { key: key || label, label };
  }
  return { key: "impresa", label: "Impresa" };
};

export default function AnalisiAvanzate() {
  const { id } = useParams();
  const { commessa } = useCommessaContext();
  const commessaId = id ?? (commessa ? String(commessa.id) : undefined);

  const [selectedRound, setSelectedRound] = useState<"all" | number>("all");
  const [selectedImpresa, setSelectedImpresa] = useState<"all" | string>("all");
  const [includeProject, setIncludeProject] = useState(true);
  const [activeWaterfallScenarios, setActiveWaterfallScenarios] = useState<WaterfallScenarioId[]>([
    "media",
    "minCategoria",
    "maxCategoria",
    "migliorOfferta",
  ]);

  const toggleWaterfallScenario = (scenarioId: WaterfallScenarioId) => {
    setActiveWaterfallScenarios((prev) => {
      const isActive = prev.includes(scenarioId);
      if (isActive) {
        const remaining = prev.filter((id) => id !== scenarioId);
        return remaining.length === 0 ? prev : remaining;
      }
      return [...prev, scenarioId];
    });
  };

  const activeFiltersAnalisi = useMemo(
    () => ({
      round: selectedRound === "all" ? null : selectedRound,
      impresa: selectedImpresa === "all" ? null : selectedImpresa,
    }),
    [selectedRound, selectedImpresa],
  );

  const activeFiltersTrend = useMemo(
    () => ({
      impresa: selectedImpresa === "all" ? null : selectedImpresa,
    }),
    [selectedImpresa],
  );

  const activeFiltersHeatmap = useMemo(
    () => ({
      round: selectedRound === "all" ? null : selectedRound,
    }),
    [selectedRound],
  );

  const { data: analisiData, isLoading: isLoadingAnalisi } = useAnalisiData(commessaId || "", activeFiltersAnalisi);
  const { data: trendData, isLoading: isLoadingTrend } = useTrendEvoluzioneData(commessaId || "", activeFiltersTrend);
  const { data: heatmapData, isLoading: isLoadingHeatmap } = useHeatmapData(commessaId || "", activeFiltersHeatmap);

  const waterfallScenarioData = useMemo(() => {
    const scenarioMap: Partial<Record<WaterfallScenarioId, WaterfallScenarioDataset>> = {};

    if (analisiData?.analisiPerWbs6?.length) {
      const dataMedia = analisiData.analisiPerWbs6.map((wbs) => {
        const progetto = wbs.progetto ?? 0;
        const media = wbs.media ?? 0;
        return {
          categoria: wbs.wbs6Label || wbs.wbs6Code || "Categoria",
          importoProgetto: progetto,
          importoOfferta: media,
          delta: media - progetto,
          deltaPercentuale: wbs.delta ?? undefined,
        };
      });

      scenarioMap.media = {
        id: "media",
        label: "Media round",
        description: "Confronto vs media dei ritorni del round",
        data: dataMedia,
        importoProgettoTotale: dataMedia.reduce((sum, item) => sum + (item.importoProgetto || 0), 0),
        importoOffertaTotale: dataMedia.reduce((sum, item) => sum + (item.importoOfferta || 0), 0),
        offertaLabel: "Media round",
      };
    }

    const categorieHeatmap = heatmapData?.data?.categorie ?? [];
    const impreseHeatmap = heatmapData?.data?.imprese ?? [];
    const hasHeatmap = categorieHeatmap.length > 0 && impreseHeatmap.length > 0;

    if (hasHeatmap) {
      const baseProgettoTotale = categorieHeatmap.reduce((sum, cat) => sum + (cat.importoProgetto || 0), 0);

      const dataMinCategoria = categorieHeatmap.map((cat) => {
        const minVal = impreseHeatmap.reduce((min, imp) => {
          const match = imp.categorie.find((c) => c.categoria === cat.categoria);
          if (match && typeof match.importoOfferta === "number") {
            return Math.min(min, match.importoOfferta);
          }
          return min;
        }, Number.POSITIVE_INFINITY);

        const offerta = minVal !== Number.POSITIVE_INFINITY ? minVal : cat.importoProgetto ?? 0;
        const progetto = cat.importoProgetto ?? 0;
        return {
          categoria: cat.categoria,
          importoProgetto: progetto,
          importoOfferta: offerta,
          delta: offerta - progetto,
        };
      });

      scenarioMap.minCategoria = {
        id: "minCategoria",
        label: "Prezzi minimi per categoria",
        description: "Per ogni WBS usa il prezzo più basso del round",
        data: dataMinCategoria,
        importoProgettoTotale: baseProgettoTotale,
        importoOffertaTotale: dataMinCategoria.reduce((sum, item) => sum + (item.importoOfferta || 0), 0),
        offertaLabel: "Prezzo minimo per categoria",
      };

      const dataMaxCategoria = categorieHeatmap.map((cat) => {
        const maxVal = impreseHeatmap.reduce((max, imp) => {
          const match = imp.categorie.find((c) => c.categoria === cat.categoria);
          if (match && typeof match.importoOfferta === "number") {
            return Math.max(max, match.importoOfferta);
          }
          return max;
        }, Number.NEGATIVE_INFINITY);

        const offerta = maxVal !== Number.NEGATIVE_INFINITY ? maxVal : cat.importoProgetto ?? 0;
        const progetto = cat.importoProgetto ?? 0;
        return {
          categoria: cat.categoria,
          importoProgetto: progetto,
          importoOfferta: offerta,
          delta: offerta - progetto,
        };
      });

      scenarioMap.maxCategoria = {
        id: "maxCategoria",
        label: "Prezzi massimi per categoria",
        description: "Per ogni WBS usa il prezzo più alto del round",
        data: dataMaxCategoria,
        importoProgettoTotale: baseProgettoTotale,
        importoOffertaTotale: dataMaxCategoria.reduce((sum, item) => sum + (item.importoOfferta || 0), 0),
        offertaLabel: "Prezzo massimo per categoria",
      };

      const impresaTotals = impreseHeatmap.map((imp) => {
        const categorieMap = new Map<string, number>();
        imp.categorie.forEach((cat) => {
          categorieMap.set(cat.categoria, cat.importoOfferta);
        });
        const totale = categorieHeatmap.reduce((sum, cat) => sum + (categorieMap.get(cat.categoria) ?? 0), 0);
        return { impresa: imp.impresa, totale, categorieMap };
      });

      const bestImpresa = impresaTotals.sort((a, b) => a.totale - b.totale)[0];

      if (bestImpresa) {
        const dataBest = categorieHeatmap.map((cat) => {
          const offerta = bestImpresa.categorieMap.get(cat.categoria);
          const progetto = cat.importoProgetto ?? 0;
          return {
            categoria: cat.categoria,
            importoProgetto: progetto,
            importoOfferta: offerta ?? progetto,
            delta: (offerta ?? progetto) - progetto,
          };
        });

        scenarioMap.migliorOfferta = {
          id: "migliorOfferta",
          label: "Miglior offerta",
          description: "Offerta complessiva più bassa del round",
          data: dataBest,
          importoProgettoTotale: baseProgettoTotale,
          importoOffertaTotale: bestImpresa.totale,
          offertaLabel: `Miglior offerta (${bestImpresa.impresa})`,
        };
      }
    }

    return scenarioMap;
  }, [analisiData, heatmapData]);

  const selectedWaterfallCharts = useMemo(() => {
    return activeWaterfallScenarios
      .map((id) => {
        const dataset = waterfallScenarioData[id];
        if (!dataset) return null;
        const meta = WATERFALL_SCENARIOS.find((option) => option.id === id);
        return {
          ...dataset,
          label: meta?.label ?? dataset.label,
          description: meta?.description ?? dataset.description,
        };
      })
      .filter(Boolean) as WaterfallScenarioDataset[];
  }, [activeWaterfallScenarios, waterfallScenarioData]);

  const hasRounds = (analisiData?.rounds.length || 0) > 1;
  const hasMultipleImprese = (analisiData?.imprese.length || 0) > 1;
  const hasTrendData = Boolean(trendData?.data?.length);
  const hasHeatmapDataAvailable = (heatmapData?.data?.categorie?.length || 0) > 0 && (heatmapData?.data?.imprese?.length || 0) > 0;
  const needsHeatmapForWaterfall = activeWaterfallScenarios.some((id) => id !== "media");
  const isLoadingWaterfall = isLoadingAnalisi || (needsHeatmapForWaterfall ? isLoadingHeatmap : false);

  const [overlayMode, setOverlayMode] = useState<"grouped" | "overlay">("grouped");
  const [overlayScale, setOverlayScale] = useState<"linear" | "log">("linear");

  const overlayBarData = useMemo(() => {
    const categories = new Map<string, Record<string, string | number | null>>();
    const series: OverlaySeries[] = [];

    // Mappa scenari selezionati per accesso rapido
    const scenarioById = new Map<WaterfallScenarioId, WaterfallScenarioDataset>();
    selectedWaterfallCharts.forEach((scenario) => {
      scenarioById.set(scenario.id, scenario);
    });

    // Baseline progetto se attivo
    if (includeProject && analisiData?.analisiPerWbs6?.length) {
      analisiData.analisiPerWbs6.forEach((wbs) => {
        const key = wbs.wbs6Label || wbs.wbs6Code || wbs.wbs6Id;
        if (!categories.has(key)) categories.set(key, { categoria: key });
        const bucket = categories.get(key)!;
        bucket.progetto = wbs.progetto ?? 0;
      });
    }

    // Dati scenari attivi
    selectedWaterfallCharts.forEach((scenario) => {
      scenario.data.forEach((item) => {
        const key = item.categoria;
        if (!categories.has(key)) categories.set(key, { categoria: key });
        const bucket = categories.get(key)!;
        bucket[scenario.id] = item.importoOfferta;
      });
    });

    const desiredOrder: ("progetto" | WaterfallScenarioId)[] = [
      "progetto",
      "maxCategoria",
      "media",
      "minCategoria",
      "migliorOfferta",
    ];

    desiredOrder.forEach((id) => {
      if (id === "progetto") {
        if (includeProject) {
          series.push({ id: "progetto", label: "Progetto", color: SERIES_COLORS.progetto });
        }
        return;
      }
      const scenario = scenarioById.get(id);
      if (!scenario) return;
      series.push({
        id: scenario.id,
        label: scenario.offertaLabel ?? scenario.label,
        color: SERIES_COLORS[id],
      });
    });

    if (series.length === 0) return null;

    return {
      data: Array.from(categories.values()),
      series,
    };
  }, [analisiData?.analisiPerWbs6, includeProject, selectedWaterfallCharts]);

  if (!commessaId) {
    return null;
  }

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Analisi Avanzate"
        description="Grafici avanzati per analisi dettagliate delle offerte"
        backHref={`/commesse/${commessaId}/analisi`}
      />

      <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
        <CardHeader className="px-4 pb-0 pt-4">
          <CardTitle className="text-base font-semibold">Filtri</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">Filtra i dati per round e impresa</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 px-4 pb-4 sm:flex-row">
          {hasRounds && (
            <div className="flex-1">
              <label className="mb-2 block text-sm font-medium">Round</label>
              <Select value={String(selectedRound)} onValueChange={(val) => setSelectedRound(val === "all" ? "all" : Number(val))}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona round" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i round</SelectItem>
                  {analisiData?.rounds.map((round) => (
                    <SelectItem key={round.numero} value={String(round.numero)}>
                      {round.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {hasMultipleImprese && (
            <div className="flex-1">
              <label className="mb-2 block text-sm font-medium">Impresa</label>
              <Select value={String(selectedImpresa)} onValueChange={(val) => setSelectedImpresa(val === "all" ? "all" : val)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona impresa" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le imprese</SelectItem>
                  {(analisiData?.imprese ?? []).map((impresa) => {
                    const option = getImpresaOption(impresa);
                    return (
                      <SelectItem key={option.key} value={option.key}>
                        {option.label}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="waterfall" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="waterfall" className="gap-2 text-sm">
            <GitCompare className="h-4 w-4" />
            Waterfall
          </TabsTrigger>
          <TabsTrigger value="trend" className="gap-2 text-sm">
            <TrendingUp className="h-4 w-4" />
            Trend Round
          </TabsTrigger>
          <TabsTrigger value="heatmap" className="gap-2 text-sm">
            <Grid3x3 className="h-4 w-4" />
            Heatmap
          </TabsTrigger>
        </TabsList>

        <TabsContent value="waterfall" className="space-y-3">
          <Card className="border border-border/60 bg-card/60 shadow-sm">
            <CardContent className="flex flex-col gap-3 p-4">
              <div className="flex flex-col gap-1">
                <p className="text-sm font-semibold">Riferimento confronto</p>
                <p className="text-xs text-muted-foreground">Scegli uno o più scenari: vengono mostrati affiancati per confronto diretto.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant={includeProject ? "default" : "outline"}
                  size="sm"
                  onClick={() => setIncludeProject((prev) => !prev)}
                  className={`h-8 ${includeProject ? "font-semibold shadow-sm" : ""}`}
                >
                  Progetto
                </Button>
                {WATERFALL_SCENARIOS.map((scenario) => {
                  const isActive = activeWaterfallScenarios.includes(scenario.id);
                  return (
                    <Button
                      key={scenario.id}
                      variant={isActive ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleWaterfallScenario(scenario.id)}
                      className={`h-8 ${isActive ? "font-semibold shadow-sm" : ""}`}
                    >
                      {scenario.label}
                    </Button>
                  );
                })}

                {overlayBarData && overlayBarData.series.length > 1 && (
                  <div className="ml-auto flex flex-wrap items-center gap-2">
                    <span className="text-xs text-muted-foreground">Visualizzazione</span>
                    <div className="flex gap-1 rounded-md border border-border/60 p-1">
                      <Button
                        variant={overlayMode === "grouped" ? "secondary" : "ghost"}
                        size="xs"
                        className="h-7 px-2 text-xs"
                        onClick={() => setOverlayMode("grouped")}
                      >
                        Affiancate
                      </Button>
                      <Button
                        variant={overlayMode === "overlay" ? "secondary" : "ghost"}
                        size="xs"
                        className="h-7 px-2 text-xs"
                        onClick={() => setOverlayMode("overlay")}
                      >
                        Sovrapposte
                      </Button>
                    </div>
                    <span className="text-xs text-muted-foreground">Scala</span>
                    <div className="flex gap-1 rounded-md border border-border/60 p-1">
                      <Button
                        variant={overlayScale === "linear" ? "secondary" : "ghost"}
                        size="xs"
                        className="h-7 px-2 text-xs"
                        onClick={() => setOverlayScale("linear")}
                      >
                        Lineare
                      </Button>
                      <Button
                        variant={overlayScale === "log" ? "secondary" : "ghost"}
                        size="xs"
                        className="h-7 px-2 text-xs"
                        onClick={() => setOverlayScale("log")}
                      >
                        Log
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {overlayBarData && overlayBarData.data.length > 0 && overlayBarData.series.length > 1 ? (
            <Card className="border border-border/60 bg-card shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Overlay categorie WBS6</CardTitle>
                <CardDescription>Confronto diretto degli importi per categoria sugli scenari selezionati</CardDescription>
              </CardHeader>
              <CardContent className="px-2 sm:px-4">
                <OverlayBarChart
                  data={overlayBarData.data}
                  series={overlayBarData.series}
                  mode={overlayMode}
                  xTickFormatter={(value) => (value?.length > 24 ? `${value.slice(0, 24)}…` : value)}
                  scale={overlayScale}
                  barSize={overlayMode === "overlay" ? 14 : 18}
                  height={540}
                />
              </CardContent>
            </Card>
          ) : isLoadingWaterfall ? (
            <div className="flex h-80 items-center justify-center rounded-lg border border-border/60 bg-card">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="rounded-lg border border-border/60 bg-card/50 p-6 text-sm text-muted-foreground">
              Nessun dato disponibile per gli scenari selezionati. Prova a cambiare round o selezionare un altro scenario.
            </div>
          )}
        </TabsContent>

        <TabsContent value="trend" className="space-y-3">
          <ChartCard
            title="Evoluzione Prezzi tra Round"
            description="Andamento delle offerte delle imprese attraverso i round di gara"
            isLoading={isLoadingTrend}
            hasData={hasTrendData}
            emptyMessage={hasRounds ? "Nessun dato disponibile per il trend" : "Sono necessari almeno 2 round per visualizzare il trend"}
          >
            {hasTrendData && trendData && <TrendEvoluzioneRound data={trendData.data} />}
          </ChartCard>
        </TabsContent>

        <TabsContent value="heatmap" className="space-y-3">
          <ChartCard
            title="Matrice Competitività Imprese"
            description="Confronto delle performance delle imprese per categoria WBS6"
            isLoading={isLoadingHeatmap}
            hasData={hasHeatmapDataAvailable}
            emptyMessage="Nessun dato disponibile per la heatmap"
          >
            {hasHeatmapDataAvailable && heatmapData?.data && (
              <HeatmapCompetitivita categorie={heatmapData.data.categorie} imprese={heatmapData.data.imprese} />
            )}
          </ChartCard>
        </TabsContent>
      </Tabs>
    </div>
  );
}
