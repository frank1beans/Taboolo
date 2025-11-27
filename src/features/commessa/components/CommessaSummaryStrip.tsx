import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { MetricCard } from "@/components/ui/metric-card";

export type CommessaMetric = {
  label: string;
  value: string;
  helper?: string;
  icon?: ReactNode;
  emphasise?: boolean;
};

interface CommessaSummaryStripProps {
  metrics: CommessaMetric[];
  className?: string;
}

export const CommessaSummaryStrip = ({ metrics, className }: CommessaSummaryStripProps) => {
  if (!metrics.length) return null;

  // Split metrics into left (first 3) and right (last) for alignment with grid below
  const leftMetrics = metrics.slice(0, 3);
  const rightMetrics = metrics.slice(3);

  return (
    <div
      className={cn(
        "grid gap-3 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]",
        className,
      )}
    >
      {/* Left section - first 3 metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {leftMetrics.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            helper={metric.helper}
            icon={metric.icon}
            emphasise={metric.emphasise}
          />
        ))}
      </div>

      {/* Right section - last metric */}
      {rightMetrics.length > 0 && (
        <div className="grid gap-3">
          {rightMetrics.map((metric) => (
            <MetricCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              helper={metric.helper}
              icon={metric.icon}
              emphasise={metric.emphasise}
            />
          ))}
        </div>
      )}
    </div>
  );
};
