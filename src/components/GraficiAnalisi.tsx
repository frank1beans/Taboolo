import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  TooltipProps,
} from "recharts";
import { TrendingUp, TrendingDown, AlertTriangle, Loader2, ChevronRight, BarChart3, PieChartIcon } from "lucide-react";
import { useAnalisiWbs6Dettaglio, useAnalisiData } from "@/hooks/useAnalisiData";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { formatCurrency, formatCurrencyCompact } from "@/lib/formatters";

const normalizeImpresaValue = (value: string | null | undefined): string | null =>
  value
    ? value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-zA-Z0-9]+/g, "")
        .toLowerCase()
    : null;

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-border rounded p-4 shadow-sm">
        <p className="font-bold text-sm uppercase tracking-wider mb-2">{label}</p>
        <div className="space-y-1">
          {payload.map((entry, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-sm">
              <span className="font-light" style={{ color: entry.color }}>
                {entry.name}
              </span>
              <span className="font-mono font-medium">{formatCurrency(Number(entry.value))}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

const renderWbsTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null;
  const progetto = Number(payload.find((item) => item.dataKey === "progetto")?.value) || 0;
  const media = Number(payload.find((item) => item.dataKey === "media")?.value) || 0;
  const delta = progetto !== 0 ? ((media - progetto) / progetto) * 100 : 0;
  return (
    <div className="bg-card border border-border rounded p-4 shadow-sm min-w-[240px]">
      <p className="font-bold text-sm uppercase tracking-wider mb-3">{label}</p>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-light text-muted-foreground">Progetto</span>
          <span className="font-mono font-medium text-sm">{formatCurrency(progetto)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-light text-muted-foreground">Media offerte</span>
          <span className="font-mono font-medium text-sm">{formatCurrency(media)}</span>
        </div>
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <span className="text-xs font-bold uppercase tracking-wider">Delta</span>
          <span className={`font-mono font-bold text-sm ${delta > 0 ? "text-destructive" : "text-green-600"}`}>
            {delta > 0 ? "+" : ""}
            {delta.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
};

interface GraficiAnalisiProps {
  commessaId: string;
  selectedRound?: "all" | number;
  onSelectedRoundChange?: (round: "all" | number) => void;
  selectedImpresa?: "all" | string;
  onSelectedImpresaChange?: (impresa: "all" | string) => void;
}

export function GraficiAnalisi({
  commessaId,
  selectedRound: controlledRound,
  onSelectedRoundChange,
  selectedImpresa: controlledImpresa,
  onSelectedImpresaChange,
}: GraficiAnalisiProps) {
  const isRoundControlled = controlledRound !== undefined;
  const [selectedRoundState, setSelectedRoundState] = useState<"all" | number>("all");
  const selectedRound = isRoundControlled ? (controlledRound ?? "all") : selectedRoundState;

  const isImpresaControlled = controlledImpresa !== undefined;
  const [selectedImpresaState, setSelectedImpresaState] = useState<"all" | string>("all");
  const selectedImpresa = isImpresaControlled
    ? (controlledImpresa ?? "all")
    : selectedImpresaState;

  const handleRoundChange = useCallback(
    (value: "all" | number) => {
      if (!isRoundControlled) {
        setSelectedRoundState(value);
      }
      onSelectedRoundChange?.(value);
    },
    [isRoundControlled, onSelectedRoundChange],
  );

  const handleImpresaChange = useCallback(
    (value: "all" | string) => {
      if (!isImpresaControlled) {
        setSelectedImpresaState(value);
      }
      onSelectedImpresaChange?.(value);
    },
    [isImpresaControlled, onSelectedImpresaChange],
  );
  const [selectedWbs6, setSelectedWbs6] = useState<string | null>(null);
  const [roundOptions, setRoundOptions] = useState<
    { value: number; label: string }[]
  >([]);

  const activeFilters = useMemo(
    () => ({
      round: selectedRound === "all" ? null : selectedRound,
      impresa: selectedImpresa === "all" ? null : selectedImpresa,
    }),
    [selectedRound, selectedImpresa],
  );
  const { data, isLoading } = useAnalisiData(commessaId, activeFilters);
  const { data: wbs6Dettaglio, isFetching: isWbs6Fetching } =
    useAnalisiWbs6Dettaglio(commessaId, selectedWbs6, activeFilters);

  const impreseDisponibili = data?.imprese ?? [];

  useEffect(() => {
    if (!data?.rounds) {
      return;
    }
    setRoundOptions((prev) => {
      const map = new Map(prev.map((round) => [round.value, round]));
      data.rounds.forEach((round) => {
        const value = round.numero;
        const label = round.label ?? `Round ${round.numero}`;
        map.set(value, { value, label });
      });
      return Array.from(map.values()).sort((a, b) => a.value - b.value);
    });
  }, [data?.rounds]);

  // Use refs to avoid infinite loops with callback dependencies
  const handleRoundChangeRef = useRef(handleRoundChange);
  const handleImpresaChangeRef = useRef(handleImpresaChange);
  
  useEffect(() => {
    handleRoundChangeRef.current = handleRoundChange;
    handleImpresaChangeRef.current = handleImpresaChange;
  }, [handleRoundChange, handleImpresaChange]);

  useEffect(() => {
    if (selectedRound === "all") return;
    if (!roundOptions.some((option) => option.value === selectedRound)) {
      handleRoundChangeRef.current("all");
    }
  }, [roundOptions, selectedRound]);

  const impresaOptions = useMemo(() => {
    const seen = new Map<string, string>();
    impreseDisponibili.forEach((impresa) => {
      const value = impresa.normalized ?? impresa.label ?? impresa.nome;
      const label = impresa.label ?? impresa.nome;
      if (!seen.has(value)) {
        seen.set(value, label);
      }
    });
    return Array.from(seen.entries())
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label, "it-IT"));
  }, [impreseDisponibili]);

  useEffect(() => {
    if (selectedImpresa === "all") return;
    if (!impresaOptions.some((option) => option.value === selectedImpresa)) {
      handleImpresaChangeRef.current("all");
    }
  }, [impresaOptions, selectedImpresa]);

  const hasActiveFilter = selectedRound !== "all" || selectedImpresa !== "all";
  const hasAnalisi = Boolean(data);

  const analisiData = data ?? {
    confrontoImporti: [],
    distribuzioneVariazioni: [],
    vociCritiche: [],
    analisiPerWbs6: [],
    rounds: [],
    imprese: [],
    filtri: {
      roundNumber: null,
      impresa: null,
      impresaNormalizzata: null,
      offerteTotali: 0,
      offerteConsiderate: 0,
      impreseAttive: [],
    },
  };

  const {
    confrontoImporti,
    distribuzioneVariazioni,
    vociCritiche,
    analisiPerWbs6,
    filtri: filtriAnalisi,
  } = analisiData;

  const normalizedSelectedImpresa = useMemo(
    () => (selectedImpresa === "all" ? null : normalizeImpresaValue(selectedImpresa)),
    [selectedImpresa],
  );

  const confrontoImportiFiltrati = useMemo(() => {
    if (!confrontoImporti || confrontoImporti.length === 0) return [];
    return confrontoImporti.filter((item) => {
      const roundMatch =
        selectedRound === "all" ||
        item.tipo === "progetto" ||
        item.roundNumber === selectedRound;
      if (!roundMatch) {
        return false;
      }

      if (!normalizedSelectedImpresa) {
        return true;
      }

      const candidates = [
        item.impresaNormalized,
        item.impresaOriginale ? normalizeImpresaValue(item.impresaOriginale) : null,
        normalizeImpresaValue(item.impresa),
      ].filter(Boolean);

      return candidates.some((value) => value === normalizedSelectedImpresa);
    });
  }, [confrontoImporti, normalizedSelectedImpresa, selectedRound]);

  useEffect(() => {
    if (
      selectedWbs6 &&
      !analisiPerWbs6.some((item) => item.wbs6Id === selectedWbs6)
    ) {
      setSelectedWbs6(null);
    }
  }, [selectedWbs6, analisiPerWbs6]);

  const formatWbs6Label = (cat: (typeof analisiPerWbs6)[number]) => {
    const parts = [cat.wbs6Code, cat.wbs6Description].filter((part) => part && part.trim().length > 0);
    return parts.length ? parts.join(" - ") : cat.wbs6Label;
  };

  const wbsChartSeries = [
    { key: "progetto", label: "Progetto", color: "#94a3b8" },
    { key: "media", label: "Media offerte", color: "hsl(var(--primary))" },
  ] as const;

  const wbs6ChartData = useMemo(
    () =>
      analisiPerWbs6.map((cat) => ({
        ...cat,
        label: formatWbs6Label(cat),
        progetto: cat.progetto ?? 0,
        media: cat.media ?? 0,
      })),
    [analisiPerWbs6, formatWbs6Label],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!hasAnalisi) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Impossibile caricare i dati di analisi.
      </div>
    );
  }

  const totaleVociCritiche = vociCritiche.filter((v) => v.criticita === "alta").length;
  const totaleVociMedie = vociCritiche.filter((v) => v.criticita === "media").length;
  const totaleVociOk = vociCritiche.filter((v) => v.criticita === "bassa").length;

  const handleWbs6Click = (wbs6Id: string) => {
    setSelectedWbs6(wbs6Id);
  };

  return (
    <div className="space-y-6">
      {/* Filtri */}
      <div className="flex flex-wrap items-center justify-end gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase text-muted-foreground">Round</span>
          <Select
            value={selectedRound === "all" ? "all" : String(selectedRound)}
            onValueChange={(value) =>
              handleRoundChange(value === "all" ? "all" : Number(value))
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Tutti i round" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti i round</SelectItem>
              {roundOptions.map((round) => (
                <SelectItem key={round.value} value={String(round.value)}>
                  {round.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs uppercase text-muted-foreground">Impresa</span>
          <Select
            value={selectedImpresa === "all" ? "all" : selectedImpresa}
            onValueChange={(value) =>
              handleImpresaChange(value === "all" ? "all" : value)
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Tutte le imprese" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le imprese</SelectItem>
              {impresaOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {hasActiveFilter && (filtriAnalisi?.offerteConsiderate ?? 0) === 0 && (
        <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
          Nessuna offerta corrisponde ai filtri selezionati.
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="ghost" className="p-6">
          <CardHeader className="p-0 pb-3">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Voci Critiche
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-light text-destructive">{totaleVociCritiche}</p>
              <TrendingUp className="h-5 w-5 text-destructive" />
            </div>
            <p className="text-xs font-light text-muted-foreground mt-2">
              Voci con criticità alta
            </p>
          </CardContent>
        </Card>

        <Card variant="ghost" className="p-6">
          <CardHeader className="p-0 pb-3">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Voci Medie
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-light text-orange-500">{totaleVociMedie}</p>
              <AlertTriangle className="h-5 w-5 text-orange-500" />
            </div>
            <p className="text-xs font-light text-muted-foreground mt-2">
              Voci con criticità media
            </p>
          </CardContent>
        </Card>

        <Card variant="ghost" className="p-6">
          <CardHeader className="p-0 pb-3">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Voci OK
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-light text-green-600">{totaleVociOk}</p>
              <TrendingDown className="h-5 w-5 text-green-600" />
            </div>
            <p className="text-xs font-light text-muted-foreground mt-2">
              Voci con criticità bassa
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grafico Confronto Importi Totali */}
        <Card variant="ghost" className="p-6">
          <CardHeader>
            <CardTitle>Confronto Importi Totali</CardTitle>
            <CardDescription>
              Analisi comparativa degli importi offerti dalle imprese
            </CardDescription>
          </CardHeader>
          <CardContent>
            {confrontoImportiFiltrati.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={confrontoImportiFiltrati}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />
                    <XAxis 
                      dataKey="impresa" 
                      className="text-sm font-light"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 13 }}
                    />
                    <YAxis 
                      className="text-sm font-light"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 13 }}
                      tickFormatter={(value) => `€${(value / 1000000).toFixed(1)}M`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="importo" radius={[4, 4, 0, 0]}>
                      {confrontoImportiFiltrati.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.colore} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-6 flex items-center justify-center gap-6 flex-wrap">
                  {confrontoImportiFiltrati.map((item) => (
                    <div key={item.impresa} className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: item.colore }} />
                      <span className="text-sm font-light text-muted-foreground">{item.impresa}</span>
                      {item.delta !== 0 && (
                        <Badge 
                          variant="outline"
                          className={cn(
                            "font-mono text-xs",
                            item.delta > 0 ? "text-destructive border-destructive/30" : "text-green-600 border-green-600/30"
                          )}
                        >
                          {item.delta > 0 ? "+" : ""}{item.delta}%
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-16 text-sm font-light text-muted-foreground">
                Nessun dato disponibile
              </div>
            )}
          </CardContent>
        </Card>

        {/* Grafico Distribuzione Variazioni */}
        <Card variant="ghost" className="p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="text-base font-bold uppercase tracking-wider">Distribuzione Variazioni</CardTitle>
            <CardDescription className="text-sm font-light">
              Numero di voci per scostamento rispetto alla media
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {(() => {
              const totaleVoci = distribuzioneVariazioni.map(item => item.valore).reduce((a, b) => a + b, 0);
              return distribuzioneVariazioni.length > 0 && totaleVoci > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={360}>
                    <PieChart>
                      <Pie
                        data={distribuzioneVariazioni}
                        cx="50%"
                        cy="50%"
                        labelLine={true}
                        label={({ nome, valore, percent }) => 
                          `${nome}: ${valore} (${(percent * 100).toFixed(1)}%)`
                        }
                        outerRadius={120}
                        innerRadius={70}
                        fill="#8884d8"
                        dataKey="valore"
                        paddingAngle={3}
                      >
                        {distribuzioneVariazioni.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.colore} />
                        ))}
                      </Pie>
                      <Tooltip 
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload;
                            const percentuale = ((data.valore / totaleVoci) * 100).toFixed(1);
                            return (
                              <div className="bg-card border border-border rounded p-4 shadow-sm">
                                <p className="font-bold text-sm uppercase tracking-wider mb-2">{data.nome}</p>
                                <p className="text-sm font-light">{data.valore} voci ({percentuale}%)</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="mt-6 grid grid-cols-2 gap-4">
                    {distribuzioneVariazioni.map((item) => {
                      const percentuale = ((item.valore / totaleVoci) * 100).toFixed(1);
                      return (
                        <div key={item.nome} className="flex items-center justify-between p-4 rounded border border-border bg-card/50">
                          <div className="flex items-center gap-3">
                            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: item.colore }} />
                            <span className="text-sm font-light">{item.nome}</span>
                          </div>
                          <div className="text-right">
                            <p className="text-xl font-light">{item.valore}</p>
                            <p className="text-xs font-light text-muted-foreground">{percentuale}%</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : (
                <div className="text-center py-16 text-sm font-light text-muted-foreground">
                  Dati insufficienti per la distribuzione
                </div>
              );
            })()}
          </CardContent>
        </Card>
      </div>


      {/* Andamento per WBS6 */}
      <Card variant="ghost" className="p-6">
        <CardHeader className="p-0 pb-4">
          <CardTitle className="text-base font-bold uppercase tracking-wider">Andamento per WBS6</CardTitle>
          <CardDescription className="text-sm font-light">
            Confronto importi progetto vs media offerte per macro-categoria WBS6 (visualizzazione affiancata)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {wbs6ChartData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={wbs6ChartData}
                  margin={{ top: 72, right: 16, left: 0, bottom: 72 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
                  <XAxis
                    dataKey="label"
                    className="text-xs"
                    interval={0}
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                    angle={-35}
                    textAnchor="end"
                    height={90}
                  />
                  <YAxis
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                    tickFormatter={(value) => formatCurrencyCompact(Number(value))}
                  />
                  <Tooltip content={renderWbsTooltip} />
                  <Legend
                    verticalAlign="top"
                    align="right"
                    wrapperStyle={{ top: 12 }}
                  />
                  {wbsChartSeries.map((serie) => (
                    <Bar
                      key={serie.key}
                      dataKey={serie.key}
                      name={serie.label}
                      fill={serie.color}
                      radius={[4, 4, 0, 0]}
                      cursor="pointer"
                      onClick={(data: { wbs6Id: string }) => handleWbs6Click(data.wbs6Id)}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>

              <div className="mt-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {analisiPerWbs6.map((cat) => {
                  const isPositive = cat.delta > 0;
                  const deltaAssoluto = cat.deltaAssoluto;
                  const categoriaLabel = formatWbs6Label(cat);
                  return (
                    <div
                      key={cat.wbs6Id}
                      className="p-3 rounded-lg border bg-card hover:shadow-md transition-shadow cursor-pointer hover:border-primary"
                      onClick={() => handleWbs6Click(cat.wbs6Id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p
                          className="text-xs font-medium text-muted-foreground truncate flex-1"
                          title={categoriaLabel}
                        >
                          {categoriaLabel}
                        </p>
                        <ChevronRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Progetto:</span>
                          <span className="font-mono">€{(cat.progetto / 1000).toFixed(0)}k</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Media:</span>
                          <span className="font-mono">€{(cat.media / 1000).toFixed(0)}k</span>
                        </div>
                        <div className="flex items-center justify-center gap-1 pt-1 border-t">
                          {isPositive ? (
                            <TrendingUp className="h-3 w-3 text-destructive" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-green-600" />
                          )}
                          <span
                            className={`text-sm font-bold ${
                              isPositive ? "text-destructive" : "text-green-600"
                            }`}
                          >
                            {isPositive ? "+" : ""}{cat.delta.toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-xs text-center text-muted-foreground">
                          {isPositive ? '+' : ''}€{(deltaAssoluto / 1000).toFixed(0)}k
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              Dati per WBS6 non disponibili
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Voci Critiche e Vantaggiose */}
      {vociCritiche.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top 10 Voci Critiche */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-destructive" />
                Top 10 Voci Critiche
              </CardTitle>
              <CardDescription>
                Voci con maggior incremento rispetto alla media
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(() => {
                const topCritiche = [...vociCritiche]
                  .filter(v => v.deltaPercentuale && v.deltaPercentuale > 0)
                  .sort((a, b) => (b.deltaPercentuale || 0) - (a.deltaPercentuale || 0))
                  .slice(0, 10);

                return topCritiche.length > 0 ? (
                  <div className="space-y-3">
                    {topCritiche.map((voce, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground truncate flex-1 pr-2">
                            {voce.descrizione || voce.codice || `Voce ${idx + 1}`}
                          </span>
                          <Badge variant="destructive">
                            +{voce.deltaPercentuale?.toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Progetto: €{voce.prezzoUnitarioProgetto?.toFixed(2)}</span>
                          <span>•</span>
                          <span>Media: €{voce.mediaPrezzoUnitario?.toFixed(2)}</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-destructive/70 to-destructive"
                            style={{ width: `${Math.min(((voce.deltaPercentuale || 0) / Math.max(...topCritiche.map(v => v.deltaPercentuale || 0))) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    Nessuna voce con delta positivo
                  </div>
                );
              })()}
            </CardContent>
          </Card>

          {/* Top 10 Voci Vantaggiose */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-green-600" />
                Top 10 Voci Vantaggiose
              </CardTitle>
              <CardDescription>
                Voci con maggior risparmio rispetto alla media
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(() => {
                const topVantaggiose = [...vociCritiche]
                  .filter(v => v.deltaPercentuale && v.deltaPercentuale < 0)
                  .sort((a, b) => (a.deltaPercentuale || 0) - (b.deltaPercentuale || 0))
                  .slice(0, 10);

                return topVantaggiose.length > 0 ? (
                  <div className="space-y-3">
                    {topVantaggiose.map((voce, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground truncate flex-1 pr-2">
                            {voce.descrizione || voce.codice || `Voce ${idx + 1}`}
                          </span>
                          <Badge className="bg-green-600">
                            {voce.deltaPercentuale?.toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Progetto: €{voce.prezzoUnitarioProgetto?.toFixed(2)}</span>
                          <span>•</span>
                          <span>Media: €{voce.mediaPrezzoUnitario?.toFixed(2)}</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-green-600/70 to-green-600"
                            style={{ width: `${Math.min((Math.abs(voce.deltaPercentuale || 0) / Math.max(...topVantaggiose.map(v => Math.abs(v.deltaPercentuale || 0)))) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    Nessuna voce con delta negativo
                  </div>
                );
              })()}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dialog for WBS6 details */}
      <Dialog
        open={selectedWbs6 !== null}
        onOpenChange={(open) => !open && setSelectedWbs6(null)}
      >
        <DialogContent className="max-w-5xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Dettaglio WBS6: {
                analisiPerWbs6.find((c) => c.wbs6Id === selectedWbs6)
                  ?.wbs6Label ?? selectedWbs6
              }
            </DialogTitle>
            <DialogDescription>
              Voci di computo presenti in questa WBS6
            </DialogDescription>
          </DialogHeader>

          {selectedWbs6 && (() => {
            const fallbackWbs6 = analisiPerWbs6.find(
              (c) => c.wbs6Id === selectedWbs6,
            );
            const categoriaData = wbs6Dettaglio ?? fallbackWbs6;

            if (!categoriaData) {
              if (isWbs6Fetching) {
                return (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span className="ml-2 text-sm">Caricamento dettagli WBS6…</span>
                  </div>
                );
              }
              return (
                <div className="text-center py-8 text-muted-foreground">
                  Categoria WBS6 non trovata.
                </div>
              );
            }

            const voci = categoriaData.voci ?? [];
            const categoriaLabel = categoriaData.wbs6Label ?? selectedWbs6;

            return (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
                  <div>
                    <p className="text-xs text-muted-foreground">Importo Progetto</p>
                    <p className="text-lg font-bold">€{categoriaData.progetto.toLocaleString('it-IT')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Media Offerte</p>
                    <p className="text-lg font-bold text-primary">€{categoriaData.media.toLocaleString('it-IT')}</p>
                  </div>
                  <div className="flex flex-col items-start">
                    <p className="text-xs text-muted-foreground">Delta</p>
                    <p className={`text-lg font-bold ${categoriaData.delta > 0 ? 'text-destructive' : 'text-green-600'}`}>
                      {categoriaData.delta > 0 ? '+' : ''}{categoriaData.delta.toFixed(1)}%
                    </p>
                    {isWbs6Fetching && (
                      <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span>Aggiornamento in corso…</span>
                      </div>
                    )}
                  </div>
                </div>

                {voci.length > 0 ? (
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[120px]">Codice</TableHead>
                          <TableHead>Descrizione</TableHead>
                          <TableHead className="w-[80px]">U.M.</TableHead>
                          <TableHead className="w-[100px] text-right">Quantità</TableHead>
                          <TableHead className="w-[120px] text-right">P.U. Progetto</TableHead>
                          <TableHead className="w-[120px] text-right">Media P.U.</TableHead>
                          <TableHead className="w-[100px] text-right">Delta %</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {voci.map((voce, idx) => {
                          const deltaPercent = voce.deltaPercentuale;
                          const hasDelta = typeof deltaPercent === "number";
                          const badgeVariant = !hasDelta
                            ? "secondary"
                            : Math.abs(deltaPercent) > 50
                            ? "destructive"
                            : Math.abs(deltaPercent) > 10
                            ? "default"
                            : "secondary";
                          const badgeClass = !hasDelta
                            ? ""
                            : Math.abs(deltaPercent) > 10 && Math.abs(deltaPercent) <= 50
                            ? "bg-orange-600"
                            : deltaPercent < -10
                            ? "bg-green-600"
                            : "";

                          return (
                            <TableRow key={`${categoriaLabel}-${idx}`}>
                              <TableCell className="font-mono text-xs">{voce.codice ?? "—"}</TableCell>
                              <TableCell className="text-sm">{voce.descrizione ?? "—"}</TableCell>
                              <TableCell className="text-xs">{voce.unitaMisura ?? "—"}</TableCell>
                              <TableCell className="text-right font-mono text-sm">
                                {typeof voce.quantita === "number"
                                  ? voce.quantita.toLocaleString('it-IT', { minimumFractionDigits: 2 })
                                  : "—"}
                              </TableCell>
                              <TableCell className="text-right font-mono text-sm">
                                {typeof voce.prezzoUnitarioProgetto === "number"
                                  ? `€${voce.prezzoUnitarioProgetto.toLocaleString('it-IT', { minimumFractionDigits: 2 })}`
                                  : "—"}
                              </TableCell>
                              <TableCell className="text-right font-mono text-sm">
                                {typeof voce.mediaPrezzoUnitario === "number"
                                  ? `€${voce.mediaPrezzoUnitario.toLocaleString('it-IT', { minimumFractionDigits: 2 })}`
                                  : "—"}
                              </TableCell>
                              <TableCell className="text-right">
                                <Badge variant={badgeVariant} className={badgeClass}>
                                  {hasDelta
                                    ? `${deltaPercent! > 0 ? "+" : ""}${deltaPercent!.toFixed(1)}%`
                                    : "—"}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Nessuna voce trovata per questa categoria
                  </div>
                )}
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}
