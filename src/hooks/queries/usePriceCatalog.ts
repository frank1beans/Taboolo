import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { queryKeys, staleTime } from "./index";
import type { ApiPriceListItem } from "@/types/api";

/**
 * Hook for fetching commessa price catalog
 */
export function usePriceCatalog(commessaId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.priceCatalog.commessa(commessaId ?? ""),
    queryFn: () => api.getCommessaPriceCatalog(commessaId!),
    enabled: !!commessaId,
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for fetching global price catalog with filters
 */
export function useGlobalPriceCatalog(filters?: {
  businessUnit?: string;
  commessaId?: string;
}) {
  return useQuery({
    queryKey: queryKeys.priceCatalog.global(filters),
    queryFn: () => api.getGlobalPriceCatalog(filters),
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for semantic search in price catalog
 */
export function useSemanticPriceCatalog(
  query: string,
  options?: {
    threshold?: number;
    enabled?: boolean;
  }
) {
  const threshold = options?.threshold ?? 0.3;
  const enabled = (options?.enabled ?? true) && query.length >= 3;

  return useQuery({
    queryKey: queryKeys.priceCatalog.semantic(query, threshold),
    queryFn: () =>
      (api as unknown as {
        semanticSearchPriceCatalog: (
          query: string,
          threshold: number
        ) => Promise<ApiPriceListItem[]>;
      }).semanticSearchPriceCatalog(query, threshold),
    enabled,
    staleTime: staleTime.dynamic,
  });
}

/**
 * Hook for updating manual offer price
 */
export function useUpdateManualPrice(commessaId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: {
      price_list_item_id: number;
      computo_id: number;
      prezzo_unitario: number;
    }) => {
      if (!commessaId) {
        throw new Error("Commessa non valida per l'aggiornamento manuale");
      }
      return api.updateManualOfferPrice(commessaId, payload);
    },
    onSuccess: async (_data, variables) => {
      // Optimistic update for price catalog
      if (commessaId) {
        queryClient.setQueryData<ApiPriceListItem[] | undefined>(
          queryKeys.priceCatalog.commessa(commessaId),
          (current) => {
            if (!current) return current;

            return current.map((item) => {
              if (item.id !== variables.price_list_item_id) return item;

              // Update the offer price for this item
              const existingOffers = { ...(item.offer_prices ?? {}) };
              // Note: caller should handle the specific offer key update

              return {
                ...item,
                offer_prices: existingOffers,
              };
            });
          }
        );

        // Invalidate related queries
        await queryClient.invalidateQueries({
          queryKey: queryKeys.confronto.detail(commessaId),
        });
        await queryClient.invalidateQueries({
          queryKey: queryKeys.analisi.detail(commessaId),
        });
      }
    },
  });
}

/**
 * Helper to invalidate all price catalog queries for a commessa
 */
export function useInvalidatePriceCatalog() {
  const queryClient = useQueryClient();

  return (commessaId: string) => {
    return queryClient.invalidateQueries({
      queryKey: queryKeys.priceCatalog.commessa(commessaId),
    });
  };
}
