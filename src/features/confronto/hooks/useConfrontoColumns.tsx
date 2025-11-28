/**
 * Hook per generare le colonne del confronto offerte
 */

import { useMemo } from "react";
import { ColDef, ColGroupDef } from "ag-grid-community";
import { formatCurrency } from "@/lib/grid-utils";
import {
  getImpresaFieldPrefix,
  getImpresaHeaderLabel,
  getColorForIndex,
} from "../utils";
import { ConfrontoRow, ImpresaView } from "../types";

interface UseConfrontoColumnsOptions {
  filteredImprese: ImpresaView[];
  isDarkMode: boolean;
}

export function useConfrontoColumns({
  filteredImprese,
  isDarkMode,
}: UseConfrontoColumnsOptions): (ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[] {
  return useMemo(() => {
    const baseColumns: (ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[] = [
      {
        headerName: "Dati Progetto",
        headerClass: "text-[11px] uppercase tracking-wide text-muted-foreground bg-muted/30",
        children: [
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
            width: 70,
            filter: "agTextColumnFilter",
          },
          {
            field: "quantita",
            headerName: "Q.tà",
            width: 90,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? params.value.toFixed(2) : "-"),
          },
          {
            field: "prezzoUnitarioProgetto",
            headerName: "P.U.",
            width: 110,
            type: "numericColumn",
            valueFormatter: (params) => formatCurrency(params.value),
            cellStyle: { fontWeight: "600" },
          },
          {
            field: "importoTotaleProgetto",
            headerName: "Importo",
            width: 130,
            type: "numericColumn",
            valueFormatter: (params) => formatCurrency(params.value),
            cellStyle: { fontWeight: "600", borderRight: "2px solid rgba(0,0,0,0.1)" },
          },
        ]
      },
      {
        headerName: "Statistiche",
        headerClass: "text-[11px] uppercase tracking-wide text-muted-foreground bg-muted/30",
        children: [
          {
            field: "mediaPrezzi",
            headerName: "Media",
            width: 110,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: { backgroundColor: isDarkMode ? "#0f172a" : "#f8fafc", fontStyle: "italic" },
          },
          {
            field: "minimoPrezzi",
            headerName: "Min",
            width: 100,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: { color: isDarkMode ? "#22c55e" : "#16a34a", fontWeight: "500" },
          },
          {
            field: "massimoPrezzi",
            headerName: "Max",
            width: 100,
            type: "numericColumn",
            valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
            cellStyle: { color: isDarkMode ? "#ef4444" : "#dc2626", fontWeight: "500" },
          },
        ]
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
            cellRenderer: (params: any) => {
              if (params.value == null) return "-";
              const val = formatCurrency(params.value);

              let badge = null;
              if (params.data) {
                const isMin = params.data.minimoPrezzi != null && Math.abs(params.value - params.data.minimoPrezzi) < 0.001;
                const isMax = params.data.massimoPrezzi != null && Math.abs(params.value - params.data.massimoPrezzi) < 0.001;

                if (isMin) {
                  badge = (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        backgroundColor: isDarkMode ? "rgba(20, 83, 45, 0.3)" : "#dcfce7",
                        color: isDarkMode ? "#22c55e" : "#16a34a",
                        fontSize: "10px",
                        fontWeight: "bold",
                        marginLeft: "4px",
                      }}
                      title="Prezzo minimo"
                    >
                      ★
                    </span>
                  );
                } else if (isMax) {
                  badge = (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        backgroundColor: isDarkMode ? "rgba(127, 29, 29, 0.3)" : "#fee2e2",
                        color: isDarkMode ? "#ef4444" : "#dc2626",
                        fontSize: "10px",
                        fontWeight: "bold",
                        marginLeft: "4px",
                      }}
                      title="Prezzo massimo"
                    >
                      ▲
                    </span>
                  );
                }
              }

              return (
                <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end" }}>
                  <span>{val}</span>
                  {badge}
                </div>
              );
            },
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
            cellRenderer: (params: any) => {
              const val = params.value != null ? formatCurrency(params.value) : "-";
              const mismatch = params.data && params.data[`${fieldPrefix}_quantityMismatch`];
              if (mismatch) {
                return (
                  <div className="flex justify-between items-center w-full">
                    <span>{val}</span>
                    <span
                      title={`Quantità diversa dal progetto: ${params.data[`${fieldPrefix}_quantita`]}`}
                      className="text-yellow-500 font-bold cursor-help"
                    >
                      ⚠️
                    </span>
                  </div>
                );
              }
              return val;
            },
          },
          {
            headerName: "Delta progetto",
            field: `${fieldPrefix}_deltaPerc`,
            width: 120,
            type: "numericColumn",
            cellRenderer: (params: any) => {
              if (params.value == null) return "-";
              const val = params.value as number;
              const isPositive = val > 0; // Worse (higher price)
              const isNegative = val < 0; // Better (lower price)

              // Colors
              const color = isPositive
                ? (isDarkMode ? "#fca5a5" : "#b91c1c")
                : isNegative
                  ? (isDarkMode ? "#86efac" : "#15803d")
                  : (isDarkMode ? "#94a3b8" : "#64748b");

              const bg = isPositive
                ? (isDarkMode ? "rgba(127, 29, 29, 0.2)" : "#fef2f2")
                : isNegative
                  ? (isDarkMode ? "rgba(20, 83, 45, 0.2)" : "#f0fdf4")
                  : "transparent";

              const border = isPositive
                ? (isDarkMode ? "rgba(248, 113, 113, 0.3)" : "#fecaca")
                : isNegative
                  ? (isDarkMode ? "rgba(74, 222, 128, 0.3)" : "#bbf7d0")
                  : "transparent";

              const arrow = isPositive ? "↑" : isNegative ? "↓" : "";
              const text = `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;

              return (
                <div style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  gap: "4px",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  backgroundColor: bg,
                  color: color,
                  border: `1px solid ${border}`,
                  fontWeight: 600,
                  fontSize: "11px",
                  width: "100%",
                }}>
                  <span>{arrow}</span>
                  <span>{text}</span>
                </div>
              );
            },
            cellStyle: {
              backgroundColor: color.bg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              padding: '4px'
            },
          },
          {
            headerName: "Delta media",
            field: `${fieldPrefix}_deltaMedia`,
            width: 120,
            type: "numericColumn",
            cellRenderer: (params: any) => {
              if (params.value == null) return "-";
              const val = params.value as number;
              const isPositive = val > 0;
              const isNegative = val < 0;

              const color = isPositive
                ? (isDarkMode ? "#fca5a5" : "#b91c1c")
                : isNegative
                  ? (isDarkMode ? "#86efac" : "#15803d")
                  : (isDarkMode ? "#94a3b8" : "#64748b");

              const bg = isPositive
                ? (isDarkMode ? "rgba(127, 29, 29, 0.2)" : "#fef2f2")
                : isNegative
                  ? (isDarkMode ? "rgba(20, 83, 45, 0.2)" : "#f0fdf4")
                  : "transparent";

              const border = isPositive
                ? (isDarkMode ? "rgba(248, 113, 113, 0.3)" : "#fecaca")
                : isNegative
                  ? (isDarkMode ? "rgba(74, 222, 128, 0.3)" : "#bbf7d0")
                  : "transparent";

              const arrow = isPositive ? "↑" : isNegative ? "↓" : "";
              const text = `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;

              return (
                <div style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  gap: "4px",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  backgroundColor: bg,
                  color: color,
                  border: `1px solid ${border}`,
                  fontWeight: 600,
                  fontSize: "11px",
                  width: "100%",
                }}>
                  <span>{arrow}</span>
                  <span>{text}</span>
                </div>
              );
            },
            cellStyle: {
              backgroundColor: color.bg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              padding: '4px',
              borderRight: `2px solid ${color.border}`
            },
          },
        ],
      };
    });

    return [...baseColumns, ...groupedColumns];
  }, [filteredImprese, isDarkMode]);
}
