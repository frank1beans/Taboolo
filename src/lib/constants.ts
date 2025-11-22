/**
 * Costanti e configurazioni centralizzate per l'applicazione
 */

import type { LucideIcon } from "lucide-react";
import { Clock, Play, CheckCircle, BarChart3, Euro, Layers3, Clock3 } from "lucide-react";
import type { CommessaStato } from "@/types/api";

// ============= STATUS CONFIG =============

export type BadgeVariant = "info" | "success" | "muted" | "warning" | "destructive";

export interface StatusConfig {
  label: string;
  description: string;
  badgeVariant: BadgeVariant;
  icon: LucideIcon;
  className: string;
}

export const STATUS_CONFIG: Record<CommessaStato, StatusConfig> = {
  setup: {
    label: "In setup",
    description: "Commessa in fase di preparazione",
    badgeVariant: "info",
    icon: Clock,
    className: "bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-200 border-sky-200 dark:border-sky-900",
  },
  in_corso: {
    label: "In corso",
    description: "Attiva e monitorata",
    badgeVariant: "success",
    icon: Play,
    className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200 border-emerald-200 dark:border-emerald-900",
  },
  chiusa: {
    label: "Chiusa",
    description: "Archiviata o completata",
    badgeVariant: "muted",
    icon: CheckCircle,
    className: "bg-slate-200 text-slate-700 dark:bg-slate-900 dark:text-slate-200 border-slate-300 dark:border-slate-800",
  },
};

// ============= BADGE STYLES =============

export const BADGE_VARIANT_STYLES: Record<BadgeVariant, string> = {
  success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  info: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  muted: "bg-muted text-muted-foreground",
  destructive: "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300",
};

// ============= METRIC ICONS =============

export const METRIC_ICONS = {
  currency: Euro,
  layers: Layers3,
  chart: BarChart3,
  clock: Clock3,
} as const;

// ============= CRITICALITY =============

export type CriticalityLevel = "alta" | "media" | "bassa";

export const CRITICALITY_CONFIG: Record<CriticalityLevel, { label: string; color: string; bgClass: string }> = {
  alta: {
    label: "Alta",
    color: "#dc2626",
    bgClass: "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300",
  },
  media: {
    label: "Media",
    color: "#f59e0b",
    bgClass: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  },
  bassa: {
    label: "Bassa",
    color: "#10b981",
    bgClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  },
};

// ============= CHART COLORS =============

export const CHART_COLORS = {
  primary: "#1E93BD",
  secondary: "#64748b",
  success: "#10b981",
  warning: "#f59e0b",
  destructive: "#dc2626",
  muted: "#94a3b8",
} as const;

export const CHART_COLOR_PALETTE = [
  "#3b82f6", // blue
  "#f59e0b", // amber
  "#10b981", // green
  "#a855f7", // purple
  "#f43f5e", // rose
  "#06b6d4", // cyan
  "#64748b", // slate
  "#ec4899", // pink
];

// ============= GRID DEFAULTS =============

export const GRID_PAGE_SIZE = 100;
export const GRID_ROW_HEIGHT = 42;
export const GRID_HEADER_HEIGHT = 56;

// ============= LAYOUT CONSTANTS =============

export const TOPBAR_HEIGHT = 44;
export const SIDEBAR_WIDTH = 256;
export const SIDEBAR_COLLAPSED_WIDTH = 64;

// ============= LOCALE =============

export const LOCALE = "it-IT";
export const CURRENCY = "EUR";

// ============= API QUERY KEYS =============

export const queryKeys = {
  commesse: () => ["commesse"] as const,
  commessa: (id: string | number) => ["commessa", String(id), "layout"] as const,
  wbs: (id: string | number) => ["commesse", String(id), "wbs", "structure"] as const,
  confronto: (id: string | number) => ["confronto", String(id)] as const,
  analisi: (id: string | number) => ["analisi", String(id)] as const,
  priceCatalog: (id?: string | number) => id
    ? ["priceCatalog", String(id)] as const
    : ["priceCatalog"] as const,
  dashboardStats: () => ["dashboardStats"] as const,
  settings: () => ["settings"] as const,
} as const;
