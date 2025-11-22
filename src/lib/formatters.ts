/**
 * Formatters centralizzati per l'applicazione
 * Sostituisce i formatter duplicati in vari file
 */

import type { ApiComputo } from "@/types/api";

// ============= CURRENCY =============

export const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "€0,00";
  return `€${value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatCurrencyCompact = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "€0";

  const absValue = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (absValue >= 1_000_000) {
    return `${sign}€${(absValue / 1_000_000).toLocaleString("it-IT", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}M`;
  }

  if (absValue >= 1_000) {
    return `${sign}€${(absValue / 1_000).toLocaleString("it-IT", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    })}K`;
  }

  return formatCurrency(value);
};

// ============= NUMBERS =============

export const formatNumber = (
  value: number | null | undefined,
  decimals: number = 2
): string => {
  if (value === null || value === undefined || isNaN(value)) return "0";
  return value.toLocaleString("it-IT", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatInteger = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "0";
  return value.toLocaleString("it-IT", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
};

export const formatPercentage = (
  value: number | null | undefined,
  decimals: number = 2
): string => {
  if (value === null || value === undefined || isNaN(value)) return "0%";
  return `${value.toLocaleString("it-IT", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
};

// ============= DATES =============

export const formatDate = (value?: string | Date | null): string => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
};

export const formatShortDate = (value?: string | Date | null): string => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

export const formatDateTime = (value?: string | Date | null): string => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleString("it-IT", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatFullDateTime = (value?: string | Date | null): string => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatRelativeTime = (value?: string | Date | null): string => {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) return "Adesso";
  if (diffMinutes < 60) return `${diffMinutes} min fa`;
  if (diffHours < 24) return `${diffHours} ore fa`;
  if (diffDays < 7) return `${diffDays} giorni fa`;

  return formatShortDate(date);
};

// ============= TEXT =============

export const truncateText = (
  text: string | null | undefined,
  maxLength: number = 80
): string => {
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
};

export const truncateMiddle = (
  text: string | null | undefined,
  startChars: number = 50,
  endChars: number = 50
): string => {
  if (!text) return "—";
  const totalChars = startChars + endChars;
  if (text.length <= totalChars) return text;
  const start = text.slice(0, startChars);
  const end = text.slice(-endChars);
  return `${start}...${end}`;
};

// ============= COMPUTI HELPERS =============

export const groupComputi = (computi: ApiComputo[]) => {
  const progetto = computi.filter((c) => c.tipo === "progetto");
  const ritorni = computi.filter((c) => c.tipo === "ritorno");
  return { progetto, ritorni };
};

export const getRoundLabel = (roundNumber: number | null | undefined): string => {
  if (roundNumber === null || roundNumber === undefined) return "—";
  return `Round ${roundNumber}`;
};

// ============= DELTA FORMATTING =============

export const formatDelta = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "0%";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatPercentage(value, 1)}`;
};

export const formatDeltaCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "€0";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatCurrency(value)}`;
};
