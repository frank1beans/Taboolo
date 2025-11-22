/**
 * MetricCard - Card unificata per visualizzazione metriche
 * Sostituisce duplicazioni in CommessaSummaryStrip, Home, AnalisiAvanzate
 */

import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export interface MetricCardProps {
  label: string;
  value: string | number;
  helper?: string;
  icon?: ReactNode | LucideIcon;
  trend?: {
    value: number;
    direction: "up" | "down" | "neutral";
  };
  variant?: "default" | "ghost" | "glass" | "compact";
  size?: "sm" | "md" | "lg";
  emphasise?: boolean;
  className?: string;
}

const variantStyles = {
  default: "rounded-[var(--radius-lg)] border border-border bg-card shadow-[var(--shadow-xs)]",
  ghost: "rounded-[var(--radius-md)] bg-muted/50 border border-border/60",
  glass: "rounded-[var(--radius-lg)] border border-border bg-card shadow-[var(--shadow-xs)]",
  compact: "rounded-[var(--radius-md)] border border-border bg-card",
};

const sizeStyles = {
  sm: "p-3 gap-2",
  md: "p-4 gap-3",
  lg: "p-5 gap-4",
};

const valueSizeStyles = {
  sm: "text-base",
  md: "text-lg",
  lg: "text-xl",
};

const emphasiseStyles = {
  sm: "text-lg",
  md: "text-2xl",
  lg: "text-3xl",
};

export function MetricCard({
  label,
  value,
  helper,
  icon,
  trend,
  variant = "default",
  size = "md",
  emphasise = false,
  className,
}: MetricCardProps) {
  const IconComponent = icon as LucideIcon;
  const isIconComponent = typeof icon === "function";

  return (
    <div
      className={cn(
        "flex items-center",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {icon && (
        <div className="rounded-lg bg-muted text-foreground/70 p-2">
          {isIconComponent ? <IconComponent className="h-5 w-5" /> : icon}
        </div>
      )}
      <div className="flex-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <div className="flex items-baseline gap-2">
          <p
            className={cn(
              "font-semibold text-foreground",
              emphasise ? emphasiseStyles[size] : valueSizeStyles[size]
            )}
          >
            {value}
          </p>
          {trend && (
            <span
              className={cn(
                "text-xs font-medium",
                trend.direction === "up" && "text-emerald-600 dark:text-emerald-400",
                trend.direction === "down" && "text-red-600 dark:text-red-400",
                trend.direction === "neutral" && "text-muted-foreground"
              )}
            >
              {trend.direction === "up" && "↑"}
              {trend.direction === "down" && "↓"}
              {trend.value > 0 ? "+" : ""}{trend.value}%
            </span>
          )}
        </div>
        {helper && (
          <p className="text-xs text-muted-foreground">{helper}</p>
        )}
      </div>
    </div>
  );
}

// ============= METRIC GRID =============

interface MetricGridProps {
  metrics: MetricCardProps[];
  columns?: 2 | 3 | 4;
  variant?: MetricCardProps["variant"];
  size?: MetricCardProps["size"];
  className?: string;
}

const gridColumns = {
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
};

export function MetricGrid({
  metrics,
  columns = 3,
  variant = "default",
  size = "md",
  className,
}: MetricGridProps) {
  if (!metrics.length) return null;

  return (
    <div className={cn("grid gap-4", gridColumns[columns], className)}>
      {metrics.map((metric) => (
        <MetricCard
          key={metric.label}
          {...metric}
          variant={metric.variant ?? variant}
          size={metric.size ?? size}
        />
      ))}
    </div>
  );
}

// ============= STAT CARD (alias compatto) =============

export interface StatCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: number;
  className?: string;
}

export function StatCard({ label, value, icon, trend, className }: StatCardProps) {
  return (
    <MetricCard
      label={label}
      value={value}
      icon={icon}
      trend={
        trend !== undefined
          ? {
              value: trend,
              direction: trend > 0 ? "up" : trend < 0 ? "down" : "neutral",
            }
          : undefined
      }
      variant="compact"
      size="sm"
      className={className}
    />
  );
}
