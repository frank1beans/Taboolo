/**
 * Hook per generare le colonne di export del confronto offerte
 */

import { useMemo } from "react";
import { formatCurrency } from "@/lib/grid-utils";
import {
  getImpresaFieldPrefix,
  getImpresaHeaderLabel,
} from "../utils";
import { ConfrontoRow, ImpresaView } from "../types";

interface ExportColumn {
  header: string;
  field: string;
  valueFormatter?: (row: ConfrontoRow) => string;
}

interface UseConfrontoExportOptions {
  filteredImprese: ImpresaView[];
}

export function useConfrontoExport({ filteredImprese }: UseConfrontoExportOptions): ExportColumn[] {
  return useMemo(() => {
    const baseExportCols: ExportColumn[] = [
      { header: "Codice", field: "codice" },
      { header: "Descrizione", field: "descrizione" },
      { header: "UM", field: "um" },
      {
        header: "Quantita",
        field: "quantita",
        valueFormatter: (row: ConfrontoRow) => row.quantita?.toFixed(2),
      },
      {
        header: "P.U. Progetto",
        field: "prezzoUnitarioProgetto",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.prezzoUnitarioProgetto),
      },
      {
        header: "Importo Progetto",
        field: "importoTotaleProgetto",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.importoTotaleProgetto),
      },
      {
        header: "Media offerte",
        field: "mediaPrezzi",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.mediaPrezzi ?? null),
      },
      {
        header: "Prezzo minimo",
        field: "minimoPrezzi",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.minimoPrezzi ?? null),
      },
      {
        header: "Prezzo massimo",
        field: "massimoPrezzi",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.massimoPrezzi ?? null),
      },
      {
        header: "Deviazione std.",
        field: "deviazionePrezzi",
        valueFormatter: (row: ConfrontoRow) => formatCurrency(row.deviazionePrezzi ?? null),
      },
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
        }
      );
    });

    return baseExportCols;
  }, [filteredImprese]);
}
