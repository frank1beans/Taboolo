import { useEffect, useMemo, useState } from "react";
import { ColDef, ColGroupDef } from "ag-grid-community";
import { DataTable, type ColumnAggregation } from "@/components/DataTable";
import { useConfrontoData } from "@/hooks/useConfrontoData";
import { formatCurrency, getGridThemeClass } from "@/lib/grid-utils";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { FrontendWbsNode } from "@/types/api";
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
import { useTheme } from "next-themes";

interface ConfrontoOfferteProps {
  commessaId: string;
  selectedRound?: number | "all";
  selectedImpresa?: string;
  onRoundChange?: (round: number | "all") => void;
  onImpresaChange?: (impresa: string | undefined) => void;
  onNavigateToCharts?: () => void;
}

interface ConfrontoRow {
  id: string;
  codice: string;
  descrizione: string;
  descrizione_estesa?: string | null;
  um: string;
  quantita: number;
  prezzoUnitarioProgetto: number;
  importoTotaleProgetto: number;
  wbs6Code?: string | null;
  wbs6Description?: string | null;
  wbs7Code?: string | null;
  wbs7Description?: string | null;
  [key: string]: any;
}

type ImpresaView = {
  nomeImpresa: string;
  roundNumber: number | null;
  roundLabel: string | null;
  impresaOriginale: string | null;
  normalizedLabel: string | null;
};

type OffertaRecord = {
  quantita?: number;
  prezzoUnitario?: number;
  importoTotale?: number;
  criticita?: string;
  note?: string;
};

const slugifyFieldId = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .toLowerCase() || "impresa";

const getImpresaFieldPrefix = (impresa: ImpresaView) => {
  const base =
    impresa.roundNumber != null
      ? `${impresa.nomeImpresa}_round_${impresa.roundNumber}`
      : impresa.nomeImpresa;
  return slugifyFieldId(base ?? `impresa_${impresa.roundNumber ?? "all"}`);
};

const getImpresaHeaderLabel = (impresa: ImpresaView) => {
  if (impresa.roundNumber != null) {
    const roundLabel = impresa.roundLabel ?? `Round ${impresa.roundNumber}`;
    return `${impresa.nomeImpresa} - ${roundLabel}`;
  }
  return impresa.nomeImpresa;
};

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
  } = useConfrontoData(commessaId);

  const { data: wbsDataRaw } = useQuery({
    queryKey: ["commesse", commessaId, "wbs", "structure"],
    queryFn: () => api.getCommessaWbsStructure(commessaId),
    enabled: !!commessaId,
  });

  const wbsData = useMemo<FrontendWbsNode[]>(() => {
    if (!wbsDataRaw?.wbs6) return [];
    return wbsDataRaw.wbs6.map(node => ({
      id: String(node.id),
      code: node.code || "",
      description: node.description || "",
      level: 6,
      importo: 0,
      children: [],
      path: []
    }));
  }, [wbsDataRaw]);

  const [selectedWbsNodeId, setSelectedWbsNodeId] = useState<string | null>(null);

  const roundOptions = useMemo(() => confrontoData?.rounds ?? [], [confrontoData?.rounds]);

  const filteredImprese = useMemo<ImpresaView[]>(() => {
    const list = (confrontoData?.imprese ?? []) as ImpresaView[];
    if (effectiveRound === "all") return list;
    return list.filter((imp) => imp.roundNumber === effectiveRound);
  }, [confrontoData?.imprese, effectiveRound]);

  const handleRoundSelect = (round: "all" | number) => {
    if (!isRoundControlled) {
      setInternalRound(round);
    }
    onRoundChange?.(round);
  };

  const rowData = useMemo<ConfrontoRow[]>(() => {
    if (!confrontoData?.voci) return [];

    return confrontoData.voci.map((voce, index) => {
      const offerteByLabel: Record<string, OffertaRecord> = voce.offerte ?? {};
      const normalizedOffers = new Map<string, OffertaRecord>();
      Object.entries(offerteByLabel).forEach(([label, offerta]) => {
        normalizedOffers.set(label.trim().toLowerCase(), offerta);
      });

      const resolveOfferta = (impresa: ImpresaView) => {
        const candidates = new Set<string>();
        const addBaseLabel = (base?: string | null) => {
          if (!base) return;
          const trimmed = base.trim();
          if (!trimmed) return;
          candidates.add(trimmed);
          if (impresa.roundNumber != null) {
            candidates.add(`${trimmed} (Round ${impresa.roundNumber})`);
            candidates.add(`${trimmed} Round ${impresa.roundNumber}`);
            candidates.add(`${trimmed} - Round ${impresa.roundNumber}`);
          }
          if (impresa.roundLabel) {
            candidates.add(`${trimmed} (${impresa.roundLabel})`);
            candidates.add(`${trimmed} - ${impresa.roundLabel}`);
          }
        };

        addBaseLabel(impresa.nomeImpresa);
        addBaseLabel(impresa.impresaOriginale);
        addBaseLabel(impresa.normalizedLabel);

        const normalizedCandidates = Array.from(candidates)
          .map((candidate) => candidate.toLowerCase())
          .filter((candidate) => candidate.length > 0);

        for (const candidate of normalizedCandidates) {
          const match = normalizedOffers.get(candidate);
          if (match) return match;
        }

        for (const [label, offerta] of Object.entries(offerteByLabel)) {
          const normalizedLabel = label.trim().toLowerCase();
          if (
            normalizedCandidates.some(
              (candidate) =>
                normalizedLabel.includes(candidate) || candidate.includes(normalizedLabel),
            )
          ) {
            return offerta;
          }
        }

        return null;
      };

      const row: ConfrontoRow = {
        id: `${voce.codice}-${index}`,
        codice: voce.codice,
        descrizione: voce.descrizione,
        descrizione_estesa: voce.descrizione_estesa,
        um: voce.um,
        quantita: voce.quantita,
        prezzoUnitarioProgetto: voce.prezzoUnitarioProgetto,
        importoTotaleProgetto: voce.importoTotaleProgetto,
        wbs6Code: voce.wbs6Code,
        wbs6Description: voce.wbs6Description,
        wbs7Code: voce.wbs7Code,
        wbs7Description: voce.wbs7Description,
      };

      const prezziVisibili: number[] = [];
      const offerCache = new Map<string, OffertaRecord | null>();

      filteredImprese.forEach((impresa) => {
        const fieldPrefix = getImpresaFieldPrefix(impresa);
        const offerta = resolveOfferta(impresa);
        offerCache.set(fieldPrefix, offerta);

        if (offerta && typeof offerta.prezzoUnitario === "number") {
          row[`${fieldPrefix}_prezzoUnitario`] = offerta.prezzoUnitario;
          prezziVisibili.push(offerta.prezzoUnitario);
        } else {
          row[`${fieldPrefix}_prezzoUnitario`] = null;
        }

        row[`${fieldPrefix}_importoTotale`] =
          offerta && typeof offerta.importoTotale === "number" ? offerta.importoTotale : null;

        if (offerta && offerta.prezzoUnitario != null && voce.prezzoUnitarioProgetto) {
          row[`${fieldPrefix}_deltaPerc`] =
            ((offerta.prezzoUnitario - voce.prezzoUnitarioProgetto) /
              voce.prezzoUnitarioProgetto) *
            100;
        } else {
          row[`${fieldPrefix}_deltaPerc`] = null;
        }
      });

      if (prezziVisibili.length) {
        const somma = prezziVisibili.reduce((acc, curr) => acc + curr, 0);
        const media = somma / prezziVisibili.length;
        const minimo = Math.min(...prezziVisibili);
        const massimo = Math.max(...prezziVisibili);
        const deviazione =
          prezziVisibili.length > 1
            ? Math.sqrt(
                prezziVisibili.reduce((acc, curr) => acc + Math.pow(curr - media, 2), 0) /
                  prezziVisibili.length,
              )
            : 0;
        row.mediaPrezzi = media;
        row.minimoPrezzi = minimo;
        row.massimoPrezzi = massimo;
        row.deviazionePrezzi = deviazione;

        filteredImprese.forEach((impresa) => {
          const fieldPrefix = getImpresaFieldPrefix(impresa);
          const offerta = offerCache.get(fieldPrefix);
          if (!offerta || offerta.prezzoUnitario == null || Math.abs(media) < 1e-9) {
            row[`${fieldPrefix}_deltaMedia`] = null;
            return;
          }
          row[`${fieldPrefix}_deltaMedia`] = ((offerta.prezzoUnitario - media) / media) * 100;
        });
      } else {
        row.mediaPrezzi = null;
        row.minimoPrezzi = null;
        row.massimoPrezzi = null;
        row.deviazionePrezzi = null;
        filteredImprese.forEach((impresa) => {
          const fieldPrefix = getImpresaFieldPrefix(impresa);
          row[`${fieldPrefix}_deltaMedia`] = null;
        });
      }

      return row;
    });
  }, [confrontoData?.voci, filteredImprese]);

  const filteredRowData = useMemo(() => {
    if (!selectedWbsNodeId) return rowData;

    return rowData.filter((row) => {
      const wbs6Match = row.wbs6Code === selectedWbsNodeId;
      const wbs7Match = row.wbs7Code === selectedWbsNodeId;
      return wbs6Match || wbs7Match;
    });
  }, [rowData, selectedWbsNodeId]);

  const exportColumns = useMemo(() => {
    const baseExportCols = [
      { header: "Codice", field: "codice" },
      { header: "Descrizione", field: "descrizione" },
      { header: "UM", field: "um" },
      { header: "Quantita", field: "quantita", valueFormatter: (row: ConfrontoRow) => row.quantita?.toFixed(2) },
      { header: "P.U. Progetto", field: "prezzoUnitarioProgetto", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.prezzoUnitarioProgetto) },
      { header: "Importo Progetto", field: "importoTotaleProgetto", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.importoTotaleProgetto) },
      { header: "Media offerte", field: "mediaPrezzi", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.mediaPrezzi ?? null) },
      { header: "Prezzo minimo", field: "minimoPrezzi", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.minimoPrezzi ?? null) },
      { header: "Prezzo massimo", field: "massimoPrezzi", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.massimoPrezzi ?? null) },
      { header: "Deviazione std.", field: "deviazionePrezzi", valueFormatter: (row: ConfrontoRow) => formatCurrency(row.deviazionePrezzi ?? null) },
    ];

    filteredImprese.forEach((impresa) => {
      const fieldPrefix = getImpresaFieldPrefix(impresa);
      const headerLabel = getImpresaHeaderLabel(impresa);
      baseExportCols.push(
        {
          header: `${headerLabel} - P.U.`,
          field: `${fieldPrefix}_prezzoUnitario`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_prezzoUnitario`];
            return val != null ? formatCurrency(val) : "-";
          },
        },
        {
          header: `${headerLabel} - Importo`,
          field: `${fieldPrefix}_importoTotale`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_importoTotale`];
            return val != null ? formatCurrency(val) : "-";
          },
        },
        {
          header: `${headerLabel} - Î” progetto`,
          field: `${fieldPrefix}_deltaPerc`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_deltaPerc`];
            return val != null ? `${val >= 0 ? "+" : ""}${val.toFixed(2)}%` : "-";
          },
        },
        {
          header: `${headerLabel} - Î” media`,
          field: `${fieldPrefix}_deltaMedia`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_deltaMedia`];
            return val != null ? `${val >= 0 ? "+" : ""}${val.toFixed(2)}%` : "-";
          },
        },
      );
    });

    return baseExportCols;
  }, [filteredImprese]);

  const columnDefs = useMemo<(ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[]>(() => {
    const baseColumns: ColDef<ConfrontoRow>[] = [
      {
        field: "codice",
        headerName: "Codice",
        width: 120,
        pinned: "left",
        filter: "agTextColumnFilter",
      },
      {
        field: "descrizione",
        headerName: "Descrizione",
        width: 300,
        pinned: "left",
        filter: "agTextColumnFilter",
        tooltipField: "descrizione_estesa",
        valueGetter: (params) => params.data?.descrizione_estesa || params.data?.descrizione,
        autoHeight: true,
        wrapText: true,
      },
      {
        field: "um",
        headerName: "UM",
        width: 80,
        filter: "agTextColumnFilter",
      },
      {
        field: "quantita",
        headerName: "Quantita",
        width: 110,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? params.value.toFixed(2) : "-"),
      },
      {
        field: "prezzoUnitarioProgetto",
        headerName: "P.U. Progetto",
        width: 130,
        type: "numericColumn",
        valueFormatter: (params) => formatCurrency(params.value),
        cellStyle: { fontWeight: "500" },
      },
      {
        field: "importoTotaleProgetto",
        headerName: "Importo Progetto",
        width: 150,
        type: "numericColumn",
        valueFormatter: (params) => formatCurrency(params.value),
        cellStyle: { fontWeight: "500" },
      },
      {
        field: "mediaPrezzi",
        headerName: "Media offerte (round)",
        width: 170,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellStyle: { backgroundColor: isDarkMode ? "#0f172a" : "#f8fafc", fontWeight: "500" },
      },
      {
        field: "minimoPrezzi",
        headerName: "Prezzo minimo",
        width: 140,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
      },
      {
        field: "massimoPrezzi",
        headerName: "Prezzo massimo",
        width: 140,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
      },
      {
        field: "deviazionePrezzi",
        headerName: "Deviazione std.",
        width: 150,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
      },
    ];

    const palette = [
      { bg: isDarkMode ? "#111827" : "#f6f8fb", border: isDarkMode ? "#1f2937" : "#e2e8f0" },
      { bg: isDarkMode ? "#1b2a3a" : "#eef2ff", border: isDarkMode ? "#334155" : "#c7d2fe" },
      { bg: isDarkMode ? "#1f2d24" : "#ecfdf3", border: isDarkMode ? "#2f3e33" : "#cde5d8" },
      { bg: isDarkMode ? "#2a1f30" : "#fdf2f8", border: isDarkMode ? "#3b2f3f" : "#f5d0e6" },
      { bg: isDarkMode ? "#202331" : "#f8fafc", border: isDarkMode ? "#2f3240" : "#e2e8f0" },
    ];

    const groupedColumns: ColGroupDef<ConfrontoRow>[] = filteredImprese.map((impresa, index) => {
      const color = palette[index % palette.length];
      const fieldPrefix = getImpresaFieldPrefix(impresa);
      const headerLabel = getImpresaHeaderLabel(impresa);

      const deltaCellStyle = (params: any) => {
        if (params.value == null) return { backgroundColor: color.bg };
        const val = params.value as number;
        return {
          backgroundColor: color.bg,
          borderRight: `1px solid ${color.border}`,
          color:
            val > 0
              ? isDarkMode
                ? "#ef4444"
                : "#dc2626"
              : val < 0
                ? isDarkMode
                  ? "#22c55e"
                  : "#16a34a"
                : undefined,
          fontWeight: "500",
        };
      };

      return {
        headerName: headerLabel,
        marryChildren: true,
        headerClass: "text-[11px] uppercase tracking-wide text-muted-foreground",
        children: [
          {
            headerName: "P.U.",
            field: `${fieldPrefix}_prezzoUnitario`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: {
              backgroundColor: color.bg,
              borderLeft: `1px solid ${color.border}`,
            },
          },
          {
            headerName: "Importo",
            field: `${fieldPrefix}_importoTotale`,
            width: 140,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: {
              backgroundColor: color.bg,
            },
          },
          {
            headerName: "Delta progetto",
            field: `${fieldPrefix}_deltaPerc`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) => {
              if (params.value == null) return "-";
              const val = params.value as number;
              return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
            },
            cellStyle: deltaCellStyle,
          },
          {
            headerName: "Delta media",
            field: `${fieldPrefix}_deltaMedia`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) => {
              if (params.value == null) return "-";
              const val = params.value as number;
              return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
            },
            cellStyle: deltaCellStyle,
          },
        ],
      };
    });

    return [...baseColumns, ...groupedColumns];
  }, [filteredImprese, isDarkMode]);

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
    ...(selectedWbsNodeId
      ? [{
          id: "wbs",
          label: "WBS",
          value: selectedWbsNodeId,
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

  // Aggregations for footer
  const aggregations: ColumnAggregation[] = [
    {
      field: "importoTotaleProgetto",
      type: "sum",
      label: "Totale",
      formatter: (v) => formatCurrency(v),
    },
  ];

  return (
    <TablePage
      title="Confronto Offerte"
      description="Analisi comparativa prezzi unitari tra imprese per round"
      stats={tableStats}
      activeFilters={activeFiltersArray}
      onClearAllFilters={() => {
        setSelectedWbsNodeId(null);
        handleRoundSelect("all");
      }}
      filters={
        roundFilters.length > 0 ? (
          <QuickFilters filters={roundFilters} />
        ) : undefined
      }
      actions={
        <div className="flex items-center gap-2">
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
      }
      className="h-full"
    >
        <DataTable
          data={filteredRowData}
          columnDefs={columnDefs}
          height="70vh"
          headerHeight={72}
          enableSearch={true}
          enableExport={true}
          enableColumnToggle={true}
          exportFileName={`confronto-offerte-${commessaId}`}
          exportColumns={exportColumns}
          getRowId={(params) => params.data.id}
          className={getGridThemeClass(isDarkMode)}
          aggregations={aggregations}
          showAggregationFooter={true}
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
















