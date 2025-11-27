import { useCallback, useRef, useState, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  ColGroupDef,
  GridApi,
  GridReadyEvent,
  ColumnState,
  RowClickedEvent,
  CellValueChangedEvent,
} from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import "@/styles/ag-grid-overrides.css";
import { RefreshCw } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";
import {
  DEFAULT_GRID_OPTIONS,
  getGridThemeClass,
  exportToExcel,
  type ExcelExportColumn,
} from "@/lib/grid-utils";
import { TableToolbar, type TableColumn } from "@/components/ui/table-toolbar";

// Aggregation types
export type AggregationType = "sum" | "avg" | "min" | "max" | "count";

export interface ColumnAggregation {
  field: string;
  type: AggregationType;
  label?: string;
  formatter?: (value: number) => string;
}

export interface DataTableProps<T = Record<string, unknown>> {
  // Data
  data: T[];
  columnDefs: (ColDef<T> | ColGroupDef<T>)[];

  // Configuration
  height?: string;
  rowHeight?: number;
  headerHeight?: number;
  getRowId?: (params: { data: T }) => string;

  // Features
  enableSearch?: boolean;
  enableExport?: boolean;
  enableColumnToggle?: boolean;
  enableRefresh?: boolean;
  enableQuickFilter?: boolean;
  enableRowSelection?: boolean;
  enablePagination?: boolean;
  pageSize?: number;

  // Aggregations
  aggregations?: ColumnAggregation[];
  showAggregationFooter?: boolean;

  // Callbacks
  onRefresh?: () => void;
  onRowClicked?: (data: T) => void;
  onSelectionChanged?: (selectedRows: T[]) => void;
  onCellValueChanged?: (event: CellValueChangedEvent<T>) => void;

  // Export
  exportFileName?: string;
  exportColumns?: ExcelExportColumn[];
  customExport?: () => void;
  exportLabel?: string;

  // Styling
  className?: string;
  suppressAutoSize?: boolean;

  // Loading
  isLoading?: boolean;

  // Custom toolbar content
  toolbarLeft?: React.ReactNode;
  toolbarRight?: React.ReactNode;
  activeFilters?: React.ReactNode;

  // Accessibility
  /** Accessible label for the data table */
  ariaLabel?: string;
  /** Description for the data table */
  ariaDescription?: string;
}

// Helper function to calculate aggregations
function calculateAggregation<T>(
  data: T[],
  field: string,
  type: AggregationType
): number {
  const values = data
    .map((item) => {
      const value = (item as Record<string, unknown>)[field];
      return typeof value === "number" ? value : null;
    })
    .filter((v): v is number => v !== null);

  if (values.length === 0) return 0;

  switch (type) {
    case "sum":
      return values.reduce((acc, val) => acc + val, 0);
    case "avg":
      return values.reduce((acc, val) => acc + val, 0) / values.length;
    case "min":
      return Math.min(...values);
    case "max":
      return Math.max(...values);
    case "count":
      return values.length;
    default:
      return 0;
  }
}

export function DataTable<T = Record<string, unknown>>({
  data,
  columnDefs,
  height = "600px",
  rowHeight,
  headerHeight,
  getRowId,
  enableSearch = true,
  enableExport = true,
  enableColumnToggle = true,
  enableRefresh = false,
  enableQuickFilter = true,
  enableRowSelection = false,
  enablePagination = false,
  pageSize = 100,
  aggregations,
  showAggregationFooter = false,
  onRefresh,
  onRowClicked,
  onSelectionChanged,
  onCellValueChanged,
  exportFileName = "export",
  exportColumns,
  customExport,
  exportLabel = "Esporta Excel",
  className,
  suppressAutoSize = false,
  isLoading = false,
  toolbarLeft,
  toolbarRight,
  activeFilters,
  ariaLabel = "Tabella dati",
  ariaDescription,
}: DataTableProps<T>) {
  const { resolvedTheme, theme } = useTheme();
  const gridRef = useRef<AgGridReact<T>>(null);
  const [gridApi, setGridApi] = useState<GridApi<T> | null>(null);
  const [searchText, setSearchText] = useState("");
  const [columnStates, setColumnStates] = useState<Map<string, boolean>>(
    new Map()
  );

  const currentTheme = resolvedTheme ?? theme;
  const isDarkMode = currentTheme === "dark";
  const gridThemeClass = getGridThemeClass(isDarkMode);
  const fillParent =
    typeof height === "string" && height.trim().endsWith("%");
  const minHeightStyle = fillParent ? { minHeight: "420px" } : undefined;

  // Calculate aggregation footer row
  const pinnedBottomRowData = useMemo(() => {
    if (!showAggregationFooter || !aggregations || aggregations.length === 0) {
      return undefined;
    }

    const aggregationRow: Record<string, unknown> = {
      _isAggregation: true,
    };

    aggregations.forEach((agg) => {
      const value = calculateAggregation(data, agg.field, agg.type);
      aggregationRow[agg.field] = agg.formatter
        ? agg.formatter(value)
        : value;
    });

    // Add label in first column
    const firstColDef = columnDefs[0];
    if (firstColDef && "field" in firstColDef && firstColDef.field) {
      aggregationRow[firstColDef.field] = "Totale";
    }

    return [aggregationRow as T];
  }, [data, aggregations, showAggregationFooter, columnDefs]);

  // Initialize column visibility states
  const initializeColumnStates = useCallback((api: GridApi<T>) => {
    const allColumns = api.getColumns();
    const states = new Map<string, boolean>();
    allColumns?.forEach((col) => {
      const colId = col.getColId();
      const isVisible = col.isVisible();
      states.set(colId, isVisible);
    });
    setColumnStates(states);
  }, []);

  const onGridReady = useCallback(
    (params: GridReadyEvent<T>) => {
      setGridApi(params.api);
      initializeColumnStates(params.api);

      // Don't auto-size columns - let them use their defined widths
      // This prevents issues with too many columns
    },
    [initializeColumnStates]
  );

  // Quick search/filter
  const handleSearch = useCallback(
    (value: string) => {
      setSearchText(value);
      if (gridApi && enableQuickFilter) {
        gridApi.setGridOption("quickFilterText", value);
      }
    },
    [gridApi, enableQuickFilter]
  );

  // Toggle column visibility
  const toggleColumn = useCallback(
    (colId: string, visible: boolean) => {
      if (!gridApi) return;

      gridApi.setColumnsVisible([colId], visible);
      setColumnStates((prev) => new Map(prev).set(colId, visible));
    },
    [gridApi]
  );

  // Show/hide all columns
  const toggleAllColumns = useCallback(
    (visible: boolean) => {
      if (!gridApi) return;

      const allColumns = gridApi.getColumns();
      const columnIds = allColumns?.map((col) => col.getColId()) || [];

      gridApi.setColumnsVisible(columnIds, visible);

      const newStates = new Map<string, boolean>();
      columnIds.forEach((id) => newStates.set(id, visible));
      setColumnStates(newStates);
    },
    [gridApi]
  );

  // Export to Excel
  const handleExport = useCallback(() => {
    if (customExport) {
      customExport();
      return;
    }

    if (exportColumns) {
      exportToExcel(data, exportColumns, exportFileName);
    }
  }, [customExport, data, exportColumns, exportFileName]);

  // Handle row click
  const onRowClickedInternal = useCallback(
    (event: RowClickedEvent<T>) => {
      if (onRowClicked && event.data) {
        onRowClicked(event.data);
      }
    },
    [onRowClicked]
  );

  // Handle selection change
  const onSelectionChangedInternal = useCallback(() => {
    if (!gridApi || !onSelectionChanged) return;

    const selectedRows = gridApi.getSelectedRows();
    onSelectionChanged(selectedRows);
  }, [gridApi, onSelectionChanged]);

  // Get toggleable columns
  const toggleableColumns = useMemo(() => {
    const flattenColumns = (
      cols: (ColDef<T> | ColGroupDef<T>)[]
    ): ColDef<T>[] => {
      return cols.flatMap((col) => {
        if ("children" in col && col.children) {
          return flattenColumns(col.children);
        }
        return [col as ColDef<T>];
      });
    };

    return flattenColumns(columnDefs).filter(
      (col) => col.field && col.headerName
    );
  }, [columnDefs]);

  // Prepare toolbar columns
  const toolbarColumns: TableColumn[] = useMemo(() => {
    return toggleableColumns.map((col) => {
      const colId = col.field as string;
      return {
        id: colId,
        label: col.headerName || colId,
        visible: columnStates.get(colId) ?? true,
      };
    });
  }, [toggleableColumns, columnStates]);

  // Filtered row count
  const filteredRowCount = useMemo(() => {
    if (!gridApi || !searchText) return undefined;
    return gridApi.getDisplayedRowCount();
  }, [gridApi, searchText, data]);

  return (
    <div
      className={cn(
        "flex flex-col gap-3 relative",
        fillParent && "h-full min-h-0",
        className,
      )}
    >
      {activeFilters ? <div className="flex flex-wrap items-center gap-2">{activeFilters}</div> : null}
      <div className="pb-3">
        <TableToolbar
          className="flex flex-col gap-2 text-sm sm:flex-row sm:items-center sm:justify-between"
          searchValue={searchText}
          onSearchChange={handleSearch}
          enableSearch={enableSearch}
          onRefresh={onRefresh}
          enableRefresh={enableRefresh}
          isRefreshing={isLoading}
          columns={toolbarColumns}
          onColumnToggle={toggleColumn}
          onToggleAllColumns={toggleAllColumns}
          enableColumnToggle={enableColumnToggle}
          onExport={handleExport}
          enableExport={enableExport}
          exportLabel={exportLabel}
          leftContent={toolbarLeft}
          rightContent={toolbarRight}
          totalRows={data.length}
          filteredRows={filteredRowCount}
          showRowCount={true}
        />
      </div>

      {/* Grid */}
      <div
        className={cn(
          gridThemeClass,
          "rounded-2xl border border-border/30 bg-card/90 shadow-[0_10px_30px_rgba(18,24,40,0.04)] overflow-hidden",
          fillParent && "flex-1 min-h-[320px]",
          isLoading && "opacity-60 pointer-events-none"
        )}
        style={{ height, ...minHeightStyle }}
        role="region"
        aria-label={ariaLabel}
        aria-busy={isLoading}
        aria-describedby={ariaDescription ? "datatable-description" : undefined}
        tabIndex={0}
      >
        {!isLoading && data.length === 0 && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80 text-sm text-muted-foreground">
            Nessun dato disponibile
          </div>
        )}
        {ariaDescription && (
          <span id="datatable-description" className="sr-only">
            {ariaDescription}
          </span>
        )}
        {isLoading && (
          <span className="sr-only" role="status" aria-live="polite">
            Caricamento dati in corso
          </span>
        )}
        <AgGridReact<T>
          ref={gridRef}
          rowData={data}
          columnDefs={columnDefs}
          {...DEFAULT_GRID_OPTIONS}
          rowHeight={rowHeight}
          headerHeight={headerHeight}
          onGridReady={onGridReady}
          onRowClicked={onRowClickedInternal}
          onSelectionChanged={onSelectionChangedInternal}
          onCellValueChanged={onCellValueChanged}
          getRowId={getRowId}
          quickFilterText={searchText}
          // Aggregation footer
          pinnedBottomRowData={pinnedBottomRowData}
          // Row selection
          rowSelection={enableRowSelection ? "multiple" : undefined}
          suppressRowClickSelection={!enableRowSelection}
          // Pagination
          pagination={enablePagination}
          paginationPageSize={pageSize}
          paginationPageSizeSelector={[25, 50, 100, 200]}
          // Keyboard navigation
          suppressCellFocus={false}
          ensureDomOrder={true}
          // Loading
          loadingOverlayComponent={() => (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
            </div>
          )}
          // Styling for aggregation row
          getRowStyle={(params) => {
            if ((params.data as Record<string, unknown>)?._isAggregation) {
              return {
                fontWeight: "600",
                backgroundColor: isDarkMode
                  ? "hsl(220, 20%, 14%)"
                  : "hsl(220, 20%, 96%)",
                borderTop: `2px solid ${isDarkMode ? "hsl(220, 16%, 26%)" : "hsl(220, 16%, 85%)"}`,
              };
            }
            return undefined;
          }}
        />
      </div>

    </div>
  );
}
