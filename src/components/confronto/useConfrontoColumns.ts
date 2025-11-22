/**
 * Hook per generare le colonne del confronto offerte
 */

import { useMemo } from "react";
import { ColDef, ColGroupDef } from "ag-grid-community";
import { formatCurrency } from "@/lib/grid-utils";
import {
  ConfrontoRow,
  ImpresaView,
  getImpresaFieldPrefix,
  getImpresaHeaderLabel,
  getColorForIndex,
} from "./confrontoUtils";

interface UseConfrontoColumnsOptions {
  filteredImprese: ImpresaView[];
  isDarkMode: boolean;
}

export function useConfrontoColumns({
  filteredImprese,
  isDarkMode,
}: UseConfrontoColumnsOptions): (ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[] {
  return useMemo(() => {
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
        cellStyle: { fontWeight: "600" },
      },
      {
        field: "importoTotaleProgetto",
        headerName: "Importo Progetto",
        width: 150,
        type: "numericColumn",
        valueFormatter: (params) => formatCurrency(params.value),
        cellStyle: { fontWeight: "600" },
      },
      {
        field: "mediaPrezzi",
        headerName: "Media offerte (round)",
        width: 170,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
        cellStyle: { backgroundColor: isDarkMode ? "#0f172a" : "#f8fafc" },
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

    const groupedColumns: ColGroupDef<ConfrontoRow>[] = filteredImprese.map((impresa, index) => {
      const color = getColorForIndex(index, isDarkMode);
      const fieldPrefix = getImpresaFieldPrefix(impresa);
      const headerLabel = getImpresaHeaderLabel(impresa);

      const deltaCellStyle = (params: any) => {
        if (params.value == null) return { backgroundColor: color.bg };
        const val = params.value as number;
        return {
          backgroundColor: color.bg,
          borderRight: `2px solid ${color.border}`,
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
          fontWeight: "600",
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
              borderLeft: `2px solid ${color.border}`,
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
}
