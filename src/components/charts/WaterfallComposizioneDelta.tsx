import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
  TooltipProps,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingDown, TrendingUp } from "lucide-react";
import { InfoTooltip } from "@/components/ui/info-tooltip";

interface WaterfallItem {
  categoria: string;
  importoProgetto: number;
  importoOfferta: number;
  delta: number; // Differenza assoluta (offerta - progetto)
  deltaPercentuale?: number;
}

interface WaterfallComposizioneDeltaProps {
  data: WaterfallItem[];
  importoProgettoTotale: number;
  importoOffertaTotale: number;
  offertaLabel?: string;
}

interface WaterfallChartData {
  name: string;
  value: number;
  start: number;
  end: number;
  color: string;
  isTotal?: boolean;
  delta?: number;
}

const formatEuro = (value: number): string => {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `€${(value / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 1_000) {
    return `€${(value / 1_000).toFixed(0)}k`;
  }
  return `€${value.toLocaleString("it-IT")}`;
};

const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload as WaterfallChartData;

  if (data.isTotal) {
    return (
      <div className="bg-card border rounded-lg p-4 shadow-lg min-w-[220px]">
        <p className="font-semibold mb-2">{data.name}</p>
        <p className="text-lg font-bold text-primary">{formatEuro(data.end)}</p>
      </div>
    );
  }

  return (
    <div className="bg-card border rounded-lg p-4 shadow-lg min-w-[260px]">
      <p className="font-semibold mb-3">{data.name}</p>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-muted-foreground">Contributo:</span>
          <span className="font-mono font-semibold">{formatEuro(data.value)}</span>
        </div>
        {typeof data.delta === "number" && (
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Delta vs progetto:</span>
            <span className={`font-mono font-semibold ${data.delta < 0 ? "text-green-600" : "text-destructive"}`}>
              {data.delta > 0 ? "+" : ""}
              {formatEuro(data.delta)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export function WaterfallComposizioneDelta({
  data,
  importoProgettoTotale,
  importoOffertaTotale,
  offertaLabel = "Offerta di riferimento",
}: WaterfallComposizioneDeltaProps) {
  const waterfallData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const chartData: WaterfallChartData[] = [];
    let runningTotal = importoProgettoTotale;

    chartData.push({
      name: "Importo Progetto",
      value: importoProgettoTotale,
      start: 0,
      end: importoProgettoTotale,
      color: "hsl(var(--muted-foreground))",
      isTotal: true,
    });

    const sortedData = [...data].sort((a, b) => a.delta - b.delta);

    sortedData.forEach((item) => {
      const start = runningTotal;
      const end = start + item.delta;
      runningTotal = end;

      chartData.push({
        name: item.categoria,
        value: item.delta,
        start: Math.min(start, end),
        end: Math.max(start, end),
        color: item.delta < 0 ? "hsl(142 71% 45%)" : "hsl(0 84% 60%)",
        delta: item.delta,
      });
    });

    chartData.push({
      name: offertaLabel,
      value: importoOffertaTotale,
      start: 0,
      end: importoOffertaTotale,
      color: "hsl(var(--primary))",
      isTotal: true,
    });

    return chartData;
  }, [data, importoProgettoTotale, importoOffertaTotale, offertaLabel]);

  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    const risparmi = data.filter((d) => d.delta < 0);
    const extraCosti = data.filter((d) => d.delta > 0);

    const totaleRisparmi = risparmi.reduce((sum, d) => sum + Math.abs(d.delta), 0);
    const totaleExtraCosti = extraCosti.reduce((sum, d) => sum + d.delta, 0);
    const deltaComplessivo = importoOffertaTotale - importoProgettoTotale;
    const deltaAssolutoTotale = Math.abs(deltaComplessivo);

    return {
      risparmi: {
        count: risparmi.length,
        totale: totaleRisparmi,
        top: risparmi.sort((a, b) => a.delta - b.delta).slice(0, 3),
      },
      extraCosti: {
        count: extraCosti.length,
        totale: totaleExtraCosti,
        top: extraCosti.sort((a, b) => b.delta - a.delta).slice(0, 3),
      },
      deltaComplessivo,
      quotaRisparmiSuDelta: deltaAssolutoTotale > 0 ? (totaleRisparmi / deltaAssolutoTotale) * 100 : 0,
    };
  }, [data, importoProgettoTotale, importoOffertaTotale]);

  if (!data || data.length === 0 || !stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Composizione Delta Progetto vs Offerta
            <InfoTooltip content="Mostra come si compone il delta totale tra progetto e l'offerta di riferimento, categoria per categoria." />
          </CardTitle>
          <CardDescription>Analisi dettagliata delle variazioni per categoria WBS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">Dati insufficienti per mostrare la composizione del delta.</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Composizione Delta Progetto vs {offertaLabel}
          <InfoTooltip content="Grafico waterfall che mostra come ogni categoria WBS contribuisce al delta totale. Le barre verdi indicano risparmi, le rosse extra-costi." />
        </CardTitle>
        <CardDescription>Scomposizione del delta tra importo progetto e riferimento selezionato</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg border bg-muted/30">
            <p className="text-xs text-muted-foreground mb-1">Importo Progetto</p>
            <p className="text-2xl font-bold text-muted-foreground">{formatEuro(importoProgettoTotale)}</p>
          </div>

          <div className="p-4 rounded-lg border bg-primary/5 border-primary/20">
            <p className="text-xs text-muted-foreground mb-1">{offertaLabel}</p>
            <p className="text-2xl font-bold text-primary">{formatEuro(importoOffertaTotale)}</p>
          </div>

          <div
            className={`p-4 rounded-lg border ${
              stats.deltaComplessivo < 0 ? "bg-green-50 border-green-200 dark:bg-green-950/20" : "bg-destructive/5 border-destructive/20"
            }`}
          >
            <p className="text-xs text-muted-foreground mb-1">Delta Totale</p>
            <div className="flex items-center gap-2">
              {stats.deltaComplessivo < 0 ? <TrendingDown className="h-5 w-5 text-green-600" /> : <TrendingUp className="h-5 w-5 text-destructive" />}
              <div>
                <p className={`text-2xl font-bold ${stats.deltaComplessivo < 0 ? "text-green-600" : "text-destructive"}`}>
                  {formatEuro(stats.deltaComplessivo)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={450}>
          <BarChart data={waterfallData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="name"
              className="text-xs"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
              angle={-35}
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis className="text-xs" tick={{ fill: "hsl(var(--muted-foreground))" }} tickFormatter={formatEuro} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="3 3" />
            <Bar dataKey="end" radius={[4, 4, 0, 0]}>
              {waterfallData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-lg border bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-900">
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="h-5 w-5 text-green-600" />
              <h4 className="font-semibold text-green-900 dark:text-green-100">Categorie con Risparmio</h4>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-green-200 dark:border-green-900">
                <span className="text-sm font-medium">Totale risparmi:</span>
                <span className="font-bold text-green-600 text-lg">{formatEuro(-stats.risparmi.totale)}</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">{stats.risparmi.count} categorie con prezzi inferiori al progetto</p>
              {stats.risparmi.top.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium truncate flex-1 pr-2">{item.categoria}</span>
                    <span className="font-mono font-semibold text-green-600">{formatEuro(item.delta)}</span>
                  </div>
                  {idx < stats.risparmi.top.length - 1 && <div className="h-px bg-green-200 dark:bg-green-900 my-2" />}
                </div>
              ))}
            </div>
          </div>

          <div className="p-5 rounded-lg border bg-destructive/5 border-destructive/20">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-5 w-5 text-destructive" />
              <h4 className="font-semibold text-destructive">Categorie con Extra-costo</h4>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-destructive/20">
                <span className="text-sm font-medium">Totale extra-costi:</span>
                <span className="font-bold text-destructive text-lg">{formatEuro(stats.extraCosti.totale)}</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">{stats.extraCosti.count} categorie con prezzi superiori al progetto</p>
              {stats.extraCosti.top.length > 0 ? (
                stats.extraCosti.top.map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium truncate flex-1 pr-2">{item.categoria}</span>
                      <span className="font-mono font-semibold text-destructive">{formatEuro(item.delta)}</span>
                    </div>
                    {idx < stats.extraCosti.top.length - 1 && <div className="h-px bg-destructive/20 my-2" />}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">Nessun extra-costo rilevato</p>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 bg-muted/30 rounded-lg border border-border">
          <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">🌟 Insights Chiave</h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            <li>• Ripartizione delta: risparmi {formatEuro(-stats.risparmi.totale)} vs extra-costi {formatEuro(stats.extraCosti.totale)}</li>
            {stats.risparmi.top.length > 0 && (
              <li>
                • Maggiore risparmio: <span className="font-semibold text-green-600">{stats.risparmi.top[0].categoria}</span> ({formatEuro(stats.risparmi.top[0].delta)})
              </li>
            )}
            {stats.extraCosti.top.length > 0 && (
              <li>
                • Maggiore extra-costo: <span className="font-semibold text-destructive">{stats.extraCosti.top[0].categoria}</span> ({formatEuro(stats.extraCosti.top[0].delta)})
              </li>
            )}
            <li className="pt-2 border-t mt-2">• Concentra le negoziazioni sulle categorie rosse per massimizzare i risparmi</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
