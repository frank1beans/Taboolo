import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export type OverlaySeries = {
  id: string;
  label: string;
  color: string;
};

interface OverlayBarChartProps {
  data: Array<Record<string, string | number | null>>;
  series: OverlaySeries[];
  height?: number;
  xKey?: string;
  valueFormatter?: (value: number) => string;
  xTickFormatter?: (value: string) => string;
  mode?: "overlay" | "grouped";
  barSize?: number;
  overlayOpacity?: number;
  scale?: "linear" | "log";
  logMin?: number;
  maxPadding?: number;
  overlayGapPx?: number;
}

const defaultFormat = (value: number) =>
  typeof value === "number" ? value.toLocaleString("it-IT") : "";

export function OverlayBarChart({
  data,
  series,
  height = 500,
  xKey = "categoria",
  valueFormatter = defaultFormat,
  xTickFormatter,
  mode = "grouped",
  barSize = 16,
  overlayOpacity = 0.5,
  scale = "linear",
  logMin = 1,
  maxPadding = 0.12,
  overlayGapPx = -14,
}: OverlayBarChartProps) {
  const isOverlay = mode === "overlay";
  const formatX = xTickFormatter ?? ((val: string) => (val?.length > 16 ? `${val.slice(0, 16)}…` : val));
  const sanitized = data.map((row) => {
    const clone: Record<string, string | number | null> = { ...row };
    Object.entries(clone).forEach(([key, val]) => {
      if (key === xKey) return;
      if (typeof val === "number" && val <= 0 && scale === "log") {
        clone[key] = null;
      }
    });
    return clone;
  });

  let minPositive = Number.POSITIVE_INFINITY;
  let maxPositive = Number.NEGATIVE_INFINITY;
  sanitized.forEach((row) => {
    Object.entries(row).forEach(([key, val]) => {
      if (key === xKey) return;
      if (typeof val === "number" && val > 0) {
        minPositive = Math.min(minPositive, val);
        maxPositive = Math.max(maxPositive, val);
      }
    });
  });

  const logDomainMin =
    scale === "log"
      ? Math.max(logMin, isFinite(minPositive) ? minPositive * 0.5 : logMin)
      : undefined;
  const linearMax =
    scale === "linear" && isFinite(maxPositive) ? maxPositive * (1 + Math.max(0, maxPadding)) : undefined;
  const logMax =
    scale === "log" && isFinite(maxPositive) ? maxPositive * (1 + Math.max(0, maxPadding)) : undefined;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={sanitized}
        margin={{ top: 16, right: 24, left: 8, bottom: 72 }}
        barCategoryGap={isOverlay ? "20%" : "18%"}
        barGap={isOverlay ? overlayGapPx : 6}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={xKey}
          angle={-35}
          textAnchor="end"
          interval="preserveStartEnd"
          height={110}
          tickMargin={16}
          minTickGap={16}
          tick={{ fontSize: 11 }}
          tickFormatter={formatX}
        />
        <YAxis
          scale={scale}
          domain={
            scale === "log"
              ? [logDomainMin ?? logMin, logMax ?? "auto"]
              : linearMax
                ? [0, linearMax]
                : undefined
          }
          allowDataOverflow={scale === "log"}
          tickFormatter={valueFormatter}
          width={80}
          tickMargin={8}
        />
        <Tooltip
          formatter={(value: any) =>
            typeof value === "number" ? valueFormatter(value) : value
          }
        />
        <Legend />
        {series.map((s) => (
          <Bar
            key={s.id}
            dataKey={s.id}
            name={s.label}
            fill={s.color}
            opacity={isOverlay ? overlayOpacity : 0.9}
            barSize={barSize}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
