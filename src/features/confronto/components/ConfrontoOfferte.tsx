import { useEffect, useMemo, useState, useCallback } from "react";
import { useTheme } from "next-themes";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { TablePage, type TableStat, type ActiveFilter } from "@/components/ui/table-page";
import { QuickFilters } from "@/components/ui/table-filters";
import { Button } from "@/components/ui/button";
import { PanelRight, BarChart3 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { formatCurrency } from "@/lib/grid-utils";
import type { ApiWbs7Node, FrontendWbsNode } from "@/types/api";

import { ConfrontoOfferteProps } from "../types";
import { useConfrontoData } from "../hooks/useConfrontoData";
import { useConfrontoColumns } from "../hooks/useConfrontoColumns";
import { ConfrontoGrid } from "./ConfrontoGrid";
import { exportConfrontoToExcel } from "../excel-export";

export function ConfrontoOfferte({
  commessaId,
  selectedRound,
  selectedImpresa,
  onRoundChange,
  onImpresaChange,
  onNavigateToCharts,
}: ConfrontoOfferteProps) {
  const { theme } = useTheme();
  const isDarkMode = theme === "dark";

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showOnlyQuantityMismatch, setShowOnlyQuantityMismatch] = useState(false);
  const isRoundControlled = selectedRound !== undefined;
  const [internalRound, setInternalRound] = useState<"all" | number>("all");
  const effectiveRound = isRoundControlled ? (selectedRound as "all" | number) : internalRound;

  useEffect(() => {
    if (isRoundControlled && selectedRound !== undefined) {
      setInternalRound(selectedRound as "all" | number);
    }
  }, [isRoundControlled, selectedRound]);

  const {
    data: confrontoData,
    isLoading: isLoadingConfronto,
    error: errorConfronto,
    rowData,
    filteredImprese,
    rounds: roundOptions,
  } = useConfrontoData(commessaId, effectiveRound);

  const { data: wbsDataRaw } = useQuery({
    queryKey: ["commesse", commessaId, "wbs", "structure"],
    queryFn: () => api.getCommessaWbsStructure(commessaId),
    enabled: !!commessaId,
  });

  const wbsData = useMemo<FrontendWbsNode[]>(() => {
    if (!wbsDataRaw?.wbs6) return [];
    const wbs7ByParent = new Map<number, ApiWbs7Node[]>();
    (wbsDataRaw.wbs7 ?? []).forEach((node) => {
      const bucket = wbs7ByParent.get(node.wbs6_id);
      if (bucket) {
        bucket.push(node);
      } else {
        wbs7ByParent.set(node.wbs6_id, [node]);
      }
    });

    return wbsDataRaw.wbs6.map((node) => {
      const basePath = [
        {
          level: 6,
          code: node.code ?? "",
          description: node.description ?? "",
        },
      ];
      const children: FrontendWbsNode[] = (wbs7ByParent.get(node.id) ?? []).map((child) => ({
        id: `wbs7-${child.id}`,
        code: child.code || "",
        description: child.description || "",
        level: 7,
        importo: 0,
        children: [],
        path: [
          ...basePath,
          {
            level: 7,
            code: child.code ?? "",
            description: child.description ?? "",
          },
        ],
      }));

      return {
        id: String(node.id),
        code: node.code || "",
        description: node.description || "",
        level: 6,
        importo: 0,
        children,
        path: basePath,
      };
    });
  }, [wbsDataRaw]);

  const [selectedWbsNodeId, setSelectedWbsNodeId] = useState<string | null>(null);
  const selectedWbsFilter = useMemo<
    { wbs6: string | null; wbs7: string | null; label: string } | null
  >(() => {
    if (!selectedWbsNodeId) return null;

    for (const wbs6 of wbsData) {
      if (wbs6.id === selectedWbsNodeId || wbs6.code === selectedWbsNodeId) {
        return {
          wbs6: wbs6.code ?? null,
          wbs7: null,
          label: wbs6.code
            ? `${wbs6.code}${wbs6.description ? ` · ${wbs6.description}` : ""}`
            : wbs6.description || wbs6.id,
        };
      }

      for (const wbs7 of wbs6.children ?? []) {
        if (wbs7.id === selectedWbsNodeId || wbs7.code === selectedWbsNodeId) {
          return {
            wbs6: wbs6.code ?? null,
            wbs7: wbs7.code ?? null,
            label: wbs7.code
              ? `${wbs7.code}${wbs7.description ? ` · ${wbs7.description}` : ""}`
              : wbs7.description || wbs7.id,
          };
        }
      }
    }

    return null;
  }, [selectedWbsNodeId, wbsData]);

  const handleRoundSelect = (round: "all" | number) => {
    if (!isRoundControlled) {
      setInternalRound(round);
    }
    onRoundChange?.(round);
  };

  const filteredRowData = useMemo(() => {
    let rows = rowData;
    if (showOnlyQuantityMismatch) {
      rows = rows.filter((row) => row.hasQuantityMismatch);
    }
    if (!selectedWbsFilter) return rows;

    return rows.filter((row) => {
      if (!selectedWbsFilter.wbs6) return false;
      if (selectedWbsFilter.wbs7) {
        return (
          row.wbs6Code === selectedWbsFilter.wbs6 &&
          row.wbs7Code === selectedWbsFilter.wbs7
        );
      }
      return row.wbs6Code === selectedWbsFilter.wbs6;
    });
  }, [rowData, selectedWbsFilter, showOnlyQuantityMismatch]);

  const columns = useConfrontoColumns({
    filteredImprese,
    isDarkMode,
  });

  const handleExcelExport = useCallback(async () => {
    await exportConfrontoToExcel(filteredRowData, filteredImprese, commessaId);
  }, [filteredRowData, filteredImprese, commessaId]);

  if (isLoadingConfronto) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (errorConfronto) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Errore nel caricamento del confronto offerte</AlertDescription>
      </Alert>
    );
  }

  // Calculate total for stats
  const totalImportoProgetto = filteredRowData.reduce((sum, row) => sum + (row.importoTotaleProgetto || 0), 0);

  // Build stats for TablePage
  const tableStats: TableStat[] = [
    { label: "voci", value: filteredRowData.length },
    { label: "importo", value: formatCurrency(totalImportoProgetto) },
    { label: "imprese", value: filteredImprese.length },
  ];

  // Build active filters
  const activeFiltersArray: ActiveFilter[] = [
    ...(selectedWbsFilter
      ? [{
        id: "wbs",
        label: "WBS",
        value: selectedWbsFilter.label,
        onRemove: () => setSelectedWbsNodeId(null),
      }]
      : []),
    ...(effectiveRound !== "all"
      ? [{
        id: "round",
        label: "Round",
        value: String(effectiveRound),
        onRemove: () => handleRoundSelect("all"),
      }]
      : []),
    ...(showOnlyQuantityMismatch
      ? [{
        id: "quantityMismatch",
        label: "Δ Quantità",
        value: "Solo differenze",
        onRemove: () => setShowOnlyQuantityMismatch(false),
      }]
      : []),
  ];

  // Build round filters
  const roundFilters = roundOptions.length > 0 ? [
    { id: "all", label: "Tutti", filter: () => handleRoundSelect("all"), isActive: effectiveRound === "all" },
    ...roundOptions.map((round) => ({
      id: String(round.numero),
      label: round.label,
      filter: () => handleRoundSelect(round.numero),
      isActive: effectiveRound === round.numero,
    })),
  ] : [];

  const filtersToolbar = (
    <div className="flex w-full flex-wrap items-center gap-2">
      {roundFilters.length > 0 && <QuickFilters filters={roundFilters} />}
      <div className="ml-auto flex flex-wrap items-center gap-2">
        <Button
          variant={showOnlyQuantityMismatch ? "secondary" : "outline"}
          size="sm"
          onClick={() => setShowOnlyQuantityMismatch((prev) => !prev)}
          className="h-8 gap-1.5"
        >
          Δ Quantità
        </Button>
        {wbsData.length > 0 && (
          <Button
            variant={isSidebarOpen ? "secondary" : "outline"}
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="h-8 gap-1.5"
          >
            <PanelRight className="h-4 w-4" />
            WBS
          </Button>
        )}
        {onNavigateToCharts && (
          <Button
            variant="outline"
            size="sm"
            onClick={onNavigateToCharts}
            className="h-8 gap-1.5"
          >
            <BarChart3 className="h-4 w-4" />
            Grafici
          </Button>
        )}
      </div>
    </div>
  );

  return (
    <TablePage
      title="Confronto Offerte"
      description="Analisi comparativa prezzi unitari tra imprese per round - usa colori e icone per leggere i delta a colpo d'occhio"
      stats={tableStats}
      activeFilters={activeFiltersArray}
      onClearAllFilters={() => {
        setSelectedWbsNodeId(null);
        handleRoundSelect("all");
      }}
      filters={filtersToolbar}
      className="h-full"
    >
      <ConfrontoGrid
        rowData={filteredRowData}
        columnDefs={columns}
        isLoading={isLoadingConfronto}
        isDarkMode={isDarkMode}
        commessaId={commessaId}
        onExcelExport={handleExcelExport}
      />

      {/* WBS Panel as Sheet Overlay */}
      <Sheet open={isSidebarOpen} onOpenChange={setIsSidebarOpen}>
        <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0">
          <SheetHeader className="px-4 py-3 border-b">
            <SheetTitle className="text-base">Filtro WBS</SheetTitle>
          </SheetHeader>
          <div className="h-[calc(100%-57px)] overflow-y-auto p-3">
            <WBSFilterPanel
              nodes={wbsData}
              selectedNodeId={selectedWbsNodeId}
              onNodeSelect={(nodeId) => {
                setSelectedWbsNodeId(nodeId);
              }}
              onClose={() => setIsSidebarOpen(false)}
              showAmounts={false}
            />
          </div>
        </SheetContent>
      </Sheet>
    </TablePage>
  );
}
