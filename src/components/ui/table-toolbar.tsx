import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import {
  Download,
  Search,
  Columns3,
  RefreshCw,
  Eye,
  EyeOff,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface TableColumn {
  id: string;
  label: string;
  visible: boolean;
}

export interface TableToolbarProps {
  // Search
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  enableSearch?: boolean;

  // Refresh
  onRefresh?: () => void;
  enableRefresh?: boolean;
  isRefreshing?: boolean;

  // Column toggle
  columns?: TableColumn[];
  onColumnToggle?: (columnId: string, visible: boolean) => void;
  onToggleAllColumns?: (visible: boolean) => void;
  enableColumnToggle?: boolean;

  // Export
  onExport?: () => void;
  enableExport?: boolean;
  exportLabel?: string;

  // Custom content
  leftContent?: React.ReactNode;
  rightContent?: React.ReactNode;

  // Row count
  totalRows?: number;
  filteredRows?: number;
  showRowCount?: boolean;

  // Styling
  className?: string;
}

export function TableToolbar({
  searchValue = "",
  onSearchChange,
  searchPlaceholder = "Cerca in tutte le colonne...",
  enableSearch = true,
  onRefresh,
  enableRefresh = false,
  isRefreshing = false,
  columns = [],
  onColumnToggle,
  onToggleAllColumns,
  enableColumnToggle = true,
  onExport,
  enableExport = true,
  exportLabel = "Esporta Excel",
  leftContent,
  rightContent,
  totalRows,
  filteredRows,
  showRowCount = true,
  className,
}: TableToolbarProps) {
  const visibleCount = columns.filter((col) => col.visible).length;
  const allVisible = visibleCount === columns.length;
  const someVisible = visibleCount > 0 && visibleCount < columns.length;

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-xl border border-border/25 bg-card/70 px-3 py-2 text-sm text-foreground shadow-[0_2px_10px_rgba(18,24,40,0.035)] sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      {/* Left section */}
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {leftContent}

        {enableSearch && onSearchChange && (
          <div className="relative flex-1 min-w-[220px] max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              placeholder={searchPlaceholder}
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              className="h-9 rounded-full pl-9"
              aria-label="Cerca nella tabella"
              role="searchbox"
            />
          </div>
        )}

        {enableRefresh && onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="h-9"
            aria-label={isRefreshing ? "Aggiornamento in corso" : "Aggiorna tabella"}
          >
            <RefreshCw
              className={cn("h-4 w-4", isRefreshing && "animate-spin")}
              aria-hidden="true"
            />
          </Button>
        )}
      </div>

      {/* Right section */}
      <div className="flex flex-wrap items-center gap-2">
        {rightContent}

        {showRowCount && totalRows !== undefined && (
          <Badge
            variant="outline"
            className="h-9 px-3 font-mono text-xs border-border/40 bg-transparent"
            aria-live="polite"
            aria-atomic="true"
            role="status"
          >
            {filteredRows !== undefined && filteredRows !== totalRows
              ? `${filteredRows} di ${totalRows}`
              : totalRows}{" "}
            righe
          </Badge>
        )}

        {enableColumnToggle && columns.length > 0 && onColumnToggle && onToggleAllColumns && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-2"
                aria-label={`Gestisci colonne visibili. ${visibleCount} di ${columns.length} visibili`}
              >
                <Columns3 className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Colonne</span>
                <Badge variant="secondary" className="ml-1 px-1.5 font-mono text-xs" aria-hidden="true">
                  {visibleCount}
                </Badge>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="flex items-center justify-between">
                <span id="column-toggle-label">Mostra/Nascondi</span>
                <div className="flex gap-1" role="group" aria-labelledby="column-toggle-label">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleAllColumns(true)}
                    disabled={allVisible}
                    className="h-6 px-2 text-xs"
                    aria-label="Mostra tutte le colonne"
                  >
                    <Eye className="h-3 w-3" aria-hidden="true" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleAllColumns(false)}
                    disabled={visibleCount === 0}
                    className="h-6 px-2 text-xs"
                    aria-label="Nascondi tutte le colonne"
                  >
                    <EyeOff className="h-3 w-3" aria-hidden="true" />
                  </Button>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {columns.map((column) => (
                <DropdownMenuCheckboxItem
                  key={column.id}
                  checked={column.visible}
                  onCheckedChange={(checked) => onColumnToggle(column.id, checked)}
                >
                  {column.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {enableExport && onExport && (
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            className="h-9 gap-2"
            aria-label={exportLabel}
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">{exportLabel}</span>
          </Button>
        )}
      </div>
    </div>
  );
}
