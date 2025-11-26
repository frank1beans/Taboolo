import { useEffect, useMemo, useState } from "react";
import { useCallback } from "react";
import { ColDef, ColGroupDef } from "ag-grid-community";
import { DataTable, type ColumnAggregation } from "@/components/DataTable";
import { useConfrontoData } from "@/hooks/useConfrontoData";
import { formatCurrency, getGridThemeClass } from "@/lib/grid-utils";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ApiWbs7Node, FrontendWbsNode } from "@/types/api";
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
import React from "react";

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
  hasQuantityMismatch?: boolean;
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
  deltaQuantita?: number | null;
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

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

const getDeltaVisual = (val: number | null | undefined) => {
  if (val == null) {
    return { text: "–", bg: undefined, color: undefined, icon: "" };
  }
  const abs = clamp(Math.abs(val), 0, 100);
  const opacity = 0.12 + abs / 900; // più visibile
  // Riferimento: progetto. Più alto = peggio (rosso), più basso = meglio (verde).
  const isGood = val < 0;
  const bg = isGood
    ? `rgba(34,197,94,${opacity})`
    : val > 0
      ? `rgba(239,68,68,${opacity})`
      : `rgba(148,163,184,0.2)`;
  const color = isGood ? "#166534" : val > 0 ? "#b91c1c" : "#475569";
  const icon = isGood ? "↓" : val > 0 ? "↑" : "•";
  const text = `${val > 0 ? "+" : ""}${val.toFixed(2)}%`;
  return { text, bg, color, icon };
};

const getHeatmapBg = (delta: number | null | undefined, baseBg: string) => {
  if (delta == null) return baseBg;
  const abs = clamp(Math.abs(delta), 0, 80);
  const tint = 0.1 + abs / 500; // intensità leggermente più alta
  return delta > 0
    ? `rgba(239,68,68,${tint})`
    : delta < 0
      ? `rgba(34,197,94,${tint})`
      : baseBg;
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
  } = useConfrontoData(commessaId);

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
      let hasQuantityMismatch = false;

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
        row[`${fieldPrefix}_quantita`] =
          offerta && typeof offerta.quantita === "number" ? offerta.quantita : null;
        row[`${fieldPrefix}_deltaQuantita`] =
          offerta && typeof offerta.deltaQuantita === "number" ? offerta.deltaQuantita : null;

        if (offerta && offerta.prezzoUnitario != null && voce.prezzoUnitarioProgetto) {
          row[`${fieldPrefix}_deltaPerc`] =
            ((offerta.prezzoUnitario - voce.prezzoUnitarioProgetto) /
              voce.prezzoUnitarioProgetto) *
            100;
        } else {
          row[`${fieldPrefix}_deltaPerc`] = null;
        }

        if (
          offerta &&
          typeof offerta.deltaQuantita === "number" &&
          Math.abs(offerta.deltaQuantita) > 1e-6
        ) {
          hasQuantityMismatch = true;
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

      row.hasQuantityMismatch = hasQuantityMismatch;
      return row;
    });
  }, [confrontoData?.voci, filteredImprese]);

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
          header: `${headerLabel} - Q.tà`,
          field: `${fieldPrefix}_quantita`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_quantita`];
            return val != null ? Number(val).toFixed(2) : "-";
          },
        },
        {
          header: `${headerLabel} - Δ Q.tà`,
          field: `${fieldPrefix}_deltaQuantita`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_deltaQuantita`];
            if (val == null) return "-";
            return val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2);
          },
        },
        {
          header: `${headerLabel} - Δ progetto`,
          field: `${fieldPrefix}_deltaPerc`,
          valueFormatter: (row: ConfrontoRow) => {
            const val = row[`${fieldPrefix}_deltaPerc`];
            return val != null ? `${val >= 0 ? "+" : ""}${val.toFixed(2)}%` : "-";
          },
        },
        {
          header: `${headerLabel} - Δ media`,
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

  const excelStyles = useMemo(
    () => [
      {
        id: "excel-delta-good",
        interior: { color: "#d1fae5", pattern: "Solid" },
        font: { color: "#166534", bold: true },
        numberFormat: { format: "0.00%" },
      },
      {
        id: "excel-delta-bad",
        interior: { color: "#fee2e2", pattern: "Solid" },
        font: { color: "#b91c1c", bold: true },
        numberFormat: { format: "0.00%" },
      },
      {
        id: "excel-price-best",
        interior: { color: "#e8f5e9", pattern: "Solid" },
        borders: { borderBottom: { color: "#22c55e", lineStyle: "Continuous", weight: 2 } },
        numberFormat: { format: '€#,##0.00' },
      },
      {
        id: "excel-price-worst",
        interior: { color: "#ffebee", pattern: "Solid" },
        borders: { borderBottom: { color: "#ef4444", lineStyle: "Continuous", weight: 2 } },
        numberFormat: { format: '€#,##0.00' },
      },
      {
        id: "excel-currency",
        numberFormat: { format: '€#,##0.00' },
      },
    ],
    []
  );

  const excelProcessCell = useCallback((params: any) => {
    const val = params.value;
    if (val == null || val === "") return "";

    const colId = params.column?.getColId?.() ?? "";

    // Percentuali: converti in valore percentuale Excel (es. 12.3 => 0.123)
    if (colId.includes("delta")) {
      const num = typeof val === "number" ? val : Number(String(val).replace("%", "").replace(",", "."));
      if (Number.isFinite(num)) return num / 100;
      return val;
    }

    // Numeri/currency già numerici
    if (typeof val === "number") return val;

    const parsed = Number(String(val).replace(/[€\s]/g, "").replace(".", "").replace(",", "."));
    return Number.isFinite(parsed) ? parsed : val;
  }, []);

  const columnDefs = useMemo<(ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[]>(() => {
    const getRowPriceExtremes = (row: ConfrontoRow) => {
      let min = Number.POSITIVE_INFINITY;
      let max = Number.NEGATIVE_INFINITY;
      filteredImprese.forEach((impresa) => {
        const fieldPrefix = getImpresaFieldPrefix(impresa);
        const val = row?.[`${fieldPrefix}_prezzoUnitario`] as number | null;
        if (typeof val === "number" && Number.isFinite(val)) {
          min = Math.min(min, val);
          max = Math.max(max, val);
        }
      });
      return {
        min: min !== Number.POSITIVE_INFINITY ? min : null,
        max: max !== Number.NEGATIVE_INFINITY ? max : null,
      };
    };

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
        field: "quantity_alert",
        headerName: "Δ Quantità",
        width: 120,
        valueGetter: (params) => (params.data?.hasQuantityMismatch ? "Diff." : ""),
        cellRenderer: (params) => {
          const hasMismatch = params.data?.hasQuantityMismatch;
          if (!hasMismatch) return "";
          return (
            <span className="inline-flex items-center gap-1 font-semibold text-destructive">
              <span aria-hidden>▲▼</span>
              Diff.
            </span>
          );
        },
        cellClass: (params) =>
          params.data?.hasQuantityMismatch ? "text-destructive font-semibold" : "text-muted-foreground",
        tooltipValueGetter: (params) =>
          params.data?.hasQuantityMismatch
            ? "Quantità ritorno diversa dal progetto per almeno un'impresa"
            : "Quantità allineata",
      },
      {
        field: "prezzoUnitarioProgetto",
        headerName: "P.U. Progetto",
        width: 130,
        type: "numericColumn",
        valueFormatter: (params) => formatCurrency(params.value),
        cellStyle: { fontWeight: "500" },
        cellClass: "excel-currency",
      },
      {
        field: "importoTotaleProgetto",
        headerName: "Importo Progetto",
        width: 150,
        type: "numericColumn",
        valueFormatter: (params) => formatCurrency(params.value),
        cellStyle: { fontWeight: "500" },
        cellClass: "excel-currency",
      },
      {
        field: "mediaPrezzi",
        headerName: "Media offerte (round)",
        width: 170,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellStyle: { backgroundColor: isDarkMode ? "#0f172a" : "#f8fafc", fontWeight: "500" },
        cellClass: "excel-currency",
      },
      {
        field: "minimoPrezzi",
        headerName: "Prezzo minimo",
        width: 140,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellClass: "excel-currency",
      },
      {
        field: "massimoPrezzi",
        headerName: "Prezzo massimo",
        width: 140,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellClass: "excel-currency",
      },
      {
        field: "deviazionePrezzi",
        headerName: "Deviazione std.",
        width: 150,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellClass: "excel-currency",
      },
    ];

    const palette = [
      { bg: isDarkMode ? "#111827" : "#f6f8fb", border: isDarkMode ? "#1f2937" : "#e2e8f0" },
      { bg: isDarkMode ? "#1b2a3a" : "#eef2ff", border: isDarkMode ? "#334155" : "#c7d2fe" },
      { bg: isDarkMode ? "#1f2d24" : "#ecfdf3", border: isDarkMode ? "#2f3e33" : "#cde5d8" },
      { bg: isDarkMode ? "#2a1f30" : "#fdf2f8", border: isDarkMode ? "#3b2f3f" : "#f5d0e6" },
      { bg: isDarkMode ? "#202331" : "#f8fafc", border: isDarkMode ? "#2f3240" : "#e2e8f0" },
    ];

    const getRowExtremes = (row: ConfrontoRow) => {
      let minDelta = Number.POSITIVE_INFINITY;
      let maxDelta = Number.NEGATIVE_INFINITY;
      let minPrice = Number.POSITIVE_INFINITY;
      let maxPrice = Number.NEGATIVE_INFINITY;
      let deltaCount = 0;
      let priceCount = 0;

      filteredImprese.forEach((impresa) => {
        const prefix = getImpresaFieldPrefix(impresa);
        const delta = row?.[`${prefix}_deltaPerc`] as number | null;
        const price = row?.[`${prefix}_prezzoUnitario`] as number | null;
        if (typeof delta === "number" && Number.isFinite(delta)) {
          minDelta = Math.min(minDelta, delta);
          maxDelta = Math.max(maxDelta, delta);
          deltaCount += 1;
        }
        if (typeof price === "number" && Number.isFinite(price)) {
          minPrice = Math.min(minPrice, price);
          maxPrice = Math.max(maxPrice, price);
          priceCount += 1;
        }
      });

      return {
        minDelta: deltaCount > 0 ? minDelta : null,
        maxDelta: deltaCount > 0 ? maxDelta : null,
        minPrice: priceCount > 0 ? minPrice : null,
        maxPrice: priceCount > 0 ? maxPrice : null,
        deltaCount,
        priceCount,
      };
    };

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
            headerName: "Q.tà",
            field: `${fieldPrefix}_quantita`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) =>
              params.value != null ? Number(params.value).toFixed(2) : "-",
            cellStyle: {
              backgroundColor: color.bg,
              borderLeft: `1px solid ${color.border}`,
            },
          },
          {
            headerName: "Δ Q.tà",
            field: `${fieldPrefix}_deltaQuantita`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) => {
              if (params.value == null) return "-";
              const val = params.value as number;
              return val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2);
            },
            cellStyle: deltaCellStyle,
          },
          {
            headerName: "P.U.",
            field: `${fieldPrefix}_prezzoUnitario`,
            width: 120,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: (params) => {
              const delta = params.data?.[`${fieldPrefix}_deltaPerc`] as number | null;
              const { minDelta, maxDelta, minPrice, maxPrice, deltaCount, priceCount } = getRowExtremes(params.data);
              const val = params.value as number | null;
              // Best/Worst solo se ci sono almeno 2 offerte con delta; se no, si passa ai prezzi.
              const useDelta = deltaCount > 1;
              const usePrice = !useDelta && priceCount > 1;
              const isBest =
                (useDelta && minDelta != null && delta != null && delta === minDelta) ||
                (usePrice && minPrice != null && val != null && val === minPrice);
              const isWorst =
                (useDelta && maxDelta != null && delta != null && delta === maxDelta) ||
                (usePrice && maxPrice != null && val != null && val === maxPrice);
              return {
                backgroundColor: getHeatmapBg(delta, color.bg),
                border: isBest ? "2px solid #22c55e" : isWorst ? "2px solid #ef4444" : undefined,
                fontWeight: isBest || isWorst ? 700 : undefined,
              };
            },
            cellClass: (params) => {
              const classes: string[] = ["excel-currency"];
              const delta = params.data?.[`${fieldPrefix}_deltaPerc`] as number | null;
              const { minDelta, maxDelta, minPrice, maxPrice, deltaCount, priceCount } = getRowExtremes(params.data);
              const val = params.value as number | null;
              const useDelta = deltaCount > 1;
              const usePrice = !useDelta && priceCount > 1;
              const isBest =
                (useDelta && minDelta != null && delta != null && delta === minDelta) ||
                (usePrice && minPrice != null && val != null && val === minPrice);
              const isWorst =
                (useDelta && maxDelta != null && delta != null && delta === maxDelta) ||
                (usePrice && maxPrice != null && val != null && val === maxPrice);
              if (isBest) classes.push("excel-price-best");
              if (isWorst) classes.push("excel-price-worst");
              return classes;
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
            cellClass: "excel-currency",
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
            cellStyle: (params) => {
              const style = deltaCellStyle(params);
              const val = params.value as number | null;
              const visual = getDeltaVisual(val);
              return {
                ...style,
                backgroundColor: visual.bg ?? style.backgroundColor,
                color: visual.color ?? style.color,
                fontWeight: "700",
              };
            },
            cellRenderer: (params) => {
              const val = params.value as number | null;
              const visual = getDeltaVisual(val);
              return (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[11px]">
                  <span aria-hidden>{visual.icon}</span>
                  {visual.text}
                </span>
              );
            },
            cellClass: (params) => {
              const val = params.value as number | null;
              if (val == null) return [];
              if (val < 0) return ["excel-delta-good"];
              if (val > 0) return ["excel-delta-bad"];
              return [];
            },
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
            cellStyle: (params) => {
              const style = deltaCellStyle(params);
              const val = params.value as number | null;
              const visual = getDeltaVisual(val);
              return {
                ...style,
                backgroundColor: visual.bg ?? style.backgroundColor,
                color: visual.color ?? style.color,
                fontWeight: "700",
              };
            },
            cellRenderer: (params) => {
              const val = params.value as number | null;
              const visual = getDeltaVisual(val);
              return (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[11px]">
                  <span aria-hidden>{visual.icon}</span>
                  {visual.text}
                </span>
              );
            },
            cellClass: (params) => {
              const val = params.value as number | null;
              if (val == null) return [];
              if (val < 0) return ["excel-delta-good"];
              if (val > 0) return ["excel-delta-bad"];
              return [];
            },
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

  // Aggregations for footer
  const aggregations: ColumnAggregation[] = [
    {
      field: "importoTotaleProgetto",
      type: "sum",
      label: "Totale",
      formatter: (v) => formatCurrency(v),
    },
  ];

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
        <div className="flex flex-col gap-3">
          <DataTable
            data={filteredRowData}
            columnDefs={columnDefs}
            height="70vh"
            headerHeight={72}
            enableSearch={true}
            enableExport={true}
            enableColumnToggle={true}
            exportFileName={`confronto-offerte-${commessaId}`}
            excelStyles={excelStyles}
            excelProcessCell={excelProcessCell}
            excelSheetName="Confronto Offerte"
            getRowId={(params) => params.data.id}
            className={getGridThemeClass(isDarkMode)}
            aggregations={aggregations}
            showAggregationFooter={true}
          />

          <div className="text-xs text-muted-foreground flex flex-wrap gap-3 items-center">
            <span className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[rgba(34,197,94,0.5)] border border-green-600/60"></span>
              Offerta sotto progetto (meglio)
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[rgba(239,68,68,0.35)] border border-red-600/60"></span>
              Offerta sopra progetto (peggio)
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full border border-green-500"></span>
              Prezzo migliore nella voce
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full border border-red-500"></span>
              Prezzo peggiore nella voce
            </span>
            <span className="inline-flex items-center gap-1 font-semibold text-destructive">
              <span aria-hidden>▲▼</span>
              Δ Quantità diversa dal progetto
            </span>
          </div>
        </div>

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
















