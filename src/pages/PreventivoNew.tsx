import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "@/lib/api-client";
import { useMemo, useState } from "react";
import type { ColDef } from "ag-grid-community";
import { DataTable, type ColumnAggregation } from "@/components/DataTable";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { TablePage, type TableStat, type ActiveFilter } from "@/components/ui/table-page";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { PanelRight } from "lucide-react";
import {
  formatCurrency,
  truncateMiddle,
} from "@/lib/grid-utils";
import type { ApiAggregatedVoce, ApiWbsPathEntry, FrontendWbsNode } from "@/types/api";
import { useCommessaContext } from "@/hooks/useCommessaContext";

export default function PreventivoNew() {
  const { id: commessaId, computoId } = useParams();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const { commessa } = useCommessaContext();

  // Fetch WBS data
  const { data: wbsData, isLoading: wbsLoading } = useQuery({
    queryKey: ["computo-wbs", computoId],
    queryFn: () => api.getComputoWbs(computoId!),
    enabled: !!computoId,
  });

  const computo = commessa?.computi?.find((c) => c.id === Number(computoId));
  const isLoading = !commessa || wbsLoading;

  // Convert WBS tree to frontend nodes
  const wbsTree = useMemo<FrontendWbsNode[]>(() => {
    if (!wbsData?.tree) return [];

    const convertNode = (node: any, index: number, parentPath: ApiWbsPathEntry[] = []): FrontendWbsNode => {
      const pathEntry = {
        level: node.level,
        code: node.code,
        description: node.description,
      };
      const path = [...parentPath, pathEntry];
      const fallback = node.code ?? node.description ?? `level-${node.level}-${index}`;
      const id = path.map((entry) => `${entry.level}:${entry.code ?? entry.description ?? "node"}`).join("|") || fallback;

      return {
        id,
        level: node.level,
        code: node.code,
        description: node.description,
        importo: node.importo,
        path,
        children: node.children
          ? node.children.map((child: any, idx: number) => convertNode(child, idx, path))
          : [],
      };
    };

    return wbsData.tree.map((node, idx) => convertNode(node, idx));
  }, [wbsData]);

  // Filter voci based on selected WBS node
  const filteredVoci = useMemo(() => {
    if (!wbsData?.voci) return [];
    if (!selectedNodeId) return wbsData.voci;

    const findNode = (nodes: FrontendWbsNode[], id: string): FrontendWbsNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node;
        if (node.children) {
          const found = findNode(node.children, id);
          if (found) return found;
        }
      }
      return null;
    };

    const selectedNode = findNode(wbsTree, selectedNodeId);
    if (!selectedNode) return wbsData.voci;

    const selectedPath = selectedNode.path ?? [];
    if (!selectedPath.length) return wbsData.voci;

    const matchesSegment = (segment: ApiWbsPathEntry, voceSegment?: ApiWbsPathEntry) => {
      if (!segment.code && !segment.description) return true;
      if (!voceSegment) return false;
      if (segment.code && voceSegment.code) {
        return voceSegment.code === segment.code;
      }
      if (!segment.code && segment.description) {
        return (voceSegment.description ?? "").trim().toLowerCase() === segment.description.trim().toLowerCase();
      }
      return true;
    };

    const matchesPath = (voce: ApiAggregatedVoce) => {
      if (!voce.wbs_path?.length) return false;
      return selectedPath.every((segment) => {
        const voceSegment = voce.wbs_path?.find((entry) => entry.level === segment.level);
        return matchesSegment(segment, voceSegment);
      });
    };

    return wbsData.voci.filter((voce) => matchesPath(voce));
  }, [wbsData, selectedNodeId, wbsTree]);

  // Column definitions
  const columnDefs = useMemo<ColDef<ApiAggregatedVoce>[]>(() => {
    return [
      // Base columns
      {
        field: "codice",
        headerName: "Codice",
        width: 150,
        cellClass: "font-mono text-xs font-semibold",
        headerClass: "font-semibold",
        sortable: true,
        resizable: true,
        filter: true,
        valueFormatter: (params) => params.value || "-",
      },
      {
        field: "descrizione",
        headerName: "Descrizione",
        width: 500,
        cellClass: "text-sm",
        headerClass: "font-semibold",
        sortable: true,
        resizable: true,
        filter: true,
        wrapText: false,
        autoHeight: false,
        valueFormatter: (params) => truncateMiddle(params.value, 60, 60),
        tooltipValueGetter: (params) => params.value || "",
      },
      {
        field: "unita_misura",
        headerName: "U.M.",
        width: 80,
        cellClass: "text-center font-mono text-xs",
        headerClass: "text-center font-semibold",
        sortable: true,
        resizable: true,
        valueFormatter: (params) => params.value || "-",
      },

      // WBS columns
      {
        field: "wbs_6_code",
        headerName: "WBS6",
        width: 100,
        cellClass: "font-mono text-xs",
        sortable: true,
        resizable: true,
        filter: true,
      },
      {
        field: "wbs_7_code",
        headerName: "WBS7",
        width: 100,
        cellClass: "font-mono text-xs",
        sortable: true,
        resizable: true,
        filter: true,
      },

      // Quantity, price, amount
      {
        field: "quantita_totale",
        headerName: "Quantità",
        width: 110,
        type: "numericColumn",
        cellClass: "font-mono text-sm",
        headerClass: "text-right font-semibold",
        sortable: true,
        resizable: true,
        valueFormatter: (params) =>
          params.value != null
            ? params.value.toLocaleString("it-IT", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 3,
              })
            : "0",
      },
      {
        field: "prezzo_unitario",
        headerName: "P. Unitario",
        width: 120,
        type: "numericColumn",
        cellClass: "font-mono text-sm font-semibold",
        headerClass: "text-right font-semibold",
        sortable: true,
        resizable: true,
        valueFormatter: (params) =>
          params.value != null ? formatCurrency(params.value) : "-",
      },
      {
        field: "importo_totale",
        headerName: "Importo",
        width: 130,
        type: "numericColumn",
        cellClass: "font-mono text-sm font-bold",
        headerClass: "text-right font-semibold",
        sortable: true,
        resizable: true,
        valueFormatter: (params) => formatCurrency(params.value),
      },
    ];
  }, []);

  // Statistics
  const stats = useMemo(() => {
    const totalVoci = filteredVoci.length;
    const totalAmount =
      filteredVoci.reduce((sum, voce) => sum + (voce.importo_totale || 0), 0) || 0;
    const wbs6Count = new Set(
      filteredVoci.map((voce) => voce.wbs_6_code).filter(Boolean)
    ).size;
    const wbs7Count = new Set(
      filteredVoci.map((voce) => voce.wbs_7_code).filter(Boolean)
    ).size;

    return { totalVoci, totalAmount, wbs6Count, wbs7Count };
  }, [filteredVoci]);

  // Build stats for TablePage
  const tableStats: TableStat[] = [
    { label: "voci", value: stats.totalVoci.toLocaleString("it-IT") },
    { label: "importo", value: formatCurrency(stats.totalAmount) },
    { label: "WBS6", value: stats.wbs6Count },
  ];

  // Build active filters for TablePage
  const activeFiltersArray: ActiveFilter[] = selectedNodeId
    ? [{
        id: "wbs",
        label: "WBS",
        value: selectedNodeId.split("|").pop()?.split(":")[1] || selectedNodeId,
        onRemove: () => setSelectedNodeId(null),
      }]
    : [];

  // Aggregations for footer
  const aggregations: ColumnAggregation[] = [
    {
      field: "importo_totale",
      type: "sum",
      label: "Totale",
      formatter: (v) => formatCurrency(v),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex-1 space-y-6 bg-muted/30 p-8">
        <Skeleton className="h-8 w-64 rounded-2xl" />
        <div className="grid gap-4 md:grid-cols-4">
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
        </div>
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!commessa || !computo) {
    return (
      <div className="flex-1 bg-muted/30 p-8">
        <Alert variant="destructive" className="rounded-2xl border border-border/60">
          <AlertDescription>Preventivo non trovato</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <TablePage
      title={computo?.nome || "Preventivo"}
      description="Dettaglio voci computo metrico con quantità e prezzi"
      stats={tableStats}
      activeFilters={activeFiltersArray}
      onClearAllFilters={() => setSelectedNodeId(null)}
      actions={
        wbsTree.length > 0 ? (
          <Button
            variant={sidebarOpen ? "secondary" : "outline"}
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="h-8 gap-1.5"
          >
            <PanelRight className="h-4 w-4" />
            WBS
          </Button>
        ) : undefined
      }
      className="h-full"
    >
      <DataTable<ApiAggregatedVoce>
        data={filteredVoci}
        columnDefs={columnDefs}
        height="70vh"
        headerHeight={64}
        enableSearch={true}
        enableExport={true}
        enableColumnToggle={true}
        exportFileName={`preventivo-${computo.nome}`}
        getRowId={(params) =>
          `${params.data.codice}-${params.data.wbs_6_code}-${params.data.wbs_7_code}`
        }
        aggregations={aggregations}
        showAggregationFooter={true}
      />

      {/* WBS Panel as Sheet Overlay */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0">
          <SheetHeader className="px-4 py-3 border-b">
            <SheetTitle className="text-base">Filtro WBS</SheetTitle>
          </SheetHeader>
          <div className="h-[calc(100%-57px)] overflow-y-auto p-3">
            <WBSFilterPanel
              nodes={wbsTree}
              selectedNodeId={selectedNodeId}
              onNodeSelect={(nodeId) => {
                setSelectedNodeId(nodeId);
              }}
              onClose={() => setSidebarOpen(false)}
              showAmounts={false}
            />
          </div>
        </SheetContent>
      </Sheet>
    </TablePage>
  );
}
