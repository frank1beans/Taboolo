import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, TrendingUp, Grid3x3, GitCompare } from "lucide-react";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { useAnalisiData } from "@/hooks/useAnalisiData";
import { useTrendEvoluzioneData } from "@/hooks/useTrendEvoluzioneData";
import { useHeatmapData } from "@/hooks/useHeatmapData";
import { prepareWaterfallData } from "@/lib/grafici-utils";
import { WaterfallComposizioneDelta } from "@/components/charts/WaterfallComposizioneDelta";
import { TrendEvoluzioneRound } from "@/components/charts/TrendEvoluzioneRound";
import { HeatmapCompetitivita } from "@/components/charts/HeatmapCompetitivita";

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

  const waterfallData = useMemo(() => {
    if (!analisiData) return null;

    const progetto = analisiData.confrontoImporti.find((i) => i.tipo === "progetto")?.importo || 0;
    const ritorni = analisiData.confrontoImporti
      .filter((i) => i.tipo === "ritorno")
      .map((i) => i.importo);

    // Offerta migliore = la più bassa tra tutti i ritorni
    const offertaMigliore = ritorni.length > 0 ? Math.min(...ritorni) : 0;

    return prepareWaterfallData(analisiData.analisiPerWbs6, progetto, offertaMigliore);
  }, [analisiData]);

  const hasRounds = (analisiData?.rounds.length || 0) > 1;
  const hasMultipleImprese = (analisiData?.imprese.length || 0) > 1;

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
          <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
            <CardHeader>
              <CardTitle>Composizione Delta per Categoria</CardTitle>
              <CardDescription>Visualizza come si compone il delta totale tra progetto e offerta migliore</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingAnalisi ? (
                <div className="flex h-96 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : waterfallData && waterfallData.data.length > 0 ? (
                <WaterfallComposizioneDelta
                  data={waterfallData.data}
                  importoProgettoTotale={waterfallData.importoProgettoTotale}
                  importoOffertaTotale={waterfallData.importoOffertaTotale}
                />
              ) : (
                <div className="flex h-96 items-center justify-center text-muted-foreground">
                  Nessun dato disponibile per il waterfall chart
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trend" className="space-y-3">
          <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
            <CardHeader>
              <CardTitle>Evoluzione Prezzi tra Round</CardTitle>
              <CardDescription>Andamento delle offerte delle imprese attraverso i round di gara</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingTrend ? (
                <div className="flex h-96 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : trendData && trendData.data.length > 0 ? (
                <TrendEvoluzioneRound data={trendData.data} />
              ) : (
                <div className="flex h-96 items-center justify-center text-muted-foreground">
                  {hasRounds ? "Nessun dato disponibile per il trend" : "Sono necessari almeno 2 round per visualizzare il trend"}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="heatmap" className="space-y-3">
          <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
            <CardHeader>
              <CardTitle>Matrice Competitività Imprese</CardTitle>
              <CardDescription>Confronto delle performance delle imprese per categoria WBS6</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingHeatmap ? (
                <div className="flex h-96 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : heatmapData && heatmapData.data ? (
                <HeatmapCompetitivita categorie={heatmapData.data.categorie} imprese={heatmapData.data.imprese} />
              ) : (
                <div className="flex h-96 items-center justify-center text-muted-foreground">
                  Nessun dato disponibile per la heatmap
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
