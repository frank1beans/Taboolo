import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { queryKeys, staleTime } from "./index";
import { useMemo } from "react";
import type { FrontendWbsNode } from "@/types/api";

type ApiWithWbs = {
  getWbsTree(commessaId: string): Promise<FrontendWbsNode[]>;
  getComputoWbs(commessaId: string, computoId?: number): Promise<unknown>;
};

const apiClient = api as unknown as ApiWithWbs;

/**
 * Hook for fetching WBS tree structure
 */
export function useWbsTree(commessaId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.wbs.tree(commessaId ?? ""),
    queryFn: () => apiClient.getWbsTree(commessaId!),
    enabled: !!commessaId,
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for fetching computo WBS data
 */
export function useComputoWbs(
  commessaId: string | undefined,
  computoId?: number
) {
  return useQuery({
    queryKey: queryKeys.wbs.computo(commessaId ?? "", computoId),
    queryFn: () => apiClient.getComputoWbs(commessaId!, computoId),
    enabled: !!commessaId,
    staleTime: staleTime.moderate,
  });
}

/**
 * Hook for filtering data by WBS node selection
 */
export function useWbsFilteredData<T extends { wbs6_code?: string | null; wbs7_code?: string | null }>(
  data: T[],
  selectedNodeId: string | null,
  wbsTree: FrontendWbsNode[]
) {
  return useMemo(() => {
    if (!selectedNodeId) return data;

    // Find the selected node in tree
    const selectedNode = wbsTree.find((n) => n.id === selectedNodeId);

    if (selectedNode) {
      // Filter by WBS6
      return data.filter((item) => item.wbs6_code === selectedNode.code);
    }

    // Check if it's a WBS7 node
    for (const wbs6 of wbsTree) {
      const wbs7 = wbs6.children.find((c) => c.id === selectedNodeId);
      if (wbs7) {
        return data.filter(
          (item) => item.wbs6_code === wbs6.code && item.wbs7_code === wbs7.code
        );
      }
    }

    return data;
  }, [data, selectedNodeId, wbsTree]);
}

/**
 * Hook for building WBS tree from price catalog items
 */
export function useBuildWbsTree<
  T extends {
    wbs6_code?: string | null;
    wbs6_description?: string | null;
    wbs7_code?: string | null;
    wbs7_description?: string | null;
  }
>(items: T[], getItemValue?: (item: T) => number) {
  return useMemo<FrontendWbsNode[]>(() => {
    if (!items.length) return [];

    const wbs6Map = new Map<string, FrontendWbsNode>();
    const wbs7Map = new Map<string, FrontendWbsNode>();

    items.forEach((item) => {
      const wbs6Code = item.wbs6_code || "SENZA_WBS6";
      const wbs7Code = item.wbs7_code;
      const itemValue = getItemValue ? getItemValue(item) : 0;

      // Create or update WBS6 node
      if (!wbs6Map.has(wbs6Code)) {
        const pathEntry = {
          level: 6,
          code: wbs6Code,
          description: item.wbs6_description || "",
        };
        wbs6Map.set(wbs6Code, {
          id: `wbs6-${wbs6Code}`,
          level: 6,
          code: wbs6Code,
          description: item.wbs6_description || "",
          importo: 0,
          children: [],
          path: [pathEntry],
        });
      }

      const wbs6Node = wbs6Map.get(wbs6Code)!;
      wbs6Node.importo += itemValue;

      // Create or update WBS7 node if exists
      if (wbs7Code) {
        const wbs7Key = `${wbs6Code}-${wbs7Code}`;
        if (!wbs7Map.has(wbs7Key)) {
          const path = [
            ...wbs6Node.path,
            {
              level: 7,
              code: wbs7Code,
              description: item.wbs7_description || "",
            },
          ];
          const wbs7Node: FrontendWbsNode = {
            id: `wbs7-${wbs7Key}`,
            level: 7,
            code: wbs7Code,
            description: item.wbs7_description || "",
            importo: 0,
            children: [],
            path,
          };
          wbs7Map.set(wbs7Key, wbs7Node);
          wbs6Node.children.push(wbs7Node);
        }
        const wbs7Node = wbs7Map.get(wbs7Key)!;
        wbs7Node.importo += itemValue;
      }
    });

    return Array.from(wbs6Map.values()).sort((a, b) =>
      (a.code || "").localeCompare(b.code || "")
    );
  }, [items, getItemValue]);
}
