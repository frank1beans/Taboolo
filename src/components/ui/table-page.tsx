/**
 * TablePage - Componente wrapper unificato per pagine con tabelle dati
 * Fornisce layout consistente con header, statistiche, filtri e azioni
 */

import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

// Types
export interface TableStat {
  label: string;
  value: string | number;
  variant?: "default" | "warning" | "success" | "error";
}

export interface ActiveFilter {
  id: string;
  label: string;
  value: string;
  onRemove?: () => void;
}

export interface TablePageProps {
  // Header
  title: string;
  description?: string;
  stats?: TableStat[];

  // Filters
  filters?: ReactNode;
  activeFilters?: ActiveFilter[];
  onClearAllFilters?: () => void;

  // Actions
  actions?: ReactNode;

  // Content
  children: ReactNode;

  // Styling
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
}

// Stat variant styles
const statVariantStyles = {
  default: "text-foreground",
  warning: "text-warning",
  success: "text-success",
  error: "text-destructive",
};

export function TablePage({
  title,
  description,
  stats,
  filters,
  activeFilters,
  onClearAllFilters,
  actions,
  children,
  className,
  headerClassName,
  contentClassName,
}: TablePageProps) {
  const hasActiveFilters = activeFilters && activeFilters.length > 0;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header Section */}
      <div className={cn(
        "flex-shrink-0 space-y-4 pb-4 border-b border-border/40",
        headerClassName
      )}>
        {/* Title Row */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}

            {/* Stats */}
            {stats && stats.length > 0 && (
              <div className="flex flex-wrap items-center gap-3 mt-2">
                {stats.map((stat, index) => (
                  <span key={stat.label} className="text-sm text-muted-foreground">
                    <span className={cn(
                      "font-semibold",
                      statVariantStyles[stat.variant || "default"]
                    )}>
                      {typeof stat.value === "number"
                        ? stat.value.toLocaleString("it-IT")
                        : stat.value}
                    </span>
                    {" "}{stat.label}
                    {index < stats.length - 1 && (
                      <span className="ml-3 text-border">•</span>
                    )}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          {actions && (
            <div className="flex items-center gap-2 flex-shrink-0">
              {actions}
            </div>
          )}
        </div>

        {/* Filters Row */}
        {(filters || hasActiveFilters) && (
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              {filters}
            </div>

            {/* Active Filters Display */}
            {hasActiveFilters && (
              <div className="flex items-center gap-2 flex-wrap">
                {activeFilters.map((filter) => (
                  <Badge
                    key={filter.id}
                    variant="outline"
                    className="text-xs px-2 py-1 border-primary/30 text-primary gap-1"
                  >
                    {filter.label}: {filter.value}
                    {filter.onRemove && (
                      <button
                        onClick={filter.onRemove}
                        className="ml-1 hover:text-destructive"
                        aria-label={`Rimuovi filtro ${filter.label}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </Badge>
                ))}
                {onClearAllFilters && activeFilters.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClearAllFilters}
                    className="h-7 text-xs"
                  >
                    Azzera tutti
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Content Section */}
      <div className={cn("flex-1 min-h-0 pt-4", contentClassName)}>
        {children}
      </div>
    </div>
  );
}

// ============= TABLE TOOLBAR =============

export interface TableToolbarProps {
  children: ReactNode;
  className?: string;
}

export function TableToolbar({ children, className }: TableToolbarProps) {
  return (
    <div className={cn(
      "flex items-center justify-between gap-3 px-3 py-2 bg-muted/30 rounded-lg border border-border/40",
      className
    )}>
      {children}
    </div>
  );
}

export interface TableToolbarGroupProps {
  children: ReactNode;
  className?: string;
  align?: "left" | "right";
}

export function TableToolbarGroup({
  children,
  className,
  align = "left"
}: TableToolbarGroupProps) {
  return (
    <div className={cn(
      "flex items-center gap-2",
      align === "right" && "ml-auto",
      className
    )}>
      {children}
    </div>
  );
}

// ============= FILTER PRESETS =============

export interface FilterPreset {
  id: string;
  name: string;
  filters: Record<string, unknown>;
}

export interface FilterPresetsProps {
  presets: FilterPreset[];
  activePresetId?: string;
  onSelectPreset: (preset: FilterPreset) => void;
  onSavePreset?: (name: string) => void;
  className?: string;
}

export function FilterPresets({
  presets,
  activePresetId,
  onSelectPreset,
  className,
}: FilterPresetsProps) {
  if (presets.length === 0) return null;

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {presets.map((preset) => (
        <Button
          key={preset.id}
          variant={activePresetId === preset.id ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onSelectPreset(preset)}
          className="h-7 text-xs"
        >
          {preset.name}
        </Button>
      ))}
    </div>
  );
}

// ============= EMPTY STATE =============

export interface TableEmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function TableEmptyState({
  icon,
  title,
  description,
  action,
  className,
}: TableEmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center",
      className
    )}>
      {icon && (
        <div className="mb-4 text-muted-foreground/50">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-4 max-w-md">
          {description}
        </p>
      )}
      {action}
    </div>
  );
}

// ============= LOADING STATE =============

export interface TableLoadingStateProps {
  message?: string;
  className?: string;
}

export function TableLoadingState({
  message = "Caricamento dati...",
  className,
}: TableLoadingStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12",
      className
    )}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mb-4" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
