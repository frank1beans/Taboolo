/**
 * Centralized data fetching hooks
 * Provides consistent query keys, caching, and error handling
 */

export * from "./usePriceCatalog";
export * from "./useCommessaQueries";
export * from "./useWbsQueries";
export * from "./usePropertySchemas";

// Query key factory for consistent cache management
export const queryKeys = {
  // Commesse
  commesse: {
    all: ["commesse"] as const,
    detail: (id: string | number) => ["commessa", String(id)] as const,
    computi: (id: string | number) => ["commessa", String(id), "computi"] as const,
  },

  // Price catalogs
  priceCatalog: {
    commessa: (commessaId: string) => ["price-catalog", commessaId] as const,
    global: (filters?: Record<string, unknown>) =>
      filters ? ["price-catalog", "global", filters] : (["price-catalog", "global"] as const),
    semantic: (query: string, threshold?: number) =>
      ["price-catalog", "semantic", query, threshold] as const,
  },

  // Property schemas
  propertySchemas: {
    all: () => ["property-schemas"] as const,
  },

  // Confronto & Analisi
  confronto: {
    detail: (commessaId: string) => ["confronto", commessaId] as const,
  },
  analisi: {
    detail: (commessaId: string) => ["analisi", commessaId] as const,
    wbs6: (commessaId: string, wbs6Code: string) =>
      ["analisi", commessaId, "wbs6", wbs6Code] as const,
  },

  // WBS
  wbs: {
    tree: (commessaId: string) => ["wbs", commessaId, "tree"] as const,
    computo: (commessaId: string, computoId?: number) =>
      computoId
        ? (["wbs", commessaId, "computo", computoId] as const)
        : (["wbs", commessaId, "computo"] as const),
  },
} as const;

// Stale time configurations
export const staleTime = {
  // Data that rarely changes
  static: 30 * 60 * 1000, // 30 minutes

  // Data that changes moderately
  moderate: 5 * 60 * 1000, // 5 minutes

  // Data that changes frequently
  dynamic: 1 * 60 * 1000, // 1 minute

  // Always fresh
  none: 0,
} as const;
