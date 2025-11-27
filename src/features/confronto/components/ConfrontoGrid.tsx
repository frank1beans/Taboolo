import React from "react";
import { ColDef, ColGroupDef } from "ag-grid-community";
import { DataTable, type ColumnAggregation } from "@/components/DataTable";
import { formatCurrency, getGridThemeClass } from "@/lib/grid-utils";
import { ConfrontoRow } from "../types";

interface ConfrontoGridProps {
    rowData: ConfrontoRow[];
    columnDefs: (ColDef<ConfrontoRow> | ColGroupDef<ConfrontoRow>)[];
    isLoading: boolean;
    isDarkMode: boolean;
    commessaId: string;
    onExcelExport: () => void;
}

export function ConfrontoGrid({
    rowData,
    columnDefs,
    isLoading,
    isDarkMode,
    commessaId,
    onExcelExport,
}: ConfrontoGridProps) {
    const aggregations: ColumnAggregation[] = [
        {
            field: "importoTotaleProgetto",
            type: "sum",
            label: "Totale",
            formatter: (v) => formatCurrency(v),
        },
    ];

    return (
        <div className="flex flex-col gap-3 h-full">
            <DataTable<ConfrontoRow>
                data={rowData}
                columnDefs={columnDefs}
                height="70vh"
                headerHeight={72}
                enableSearch={true}
                enableExport={true}
                enableColumnToggle={true}
                exportFileName={`confronto-offerte-${commessaId}`}
                customExport={onExcelExport}

                getRowId={(params) => params.data.id}
                className={getGridThemeClass(isDarkMode)}
                aggregations={aggregations}
                showAggregationFooter={true}
                isLoading={isLoading}
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
    );
}
