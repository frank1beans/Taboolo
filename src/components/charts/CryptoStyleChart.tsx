import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
  Bar,
  BarChart,
  ComposedChart,
  Line,
} from "recharts";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface CryptoStyleChartProps {
  data: Array<{
    label: string;
    progetto: number;
    media: number;
    wbs6Id?: string;
    delta?: number;
  }>;
  height?: number;
  showGrid?: boolean;
  onBarClick?: (wbs6Id: string) => void;
}

const formatCurrency = (value: number): string => {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `€${Math.round(value / 1000)}k`;
  return `€${value.toLocaleString("it-IT")}`;
};

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null;

  const progetto = payload.find((p) => p.dataKey === "progetto")?.value || 0;
  const media = payload.find((p) => p.dataKey === "media")?.value || 0;
  const delta = progetto !== 0 ? ((media - progetto) / progetto) * 100 : 0;
  const isPositive = delta > 0;

  return (
    <div className="crypto-tooltip">
      <div className="backdrop-blur-xl bg-black/80 border border-white/10 rounded-2xl p-4 shadow-2xl min-w-[260px]">
        <p className="text-white font-semibold mb-3 text-sm tracking-wide">{label}</p>

        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-slate-400 to-slate-500" />
              <span className="text-slate-300 text-xs font-medium">Progetto</span>
            </div>
            <span className="text-white font-mono font-semibold text-sm">
              {formatCurrency(Number(progetto))}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
              <span className="text-slate-300 text-xs font-medium">Media offerte</span>
            </div>
            <span className="text-white font-mono font-semibold text-sm">
              {formatCurrency(Number(media))}
            </span>
          </div>

          <div className="pt-2 mt-2 border-t border-white/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                {isPositive ? (
                  <TrendingUp className="h-3.5 w-3.5 text-red-400" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5 text-emerald-400" />
                )}
                <span className="text-slate-300 text-xs font-medium">Delta</span>
              </div>
              <span
                className={`font-mono font-bold text-sm ${
                  isPositive ? "text-red-400" : "text-emerald-400"
                }`}
              >
                {isPositive ? "+" : ""}
                {delta.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export function CryptoStyleChart({
  data,
  height = 450,
  showGrid = true,
  onBarClick,
}: CryptoStyleChartProps) {
  const chartData = useMemo(() => data, [data]);

  return (
    <div className="relative w-full">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 rounded-2xl blur-3xl -z-10 animate-pulse" />

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={chartData}
          margin={{ top: 80, right: 30, left: 10, bottom: 80 }}
        >
          <defs>
            {/* Gradient per il progetto */}
            <linearGradient id="progettoGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#94a3b8" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#94a3b8" stopOpacity={0.1} />
            </linearGradient>

            {/* Gradient animato per media offerte */}
            <linearGradient id="mediaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.9} />
              <stop offset="50%" stopColor="#a855f7" stopOpacity={0.6} />
              <stop offset="100%" stopColor="#ec4899" stopOpacity={0.1} />
            </linearGradient>

            {/* Glow effect per le barre */}
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.05)"
              vertical={false}
            />
          )}

          <XAxis
            dataKey="label"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            tickLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            interval={0}
            angle={-35}
            textAnchor="end"
            height={100}
          />

          <YAxis
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            tickLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            tickFormatter={formatCurrency}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255, 255, 255, 0.02)" }} />

          {/* Area chart per progetto con gradiente */}
          <Area
            type="monotone"
            dataKey="progetto"
            stroke="#94a3b8"
            strokeWidth={2}
            fill="url(#progettoGradient)"
            fillOpacity={0.4}
            animationDuration={1500}
            animationBegin={0}
          />

          {/* Barre per media offerte con gradiente neon */}
          <Bar
            dataKey="media"
            fill="url(#mediaGradient)"
            radius={[8, 8, 0, 0]}
            animationDuration={1500}
            animationBegin={300}
            cursor="pointer"
            onClick={(data: any) => {
              if (onBarClick && data.wbs6Id) {
                onBarClick(data.wbs6Id);
              }
            }}
            style={{ filter: "url(#glow)" }}
          />

          {/* Linea di trend */}
          <Line
            type="monotone"
            dataKey="media"
            stroke="url(#mediaGradient)"
            strokeWidth={3}
            dot={{
              fill: "#fff",
              stroke: "#a855f7",
              strokeWidth: 2,
              r: 5,
            }}
            activeDot={{
              fill: "#ec4899",
              stroke: "#fff",
              strokeWidth: 3,
              r: 7,
            }}
            animationDuration={2000}
            animationBegin={600}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend personalizzata con stile crypto */}
      <div className="flex items-center justify-center gap-6 mt-6 px-4">
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-slate-500/10 to-slate-600/10 border border-slate-400/20">
          <div className="w-3 h-3 rounded-full bg-gradient-to-r from-slate-400 to-slate-500" />
          <span className="text-xs font-medium text-slate-300">Progetto</span>
        </div>

        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 border border-purple-400/20">
          <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse" />
          <span className="text-xs font-medium bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent font-semibold">
            Media Offerte
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
          <Activity className="h-3 w-3 text-primary animate-pulse" />
          <span className="text-xs font-medium text-primary">Live</span>
        </div>
      </div>
    </div>
  );
}
