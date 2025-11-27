import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { InfoTooltip } from "@/components/ui/info-tooltip";

interface OffertaRound {
  round: number;
  roundLabel?: string;
  importo: number;
  delta?: number; // Delta rispetto al round precedente
}

interface ImpresaTrend {
  impresa: string;
  color: string;
  offerte: OffertaRound[];
  deltaComplessivo?: number; // Delta dal primo all'ultimo round
}

interface TrendEvoluzioneRoundProps {
  data: ImpresaTrend[];
}

const formatEuro = (value: number): string => {
  if (value >= 1_000_000) {
    return `€${(value / 1_000_000).toFixed(2)}M`;
  }
  if (value >= 1_000) {
    return `€${(value / 1_000).toFixed(0)}k`;
  }
  return `€${value.toLocaleString("it-IT")}`;
};

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-card border rounded-lg p-4 shadow-lg min-w-[280px]">
      <p className="font-semibold mb-3 text-base">{label}</p>
      <div className="space-y-2">
        {payload
          .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0))
          .map((entry, index) => {
            const impresaData = entry.payload as any;
            const deltaRound = impresaData[`${entry.dataKey}_delta`];

            return (
              <div key={index} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2 flex-1">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm font-medium truncate">{entry.name}</span>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-semibold">
                    {formatEuro(Number(entry.value))}
                  </p>
                  {typeof deltaRound === "number" && deltaRound !== 0 && (
                    <p className={`text-xs font-medium ${deltaRound < 0 ? "text-green-600" : "text-destructive"}`}>
                      {deltaRound > 0 ? "+" : ""}{deltaRound.toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
};

export function TrendEvoluzioneRound({ data }: TrendEvoluzioneRoundProps) {
  // Prepara i dati per il grafico
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Trova tutti i round unici
    const allRounds = new Set<number>();
    data.forEach((impresa) => {
      impresa.offerte.forEach((offerta) => {
        allRounds.add(offerta.round);
      });
    });

    const rounds = Array.from(allRounds).sort((a, b) => a - b);

    // Crea un array di oggetti, uno per ogni round
    return rounds.map((roundNum) => {
      const roundData: any = {
        round: `Round ${roundNum}`,
        roundNum,
      };

      data.forEach((impresa) => {
        const offerta = impresa.offerte.find((o) => o.round === roundNum);
        if (offerta) {
          roundData[impresa.impresa] = offerta.importo;
          roundData[`${impresa.impresa}_delta`] = offerta.delta || 0;
        }
      });

      return roundData;
    });
  }, [data]);

  // Calcola statistiche di tendenza
  const trendStats = useMemo(() => {
    return data.map((impresa) => {
      const offerte = [...impresa.offerte].sort((a, b) => a.round - b.round);
      if (offerte.length < 2) {
        return {
          impresa: impresa.impresa,
          color: impresa.color,
          trend: "stable" as const,
          deltaComplessivo: 0,
        };
      }

      const primo = offerte[0].importo;
      const ultimo = offerte[offerte.length - 1].importo;
      const delta = ((ultimo - primo) / primo) * 100;

      return {
        impresa: impresa.impresa,
        color: impresa.color,
        trend: delta < -2 ? ("down" as const) : delta > 2 ? ("up" as const) : ("stable" as const),
        deltaComplessivo: delta,
      };
    });
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Evoluzione Prezzi tra Round
            <InfoTooltip content="Mostra come cambiano le offerte delle imprese tra i diversi round di gara. Utile per identificare chi migliora l'offerta e chi rimane stabile." />
          </CardTitle>
          <CardDescription>
            Analisi dell'andamento temporale delle offerte
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            Dati insufficienti per mostrare l'evoluzione tra round.
            <br />
            <span className="text-sm">Sono necessari almeno 2 round con offerte.</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              Evoluzione Prezzi tra Round
              <InfoTooltip content="Mostra come cambiano le offerte delle imprese tra i diversi round di gara. Le linee in discesa indicano riduzioni di prezzo (positivo), quelle in salita indicano aumenti (da verificare)." />
            </CardTitle>
            <CardDescription>
              Andamento temporale delle offerte e dinamiche di negoziazione
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Grafico */}
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="round"
              className="text-sm"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis
              className="text-sm"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={formatEuro}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: "20px" }}
              iconType="line"
            />
            {data.map((impresa) => (
              <Line
                key={impresa.impresa}
                type="monotone"
                dataKey={impresa.impresa}
                name={impresa.impresa}
                stroke={impresa.color}
                strokeWidth={3}
                dot={{ r: 5, strokeWidth: 2, fill: "white" }}
                activeDot={{ r: 7 }}
                connectNulls={true}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trendStats.map((stat) => {
            const TrendIcon =
              stat.trend === "down"
                ? TrendingDown
                : stat.trend === "up"
                ? TrendingUp
                : Minus;
            const trendColor =
              stat.trend === "down"
                ? "text-green-600"
                : stat.trend === "up"
                ? "text-destructive"
                : "text-muted-foreground";
            const bgColor =
              stat.trend === "down"
                ? "bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-900"
                : stat.trend === "up"
                ? "bg-destructive/5 border-destructive/20"
                : "bg-muted/50 border-border";

            return (
              <div
                key={stat.impresa}
                className={`p-4 rounded-lg border ${bgColor} transition-all hover:shadow-md`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-1">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: stat.color }}
                    />
                    <p className="font-medium text-sm truncate" title={stat.impresa}>
                      {stat.impresa}
                    </p>
                  </div>
                  <TrendIcon className={`h-5 w-5 flex-shrink-0 ${trendColor}`} />
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Variazione complessiva</p>
                  <p className={`text-2xl font-bold ${trendColor}`}>
                    {stat.deltaComplessivo > 0 ? "+" : ""}
                    {stat.deltaComplessivo.toFixed(1)}%
                  </p>
                  <Badge
                    variant={
                      stat.trend === "down"
                        ? "default"
                        : stat.trend === "up"
                        ? "destructive"
                        : "secondary"
                    }
                    className={stat.trend === "down" ? "bg-green-600" : ""}
                  >
                    {stat.trend === "down"
                      ? "In miglioramento"
                      : stat.trend === "up"
                      ? "In aumento"
                      : "Stabile"}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>

        {/* Insights */}
        <div className="p-4 bg-muted/30 rounded-lg border border-border">
          <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
            💡 Insights
          </h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            {trendStats.some((s) => s.trend === "down") && (
              <li>
                • Imprese in miglioramento:{" "}
                <span className="font-medium text-green-600">
                  {trendStats
                    .filter((s) => s.trend === "down")
                    .map((s) => s.impresa)
                    .join(", ")}
                </span>
                {" "}(opportunità di negoziazione)
              </li>
            )}
            {trendStats.some((s) => s.trend === "up") && (
              <li>
                • Imprese con aumenti:{" "}
                <span className="font-medium text-destructive">
                  {trendStats
                    .filter((s) => s.trend === "up")
                    .map((s) => s.impresa)
                    .join(", ")}
                </span>
                {" "}(da verificare)
              </li>
            )}
            {trendStats.some((s) => s.trend === "stable") && (
              <li>
                • Imprese stabili:{" "}
                <span className="font-medium text-foreground">
                  {trendStats
                    .filter((s) => s.trend === "stable")
                    .map((s) => s.impresa)
                    .join(", ")}
                </span>
              </li>
            )}
            <li className="pt-2 border-t border-border mt-2">
              • Migliore negoziatore:{" "}
              <span className="font-semibold text-green-600">
                {trendStats.reduce((best, current) =>
                  current.deltaComplessivo < best.deltaComplessivo ? current : best
                ).impresa}
              </span>
              {" "}(
              {trendStats
                .reduce((best, current) =>
                  current.deltaComplessivo < best.deltaComplessivo ? current : best
                )
                .deltaComplessivo.toFixed(1)}
              % di riduzione)
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
