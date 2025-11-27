import type {
  ColDef,
  ValueFormatterParams,
  GridOptions,
  ITooltipParams,
  CellStyle,
} from "ag-grid-community";
import { utils, writeFile } from "xlsx";
import type * as ExcelJSTypes from "exceljs";
import ExcelJS from "exceljs/dist/exceljs.min.js";

// ============= FORMATTERS =============

export const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return "€0,00";
  return `€${value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatNumber = (
  value: number | null | undefined,
  decimals: number = 2
): string => {
  if (value === null || value === undefined || isNaN(value)) return "0";
  return value.toLocaleString("it-IT", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatPercentage = (
  value: number | null | undefined,
  decimals: number = 2
): string => {
  if (value === null || value === undefined || isNaN(value)) return "0%";
  return `${value.toLocaleString("it-IT", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
};

// ============= VALUE FORMATTERS =============

export const currencyValueFormatter = (params: ValueFormatterParams): string => {
  return formatCurrency(params.value);
};

export const numberValueFormatter = (
  decimals: number = 2
) => (params: ValueFormatterParams): string => {
  return formatNumber(params.value, decimals);
};

export const percentageValueFormatter = (
  decimals: number = 2
) => (params: ValueFormatterParams): string => {
  return formatPercentage(params.value, decimals);
};

// ============= TOOLTIP =============

export const defaultTooltipValueGetter = (params: ITooltipParams): string => {
  return params.value ?? "";
};

// ============= CELL STYLES =============

export interface ColorTheme {
  bg: string;
  border: string;
  text: string;
}

export interface ImpresaColorTheme {
  light: ColorTheme;
  dark: ColorTheme;
}

export const IMPRESA_COLOR_PALETTE: Record<string, ImpresaColorTheme> = {
  blue: {
    light: { bg: "rgba(59,130,246,0.08)", border: "rgba(59,130,246,0.25)", text: "#1e3a8a" },
    dark: { bg: "rgba(59,130,246,0.18)", border: "rgba(147,197,253,0.35)", text: "#dbeafe" },
  },
  amber: {
    light: { bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.22)", text: "#92400e" },
    dark: { bg: "rgba(245,158,11,0.18)", border: "rgba(251,191,36,0.35)", text: "#fef3c7" },
  },
  green: {
    light: { bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.24)", text: "#065f46" },
    dark: { bg: "rgba(16,185,129,0.16)", border: "rgba(110,231,183,0.35)", text: "#d1fae5" },
  },
  purple: {
    light: { bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.24)", text: "#581c87" },
    dark: { bg: "rgba(168,85,247,0.18)", border: "rgba(196,181,253,0.35)", text: "#f3e8ff" },
  },
  rose: {
    light: { bg: "rgba(244,63,94,0.08)", border: "rgba(244,63,94,0.24)", text: "#9f1239" },
    dark: { bg: "rgba(244,63,94,0.18)", border: "rgba(251,207,232,0.35)", text: "#ffe4e6" },
  },
  cyan: {
    light: { bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.24)", text: "#164e63" },
    dark: { bg: "rgba(6,182,212,0.18)", border: "rgba(165,243,252,0.35)", text: "#cffafe" },
  },
  slate: {
    light: { bg: "rgba(100,116,139,0.08)", border: "rgba(100,116,139,0.20)", text: "#1e293b" },
    dark: { bg: "rgba(148,163,184,0.18)", border: "rgba(148,163,184,0.35)", text: "#e2e8f0" },
  },
};

const COLOR_KEYS = ["blue", "amber", "green", "purple", "rose", "cyan", "slate"];

export const getImpresaColor = (index: number): ImpresaColorTheme => {
  const key = COLOR_KEYS[index % COLOR_KEYS.length];
  return IMPRESA_COLOR_PALETTE[key];
};

export const createImpresaCellStyle = (
  theme: ImpresaColorTheme,
  isDarkMode: boolean
): CellStyle => {
  const colors = isDarkMode ? theme.dark : theme.light;
  return {
    backgroundColor: colors.bg,
    borderRight: `1px solid ${colors.border}`,
    borderLeft: `1px solid ${colors.border}`,
    color: colors.text,
  };
};

// ============= DELTA STYLES =============

export const getDeltaCellStyle = (
  value: number | null | undefined,
  isDarkMode: boolean
): CellStyle => {
  if (value === null || value === undefined) return {};

  if (value > 0) {
    return {
      color: isDarkMode ? "#fca5a5" : "#dc2626",
      fontWeight: "600",
    };
  } else if (value < 0) {
    return {
      color: isDarkMode ? "#86efac" : "#16a34a",
      fontWeight: "600",
    };
  }
  return {
    color: isDarkMode ? "#a1a1aa" : "#71717a",
    fontWeight: "500",
  };
};

// ============= COLUMN DEFINITIONS =============

export const BASE_COLUMN_DEFAULTS: Partial<ColDef> = {
  sortable: true,
  resizable: true,
  filter: true,
  floatingFilter: false,
  suppressMovable: true,
  tooltipValueGetter: defaultTooltipValueGetter,
};

export const createCodeColumn = (headerName: string = "Codice"): ColDef => ({
  field: "codice",
  headerName,
  width: 130,
  pinned: "left",
  lockPinned: true,
  cellClass: "font-mono text-xs font-semibold",
  headerClass: "font-semibold",
  ...BASE_COLUMN_DEFAULTS,
});

export const createDescriptionColumn = (
  headerName: string = "Descrizione"
): ColDef => ({
  field: "descrizione",
  headerName,
  width: 350,
  minWidth: 200,
  flex: 1,
  cellClass: "text-sm",
  headerClass: "font-semibold",
  wrapText: false,
  autoHeight: false,
  ...BASE_COLUMN_DEFAULTS,
});

export const createUnitColumn = (headerName: string = "U.M."): ColDef => ({
  field: "unita_misura",
  headerName,
  width: 80,
  cellClass: "text-center font-mono text-xs",
  headerClass: "text-center font-semibold",
  ...BASE_COLUMN_DEFAULTS,
});

export const createQuantityColumn = (headerName: string = "Quantità"): ColDef => ({
  field: "quantita",
  headerName,
  width: 110,
  type: "numericColumn",
  cellClass: "font-mono text-sm",
  headerClass: "text-right font-semibold",
  valueFormatter: numberValueFormatter(3),
  ...BASE_COLUMN_DEFAULTS,
});

export const createPriceColumn = (
  field: string,
  headerName: string
): ColDef => ({
  field,
  headerName,
  width: 120,
  type: "numericColumn",
  cellClass: "font-mono text-sm font-semibold",
  headerClass: "text-right font-semibold",
  valueFormatter: currencyValueFormatter,
  ...BASE_COLUMN_DEFAULTS,
});

export const createAmountColumn = (
  field: string,
  headerName: string
): ColDef => ({
  field,
  headerName,
  width: 130,
  type: "numericColumn",
  cellClass: "font-mono text-sm font-bold",
  headerClass: "text-right font-semibold",
  valueFormatter: currencyValueFormatter,
  ...BASE_COLUMN_DEFAULTS,
});

export const createDeltaColumn = (
  field: string,
  headerName: string,
  isDarkMode: boolean = false
): ColDef => ({
  field,
  headerName,
  width: 100,
  type: "numericColumn",
  cellClass: "font-mono text-sm",
  headerClass: "text-right font-semibold",
  valueFormatter: percentageValueFormatter(2),
  cellStyle: (params) => getDeltaCellStyle(params.value, isDarkMode),
  ...BASE_COLUMN_DEFAULTS,
});

// ============= WBS COLUMNS =============

export const createWbs6Column = (headerName: string = "WBS6"): ColDef => ({
  field: "wbs6_code",
  headerName,
  width: 100,
  cellClass: "font-mono text-xs",
  headerClass: "font-semibold",
  sortable: true,
  filter: true,
  ...BASE_COLUMN_DEFAULTS,
});

export const createWbs7Column = (headerName: string = "WBS7"): ColDef => ({
  field: "wbs7_code",
  headerName,
  width: 110,
  cellClass: "font-mono text-xs",
  headerClass: "font-semibold",
  sortable: true,
  filter: true,
  ...BASE_COLUMN_DEFAULTS,
});

export const createWbsColumns = (includeLevel7: boolean = true): ColDef[] => {
  const columns: ColDef[] = [createWbs6Column()];
  if (includeLevel7) {
    columns.push(createWbs7Column());
  }
  return columns;
};

// ============= ITEM COLUMNS (for price lists) =============

export const createItemCodeColumn = (
  headerName: string = "Codice",
  options?: { pinned?: boolean | "left" | "right"; width?: number }
): ColDef => ({
  field: "item_code",
  headerName,
  width: options?.width ?? 150,
  pinned: options?.pinned ?? "left",
  cellClass: "font-mono text-xs font-semibold",
  headerClass: "font-semibold",
  sortable: true,
  filter: true,
  ...BASE_COLUMN_DEFAULTS,
});

export const createItemDescriptionColumn = (
  headerName: string = "Descrizione",
  options?: { width?: number; truncateStart?: number; truncateEnd?: number }
): ColDef => ({
  field: "item_description",
  headerName,
  width: options?.width ?? 420,
  cellClass: "text-sm",
  headerClass: "font-semibold",
  sortable: true,
  filter: true,
  valueFormatter: (params) =>
    truncateMiddle(params.value, options?.truncateStart ?? 60, options?.truncateEnd ?? 60),
  tooltipValueGetter: (params) => params.value || "",
  ...BASE_COLUMN_DEFAULTS,
});

export const createUnitLabelColumn = (headerName: string = "U.M."): ColDef => ({
  field: "unit_label",
  headerName,
  width: 80,
  cellClass: "text-center font-mono text-xs",
  headerClass: "text-center font-semibold",
  ...BASE_COLUMN_DEFAULTS,
});

// ============= GENERIC COLUMN BUILDERS =============

export interface GenericColumnOptions {
  field: string;
  headerName: string;
  width?: number;
  type?: "text" | "numeric" | "currency" | "percentage";
  cellClass?: string;
  headerClass?: string;
  pinned?: boolean | "left" | "right";
  editable?: boolean;
}

export const createGenericColumn = (options: GenericColumnOptions): ColDef => {
  const base: ColDef = {
    field: options.field,
    headerName: options.headerName,
    width: options.width ?? 120,
    cellClass: options.cellClass ?? "text-sm",
    headerClass: options.headerClass ?? "font-semibold",
    pinned: options.pinned,
    editable: options.editable,
    ...BASE_COLUMN_DEFAULTS,
  };

  switch (options.type) {
    case "numeric":
      return {
        ...base,
        type: "numericColumn",
        cellClass: options.cellClass ?? "font-mono text-sm",
        headerClass: options.headerClass ?? "text-right font-semibold",
        valueFormatter: numberValueFormatter(2),
      };
    case "currency":
      return {
        ...base,
        type: "numericColumn",
        cellClass: options.cellClass ?? "font-mono text-sm font-semibold",
        headerClass: options.headerClass ?? "text-right font-semibold",
        valueFormatter: currencyValueFormatter,
      };
    case "percentage":
      return {
        ...base,
        type: "numericColumn",
        cellClass: options.cellClass ?? "font-mono text-sm",
        headerClass: options.headerClass ?? "text-right font-semibold",
        valueFormatter: percentageValueFormatter(2),
      };
    default:
      return base;
  }
};

// ============= GROUPED COLUMN BUILDER =============

export interface ColumnGroupOptions {
  headerName: string;
  headerClass?: string;
  children: ColDef[];
  marryChildren?: boolean;
}

export const createColumnGroup = (options: ColumnGroupOptions) => ({
  headerName: options.headerName,
  headerClass: options.headerClass ?? "font-semibold",
  marryChildren: options.marryChildren ?? true,
  children: options.children,
});

// ============= PROJECT PRICE COLUMNS =============

export const createProjectPriceColumns = (
  isDarkMode: boolean = false
): ColDef[] => [
  {
    field: "project_price",
    headerName: "Prezzo base",
    width: 160,
    type: "numericColumn",
    cellClass: "font-mono text-sm font-semibold text-blue-700 dark:text-blue-200",
    headerClass: "text-right font-bold",
    valueFormatter: currencyValueFormatter,
    ...BASE_COLUMN_DEFAULTS,
  },
  {
    field: "project_quantity",
    headerName: "Q.tà progetto",
    width: 150,
    type: "numericColumn",
    cellClass: "font-mono text-sm",
    headerClass: "text-right font-semibold",
    valueFormatter: (params) =>
      params.value != null ? Number(params.value).toLocaleString("it-IT") : "-",
    ...BASE_COLUMN_DEFAULTS,
  },
];

// ============= GRID OPTIONS =============

export const DEFAULT_GRID_OPTIONS: GridOptions = {
  defaultColDef: BASE_COLUMN_DEFAULTS,
  enableCellTextSelection: true,
  ensureDomOrder: true,
  animateRows: true,
  rowHeight: 32,
  headerHeight: 56,
  suppressCellFocus: true,
  suppressRowHoverHighlight: false,
  suppressColumnVirtualisation: false,
  suppressRowVirtualisation: false,
  enableBrowserTooltips: true,
  tooltipShowDelay: 500,
  pagination: false,
  domLayout: "normal",
};

// ============= EXCEL EXPORT =============

export interface ExcelExportColumn {
  header: string;
  field: string;
  valueFormatter?: (row: any) => any;
}

export const exportToExcel = (
  data: any[],
  columns: ExcelExportColumn[],
  fileName: string
): void => {
  const headers = columns.map((col) => col.header);

  const rows = data.map((row) =>
    columns.map((col) => {
      // If valueFormatter exists, pass the entire row
      if (col.valueFormatter) {
        return col.valueFormatter(row);
      }
      // Otherwise get the field value
      return row[col.field] ?? "";
    })
  );

  const worksheet = utils.aoa_to_sheet([headers, ...rows]);

  // Auto-size columns
  const maxWidths = columns.map((_, colIndex) => {
    const headerLength = headers[colIndex]?.length || 10;
    const maxDataLength = Math.max(
      ...rows.map((row) => {
        const cell = row[colIndex];
        return cell ? String(cell).length : 0;
      })
    );
    return Math.max(headerLength, maxDataLength, 10);
  });

  worksheet["!cols"] = maxWidths.map((width) => ({ wch: Math.min(width + 2, 50) }));

  const workbook = utils.book_new();
  utils.book_append_sheet(workbook, worksheet, "Elenco Prezzi");

  writeFile(workbook, `${fileName}.xlsx`);
};

// ============= THEME STYLES =============

export const GRID_THEME_CLASS = {
  light: "ag-theme-alpine",
  dark: "ag-theme-alpine-dark",
};

export const getGridThemeClass = (isDarkMode: boolean): string => {
  return isDarkMode ? GRID_THEME_CLASS.dark : GRID_THEME_CLASS.light;
};

// ============= UTILITY FUNCTIONS =============

export const getRowId = (params: { data: any }): string => {
  return params.data.id || params.data.codice || String(Math.random());
};

export const shortenDescription = (text: string | null | undefined, maxLength: number = 80): string => {
  if (!text) return "-";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
};

/**
 * Tronca una descrizione mostrando inizio e fine
 * @param text - Testo da troncare
 * @param startChars - Numero di caratteri dall'inizio (default 50)
 * @param endChars - Numero di caratteri dalla fine (default 50)
 * @returns Testo troncato nel formato "inizio...fine"
 */
export const truncateMiddle = (
  text: string | null | undefined,
  startChars: number = 50,
  endChars: number = 50
): string => {
  if (!text) return "-";

  const totalChars = startChars + endChars;
  if (text.length <= totalChars) return text;

  const start = text.slice(0, startChars);
  const end = text.slice(-endChars);

  return `${start}...${end}`;
};

// ============= EXCELJS EXPORT =============

export interface ExcelJSColumnConfig {
  header: string;
  field: string;
  width?: number;
  valueFormatter?: (row: any) => any;
  // Formula support: return a formula string like "=SUM(A2:A10)"
  formula?: (row: any, rowIndex: number) => string | null;
  // Styling
  style?: Partial<ExcelJSTypes.Style>;
  // Header styling (applied only to header cells)
  headerStyle?: Partial<ExcelJSTypes.Style>;
  // Cell-specific styling function (takes row data and returns style)
  cellStyle?: (row: any, rowIndex: number) => Partial<ExcelJSTypes.Style> | null;
  // Conditional formatting rules
  conditionalFormatting?: ConditionalFormattingRule[];
}

export interface ConditionalFormattingRule {
  type: "cellIs" | "expression" | "colorScale" | "dataBar";
  priority?: number;
  // For cellIs type
  operator?: "lessThan" | "greaterThan" | "equal" | "between" | "containsText";
  value?: any;
  value2?: any; // For "between" operator
  // For expression type
  formula?: string;
  // Styling to apply when condition is met
  style?: Partial<ExcelJSTypes.Style>;
  // For colorScale type
  colorScale?: {
    min?: { color: string };
    mid?: { color: string };
    max?: { color: string };
  };
  // For dataBar type
  dataBar?: {
    color: string;
    showValue?: boolean;
  };
}

export interface GlobalConditionalFormatting {
  range: string;
  rules: Array<{
    type: "expression" | "cellIs" | "colorScale" | "dataBar";
    formula?: string;
    operator?: "lessThan" | "greaterThan" | "equal" | "between" | "containsText";
    value?: any;
    value2?: any;
    style?: Partial<ExcelJSTypes.Style>;
    colorScale?: {
      min?: { color: { argb: string } };
      mid?: { color: { argb: string } };
      max?: { color: { argb: string } };
    };
  }>;
}

export interface ExcelJSExportOptions {
  fileName: string;
  sheetName?: string;
  columns: ExcelJSColumnConfig[];
  data: any[];
  // Global styles
  headerStyle?: Partial<ExcelJSTypes.Style>;
  dataStyle?: Partial<ExcelJSTypes.Style>;
  // Auto-filter
  enableAutoFilter?: boolean;
  // Freeze panes
  freezeRows?: number;
  freezeColumns?: number;
  // Global conditional formatting
  conditionalFormatting?: GlobalConditionalFormatting[];
}

/**
 * Esporta dati in Excel usando ExcelJS con supporto per formule e formattazione condizionale
 */
export const exportToExcelJS = async (options: ExcelJSExportOptions): Promise<void> => {
  const {
    fileName,
    sheetName = "Data",
    columns,
    data,
    headerStyle,
    dataStyle,
    enableAutoFilter = true,
    freezeRows = 1,
    freezeColumns = 0,
  } = options;

  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet(sheetName);

  // Define columns
  worksheet.columns = columns.map((col) => ({
    header: col.header,
    key: col.field,
    width: col.width ?? 15,
  }));

  // Style header row
  const defaultHeaderStyle: Partial<ExcelJSTypes.Style> = {
    font: { bold: true, size: 11 },
    fill: {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: "FFE9ECEF" },
    },
    alignment: { vertical: "middle", horizontal: "center" },
    border: {
      top: { style: "thin", color: { argb: "FFADB5BD" } },
      bottom: { style: "thin", color: { argb: "FFADB5BD" } },
      left: { style: "thin", color: { argb: "FFADB5BD" } },
      right: { style: "thin", color: { argb: "FFADB5BD" } },
    },
  };

  const headerRow = worksheet.getRow(1);
  headerRow.height = 25;
  headerRow.eachCell((cell, colNumber) => {
    const columnConfig = columns[colNumber - 1];
    // Apply column-specific header style if available, otherwise use default
    cell.style = {
      ...defaultHeaderStyle,
      ...headerStyle,
      ...columnConfig?.headerStyle
    };
  });

  // Add data rows
  data.forEach((row, rowIndex) => {
    const excelRow: any = {};

    columns.forEach((col) => {
      // Check if there's a formula in column config
      if (col.formula) {
        const formulaValue = col.formula(row, rowIndex + 2); // +2 because Excel is 1-indexed and row 1 is header
        if (formulaValue) {
          excelRow[col.field] = { formula: formulaValue };
          return;
        }
      }

      // Check if the data value itself is a formula object
      const fieldValue = row[col.field];
      if (fieldValue && typeof fieldValue === 'object' && 'formula' in fieldValue) {
        excelRow[col.field] = { formula: fieldValue.formula };
        return;
      }

      // Otherwise use value formatter or raw value
      if (col.valueFormatter) {
        excelRow[col.field] = col.valueFormatter(row);
      } else {
        excelRow[col.field] = fieldValue ?? "";
      }
    });

    const addedRow = worksheet.addRow(excelRow);

    // Apply data styling
  const defaultDataStyle: Partial<ExcelJSTypes.Style> = {
      alignment: { vertical: "middle", horizontal: "left" },
      border: {
        top: { style: "thin", color: { argb: "FFE9ECEF" } },
        bottom: { style: "thin", color: { argb: "FFE9ECEF" } },
        left: { style: "thin", color: { argb: "FFE9ECEF" } },
        right: { style: "thin", color: { argb: "FFE9ECEF" } },
      },
    };

    addedRow.eachCell((cell, colNumber) => {
      const columnConfig = columns[colNumber - 1];
      // Check if there's a cell-specific style function
      const cellSpecificStyle = columnConfig?.cellStyle?.(row, rowIndex + 2);
      cell.style = {
        ...defaultDataStyle,
        ...dataStyle,
        ...columnConfig?.style,
        ...cellSpecificStyle,
      };
    });
  });

  // Apply conditional formatting
  columns.forEach((col, colIndex) => {
    if (!col.conditionalFormatting || col.conditionalFormatting.length === 0) return;

    const numberToColumn = (idx: number) => {
      let n = idx + 1;
      let s = "";
      while (n > 0) {
        const r = (n - 1) % 26;
        s = String.fromCharCode(65 + r) + s;
        n = Math.floor((n - 1) / 26);
      }
      return s;
    };

    const colLetter = numberToColumn(colIndex); // supports AA, AB...
    const rangeStart = `${colLetter}2`; // Start from row 2 (after header)
    const rangeEnd = `${colLetter}${data.length + 1}`;
    const range = `${rangeStart}:${rangeEnd}`;

    col.conditionalFormatting.forEach((rule) => {
      if (rule.type === "cellIs" && rule.operator && rule.style) {
        worksheet.addConditionalFormatting({
          ref: range,
          rules: [
            {
              type: "cellIs",
              operator: rule.operator,
              formulae: [String(rule.value), rule.value2 ? String(rule.value2) : undefined].filter(
                Boolean
              ) as string[],
              style: rule.style as any,
              priority: rule.priority ?? 1,
            },
          ],
        });
      } else if (rule.type === "expression" && rule.formula && rule.style) {
        worksheet.addConditionalFormatting({
          ref: range,
          rules: [
            {
              type: "expression",
              formulae: [rule.formula],
              style: rule.style as any,
              priority: rule.priority ?? 1,
            },
          ],
        });
      } else if (rule.type === "colorScale" && rule.colorScale) {
        worksheet.addConditionalFormatting({
          ref: range,
          rules: [
            {
              type: "colorScale",
              cfvo: [
                { type: "min" },
                ...(rule.colorScale.mid ? [{ type: "percentile" as const, value: 50 }] : []),
                { type: "max" },
              ],
              color: [
                rule.colorScale.min ? { argb: rule.colorScale.min.color.replace("#", "FF") } : undefined,
                ...(rule.colorScale.mid
                  ? [{ argb: rule.colorScale.mid.color.replace("#", "FF") }]
                  : []),
                rule.colorScale.max ? { argb: rule.colorScale.max.color.replace("#", "FF") } : undefined,
              ].filter(Boolean) as any[],
              priority: rule.priority ?? 1,
            },
          ],
        });
      } else if (rule.type === "dataBar" && rule.dataBar) {
        worksheet.addConditionalFormatting({
          ref: range,
          rules: [
            {
              type: "dataBar",
              cfvo: [{ type: "min" }, { type: "max" }],
              color: rule.dataBar.color.replace("#", ""),
              showValue: rule.dataBar.showValue ?? true,
              priority: rule.priority ?? 1,
            } as any,
          ],
        });
      }
    });
  });

  // Apply global conditional formatting
  if (options.conditionalFormatting) {
    options.conditionalFormatting.forEach((formatting) => {
      formatting.rules.forEach((rule) => {
        if (rule.type === "expression" && rule.formula && rule.style) {
          worksheet.addConditionalFormatting({
            ref: formatting.range,
            rules: [
              {
                type: "expression",
                formulae: [rule.formula],
                style: rule.style as any,
                priority: 1,
              },
            ],
          });
        } else if (rule.type === "cellIs" && rule.operator && rule.style) {
          worksheet.addConditionalFormatting({
            ref: formatting.range,
            rules: [
              {
                type: "cellIs",
                operator: rule.operator,
                formulae: [String(rule.value), rule.value2 ? String(rule.value2) : undefined].filter(
                  Boolean
                ) as string[],
                style: rule.style as any,
                priority: 1,
              },
            ],
          });
        } else if (rule.type === "colorScale" && rule.colorScale) {
          worksheet.addConditionalFormatting({
            ref: formatting.range,
            rules: [
              {
                type: "colorScale",
                cfvo: [
                  { type: "min" },
                  ...(rule.colorScale.mid ? [{ type: "percentile" as const, value: 50 }] : []),
                  { type: "max" },
                ],
                color: [
                  rule.colorScale.min,
                  ...(rule.colorScale.mid ? [rule.colorScale.mid] : []),
                  rule.colorScale.max,
                ].filter(Boolean) as any[],
                priority: 1,
              },
            ],
          });
        }
      });
    });
  }

  // Auto-filter
  if (enableAutoFilter && data.length > 0) {
    worksheet.autoFilter = {
      from: { row: 1, column: 1 },
      to: { row: data.length + 1, column: columns.length },
    };
  }

  // Freeze panes
  if (freezeRows > 0 || freezeColumns > 0) {
    worksheet.views = [
      {
        state: "frozen",
        xSplit: freezeColumns,
        ySplit: freezeRows,
        activeCell: "A1",
      },
    ];
  }

  // Generate buffer and download
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName.endsWith(".xlsx") ? fileName : `${fileName}.xlsx`;
  link.click();
  window.URL.revokeObjectURL(url);
};
