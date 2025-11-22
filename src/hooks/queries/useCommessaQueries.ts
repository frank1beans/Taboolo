import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { queryKeys, staleTime } from "./index";
import type { ApiCommessa } from "@/types/api";

/**
 * Hook for fetching all commesse
 */
export function useCommesse() {
  return useQuery({
    queryKey: queryKeys.commesse.all,
    queryFn: () => api.listCommesse(),
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for fetching single commessa detail
 */
export function useCommessaDetail(commessaId: string | number | undefined) {
  const id = commessaId ? String(commessaId) : "";

  return useQuery({
    queryKey: queryKeys.commesse.detail(id),
    queryFn: () => api.getCommessa(Number(id)),
    enabled: !!id && !Number.isNaN(Number(id)),
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for creating a new commessa
 */
export function useCreateCommessa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Parameters<typeof api.createCommessa>[0]) =>
      api.createCommessa(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.commesse.all });
    },
  });
}

/**
 * Hook for updating a commessa
 */
export function useUpdateCommessa(commessaId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Parameters<typeof api.updateCommessa>[1]) =>
      api.updateCommessa(commessaId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.commesse.detail(commessaId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.commesse.all });
    },
  });
}

/**
 * Hook for deleting a commessa
 */
export function useDeleteCommessa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commessaId: number) => api.deleteCommessa(commessaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.commesse.all });
    },
  });
}

/**
 * Hook for confronto data
 */
export function useConfrontoQuery(commessaId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.confronto.detail(commessaId ?? ""),
    queryFn: () =>
      (api as unknown as { getConfronto: (id: string) => Promise<unknown> }).getConfronto(
        commessaId!
      ),
    enabled: !!commessaId,
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for analisi data
 */
export function useAnalisiQuery(commessaId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.analisi.detail(commessaId ?? ""),
    queryFn: () =>
      (api as unknown as { getAnalisi: (id: string) => Promise<unknown> }).getAnalisi(
        commessaId!
      ),
    enabled: !!commessaId,
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for WBS6 detail in analisi
 */
export function useAnalisiWbs6Detail(
  commessaId: string | undefined,
  wbs6Code: string | undefined
) {
  return useQuery({
    queryKey: queryKeys.analisi.wbs6(commessaId ?? "", wbs6Code ?? ""),
    queryFn: () =>
      (api as unknown as {
        getAnalisiWbs6Detail: (commessaId: string, wbs6Code: string) => Promise<unknown>;
      }).getAnalisiWbs6Detail(commessaId!, wbs6Code!),
    enabled: !!commessaId && !!wbs6Code,
    staleTime: staleTime.moderate,
  });
}

/**
 * Helper to invalidate all commessa-related queries
 */
export function useInvalidateCommessaData() {
  const queryClient = useQueryClient();

  return async (commessaId: string | number) => {
    const id = String(commessaId);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.commesse.detail(id) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.confronto.detail(id) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.analisi.detail(id) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.priceCatalog.commessa(id) }),
    ]);
  };
}
