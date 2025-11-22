import { useMemo, useCallback, useEffect } from "react";
import { Trash2, UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { read } from "xlsx";

import { UploadArea } from "@/components/UploadArea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiImportConfig } from "@/types/api";
import { cn } from "@/lib/utils";

export type BatchUploadRowStatus = "idle" | "uploading" | "success" | "error";

export interface BatchUploadRowState {
  id: string;
  file: File | null;
  impresa: string;
  round: string;
  configId: string;
  sheetName: string;
  sheetOptions: string[];
  status: BatchUploadRowStatus;
  message?: string;
}

interface BatchUploadRowProps {
  row: BatchUploadRowState;
  configs: ApiImportConfig[];
  onChange: (rowId: string, updates: Partial<BatchUploadRowState>) => void;
  onRemove?: (rowId: string) => void;
  disabled?: boolean;
  index?: number;
}

const statusMap: Record<BatchUploadRowStatus, { label: string; variant: string }> = {
  idle: { label: "In attesa", variant: "secondary" },
  uploading: { label: "In caricamento", variant: "outline" },
  success: { label: "Caricato", variant: "default" },
  error: { label: "Errore", variant: "destructive" },
};

const NONE_CONFIG_VALUE = "__none_import_config__";
const NONE_SHEET_VALUE = "__custom_sheet__";

export function BatchUploadRow({
  row,
  configs,
  onChange,
  onRemove,
  disabled = false,
  index,
}: BatchUploadRowProps) {
  const status = useMemo(() => statusMap[row.status], [row.status]);
  const isFilled = Boolean(row.file || row.impresa || row.round || row.configId);
  const selectedConfig = useMemo(
    () => configs.find((config) => String(config.id) === row.configId),
    [configs, row.configId],
  );
  const sheetOptions = row.sheetOptions ?? [];

  useEffect(() => {
    if (!row.configId) return;
    const configSheet = selectedConfig?.sheet_name?.trim();
    if (!configSheet) return;
    if (!row.sheetName) {
      onChange(row.id, { sheetName: configSheet });
    }
  }, [row.configId, row.sheetName, selectedConfig?.sheet_name, onChange, row.id]);

  const matchSheetName = useCallback((names: string[], desired?: string | null) => {
    if (!desired) return undefined;
    const lowered = desired.trim().toLowerCase();
    if (!lowered) return undefined;
    return names.find((name) => name.trim().toLowerCase() === lowered);
  }, []);

  const handleFileSelected = useCallback(
    (file: File | null) => {
      if (!file) {
        onChange(row.id, { file: null, sheetOptions: [] });
        return;
      }
      onChange(row.id, { file });
      (async () => {
        try {
          const buffer = await file.arrayBuffer();
          const workbook = read(buffer, { type: "array" });
          const names = workbook.SheetNames ?? [];
          const preferred =
            matchSheetName(names, row.sheetName) ??
            matchSheetName(names, selectedConfig?.sheet_name) ??
            names[0] ??
            "";
          onChange(row.id, {
            sheetOptions: names,
            sheetName: preferred,
          });
        } catch (error) {
          toast.error("Impossibile leggere il file Excel", {
            description: error instanceof Error ? error.message : undefined,
          });
          onChange(row.id, { sheetOptions: [] });
        }
      })();
    },
    [matchSheetName, onChange, row.id, row.sheetName, selectedConfig?.sheet_name],
  );

  return (
    <div className="space-y-4 rounded-xl border border-border/60 bg-card/80 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <UploadCloud className="h-4 w-4 text-primary" />
          <span>{`Caricamento ${index != null ? `#${index + 1}` : ""}`}</span>
          <Badge variant={status.variant as never}>{status.label}</Badge>
          {row.message && (
            <span
              className={cn(
                "text-xs",
                row.status === "error" ? "text-destructive" : "text-muted-foreground",
              )}
            >
              {row.message}
            </span>
          )}
        </div>
        {onRemove && isFilled && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onRemove(row.id)}
            disabled={disabled || row.status === "uploading"}
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <UploadArea
          onFileSelected={handleFileSelected}
          onFileUpload={() => Promise.resolve()}
          successMessage={null}
          submitLabel="File pronto per l'import"
          disabled={disabled || row.status === "uploading"}
        />

        <div className="space-y-3">
          <div className="space-y-1">
            <Label>Impresa</Label>
            <Input
              placeholder="Nome impresa"
              value={row.impresa}
              onChange={(event) => onChange(row.id, { impresa: event.target.value })}
              disabled={disabled || row.status === "uploading"}
            />
          </div>
          <div className="space-y-1">
            <Label>Round</Label>
            <Input
              type="number"
              min={1}
              placeholder="Numero round"
              value={row.round}
              onChange={(event) => onChange(row.id, { round: event.target.value })}
              disabled={disabled || row.status === "uploading"}
            />
          </div>
          <div className="space-y-1">
            <Label>Configurazione import</Label>
            <Select
              value={row.configId || NONE_CONFIG_VALUE}
              onValueChange={(value) => {
                if (value === NONE_CONFIG_VALUE) {
                  onChange(row.id, { configId: "", sheetName: "" });
                  return;
                }
                const config = configs.find((item) => String(item.id) === value);
                onChange(row.id, {
                  configId: value,
                  sheetName: config?.sheet_name?.trim() ?? row.sheetName,
                });
              }}
              disabled={disabled || row.status === "uploading"}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona configurazione" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE_CONFIG_VALUE}>Nessuna configurazione</SelectItem>
                {configs.map((config) => (
                  <SelectItem key={config.id} value={String(config.id)}>
                    {config.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {row.configId ? (
              <p className="text-xs text-muted-foreground">
                Foglio configurazione: {selectedConfig?.sheet_name ?? "—"}
              </p>
            ) : null}
          </div>
          {row.configId ? (
            <div className="space-y-1">
              <Label>Foglio Excel</Label>
              {sheetOptions.length ? (
                <Select
                  value={row.sheetName || NONE_SHEET_VALUE}
                  onValueChange={(value) =>
                    onChange(row.id, { sheetName: value === NONE_SHEET_VALUE ? "" : value })
                  }
                  disabled={disabled || row.status === "uploading"}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona foglio" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE_SHEET_VALUE}>Personalizzato</SelectItem>
                    {sheetOptions.map((sheet) => (
                      <SelectItem key={sheet} value={sheet}>
                        {sheet}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  placeholder="Es. EPU - phase 1"
                  value={row.sheetName}
                  onChange={(event) => onChange(row.id, { sheetName: event.target.value })}
                  disabled={disabled || row.status === "uploading"}
                />
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

