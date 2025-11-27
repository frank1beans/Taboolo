import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, Loader2, Play, Plus } from "lucide-react";

import { BatchUploadRow, BatchUploadRowState } from "@/components/BatchUploadRow";
import { CommessaPageHeader } from "@/features/commessa";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { api } from "@/lib/api-client";
import type { ApiImportConfig } from "@/types/api";

type DefaultMetadata = {
  impresa: string;
  round: string;
  configId: string;
};

type RitorniGaraBatchProps = {
  inline?: boolean;
};

const NONE_IMPORT_CONFIG_VALUE = "__none_import_config__";

const createEmptyRow = (defaults?: DefaultMetadata): BatchUploadRowState => ({
  id: crypto.randomUUID(),
  file: null,
  impresa: defaults?.impresa ?? "",
  round: defaults?.round ?? "",
  configId: defaults?.configId ?? "",
  sheetName: "",
  sheetOptions: [],
  status: "idle",
  message: undefined,
});

const splitTokens = (value?: string | null): string[] =>
  value
    ?.split(/[,;\s]+/)
    .map((token) => token.trim())
    .filter(Boolean) ?? [];

export default function RitorniGaraBatch({ inline = false }: RitorniGaraBatchProps = {}) {
  const { id } = useParams();
  const commessaId = useMemo(() => Number(id), [id]);
  const isValidId = Number.isFinite(commessaId);
  const { commessa } = useCommessaContext();
  const { toast } = useToast();

  const [defaults, setDefaults] = useState<DefaultMetadata>({
    impresa: "",
    round: "",
    configId: "",
  });
  const [rows, setRows] = useState<BatchUploadRowState[]>([createEmptyRow(defaults)]);
  const [isUploading, setIsUploading] = useState(false);
  const [runStats, setRunStats] = useState<{ success: number; error: number }>({
    success: 0,
    error: 0,
  });

  const {
    data: importConfigs = [],
    isLoading: configsLoading,
    isError: configsError,
  } = useQuery<ApiImportConfig[]>({
    queryKey: ["import-configs", commessaId, "batch"],
    queryFn: () => api.listImportConfigs({ commessaId }),
    enabled: isValidId,
  });

  const hasConfigs = importConfigs.length > 0;

  // Righe "piene" (hanno almeno un campo)
  const filledRows = useMemo(
    () =>
      rows.filter((row) => row.file || row.impresa || row.round || row.configId),
    [rows],
  );

  // Righe effettivamente importabili (file + impresa + round + config)
  const uploadableRows = useMemo(
    () =>
      rows.filter(
        (row) =>
          row.file &&
          row.impresa.trim() &&
          row.round.trim() &&
          row.configId.trim(),
      ),
    [rows],
  );

  const canImportAll = useMemo(
    () => hasConfigs && uploadableRows.length > 0 && !isUploading,
    [hasConfigs, uploadableRows.length, isUploading],
  );

  const ensureTrailingEmptyRow = useCallback(
    (list: BatchUploadRowState[]): BatchUploadRowState[] => {
      const hasEmpty = list.some((row) => row.file === null && !row.impresa && !row.round && !row.configId);
      if (!hasEmpty) {
        return [...list, createEmptyRow(defaults)];
      }
      return list;
    },
    [defaults],
  );

  const addEmptyRow = useCallback(() => {
    setRows((prev) => ensureTrailingEmptyRow(prev));
  }, [ensureTrailingEmptyRow]);

  const updateRow = useCallback(
    (rowId: string, updates: Partial<BatchUploadRowState>) => {
      setRows((prev) => {
        let updated = prev.map((row) => {
          if (row.id !== rowId) return row;

          const shouldResetStatus =
            updates.file !== undefined ||
            updates.impresa !== undefined ||
            updates.round !== undefined ||
            updates.configId !== undefined;

          return {
            ...row,
            ...updates,
            status: updates.status ?? (shouldResetStatus ? "idle" : row.status),
            message: updates.message ?? (shouldResetStatus ? undefined : row.message),
          };
        });

        const previousRow = prev.find((row) => row.id === rowId);
        const currentRow = updated.find((row) => row.id === rowId);

        // se prima non c'era file e ora sì, assicuro una riga vuota in coda
        if (!previousRow?.file && currentRow?.file) {
          updated = ensureTrailingEmptyRow(updated);
        }

        // autopopola impresa da config se non impostata
        if (updates.configId) {
          const selectedConfig = importConfigs.find(
            (config) => String(config.id) === updates.configId,
          );
          if (selectedConfig?.impresa && !currentRow?.impresa) {
            updated = updated.map((row) =>
              row.id === rowId ? { ...row, impresa: selectedConfig.impresa } : row,
            );
          }
        }

        return updated;
      });
    },
    [ensureTrailingEmptyRow, importConfigs],
  );

  const removeRow = useCallback(
    (rowId: string) => {
      setRows((prev) => {
        // se c'è una sola riga, la resettiamo invece di rimuoverla
        if (prev.length === 1) {
          return [createEmptyRow(defaults)];
        }
        const filtered = prev.filter((row) => row.id !== rowId);
        return ensureTrailingEmptyRow(filtered);
      });
    },
    [defaults, ensureTrailingEmptyRow],
  );

  const applyDefaultsToEmptyRows = useCallback(() => {
    setRows((prev) =>
      prev.map((row) => {
        const isTrulyEmpty =
          !row.file && !row.impresa.trim() && !row.round.trim() && !row.configId.trim();
        if (!isTrulyEmpty) return row;
        return {
          ...row,
          impresa: defaults.impresa || row.impresa,
          round: defaults.round || row.round,
          configId: defaults.configId || row.configId,
        };
      }),
    );
  }, [defaults]);

  const buildPayload = useCallback(
    (row: BatchUploadRowState) => {
      if (!isValidId) throw new Error("Commessa non valida");
      if (!row.file) throw new Error("Seleziona un file per questa riga");

      const impresa = row.impresa.trim();
      if (!impresa) throw new Error("Inserisci il nome dell'impresa");

      const roundNumber = Number(row.round);
      if (!Number.isFinite(roundNumber) || roundNumber <= 0) {
        throw new Error("Inserisci un round valido (numero intero)");
      }

      const config = importConfigs.find((item) => String(item.id) === row.configId);
      if (!config) throw new Error("Seleziona una configurazione di import");

      const sheetName = row.sheetName?.trim() || config.sheet_name?.trim();
      if (!sheetName) {
        throw new Error("Seleziona il foglio da utilizzare per l'import");
      }

      const codeColumns = splitTokens(config.code_columns);
      const descriptionColumns = splitTokens(config.description_columns);
      const priceColumn = config.price_column?.trim() || undefined;
      const quantityColumn = config.quantity_column?.trim() || undefined;

      if (!codeColumns.length || !descriptionColumns.length || !priceColumn) {
        throw new Error(
          "Configura colonne codice, descrizione e prezzo nella configurazione",
        );
      }

      return {
        commessaId,
        file: row.file,
        impresa,
        roundMode: "new" as const,
        roundNumber,
        sheetName,
        codeColumns,
        descriptionColumns,
        priceColumn,
        quantityColumn,
      };
    },
    [importConfigs, isValidId, commessaId],
  );

  const handleImportAll = async () => {
    if (!uploadableRows.length) {
      toast({
        title: "Nessuna riga completa",
        description:
          "Compila impresa, round, configurazione e seleziona almeno un file prima di avviare l'import.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setRunStats({ success: 0, error: 0 });

    for (const row of uploadableRows) {
      try {
        const payload = buildPayload(row);
        setRows((prev) =>
          prev.map((item) =>
            item.id === row.id
              ? { ...item, status: "uploading", message: "Upload in corso..." }
              : item,
          ),
        );

        await api.uploadRitorno(payload.commessaId, {
          file: payload.file,
          impresa: payload.impresa,
          roundMode: payload.roundMode,
          roundNumber: payload.roundNumber,
          sheetName: payload.sheetName,
          codeColumns: payload.codeColumns,
          descriptionColumns: payload.descriptionColumns,
          priceColumn: payload.priceColumn,
          quantityColumn: payload.quantityColumn,
        });

        setRows((prev) =>
          prev.map((item) =>
            item.id === row.id
              ? { ...item, status: "success", message: "Completato" }
              : item,
          ),
        );
        setRunStats((prev) => ({ ...prev, success: prev.success + 1 }));
        toast({
          title: "Import riuscito",
          description: `${row.impresa} - round ${row.round} completato`,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Errore durante l'import";
        setRows((prev) =>
          prev.map((item) =>
            item.id === row.id
              ? { ...item, status: "error", message }
              : item,
          ),
        );
        setRunStats((prev) => ({ ...prev, error: prev.error + 1 }));
        toast({
          title: "Errore import",
          description: message,
          variant: "destructive",
        });
      }
    }

    setIsUploading(false);
  };

  const content = (
    <div className="flex flex-col gap-5">
      {/* Pannello modalità & defaults */}
      <Card className="rounded-2xl border border-border/60 bg-card shadow-sm">
        <CardHeader className="flex flex-col gap-2 border-b border-border/60 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">Modalità import</CardTitle>
            <p className="text-sm text-muted-foreground">
              Imposta valori predefiniti riutilizzabili nelle righe vuote e nella coda.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>
              Configurazioni disponibili: {importConfigs.length}{" "}
              {configsLoading ? "(caricamento...)" : ""}
            </span>
            {configsError && (
              <span className="text-destructive">
                Errore nel caricamento delle configurazioni.
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1">
              <Label htmlFor="default-impresa">Impresa predefinita</Label>
              <Input
                id="default-impresa"
                placeholder="Nome impresa"
                value={defaults.impresa}
                onChange={(event) =>
                  setDefaults((prev) => ({ ...prev, impresa: event.target.value }))
                }
                disabled={isUploading}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="default-round">Round predefinito</Label>
              <Input
                id="default-round"
                type="number"
                min={1}
                placeholder="Numero round"
                value={defaults.round}
                onChange={(event) =>
                  setDefaults((prev) => ({ ...prev, round: event.target.value }))
                }
                disabled={isUploading}
              />
            </div>
            <div className="space-y-1 sm:col-span-2 lg:col-span-1">
              <Label>Configurazione predefinita</Label>
              <Select
                value={defaults.configId || NONE_IMPORT_CONFIG_VALUE}
                onValueChange={(value) =>
                  setDefaults((prev) => ({
                    ...prev,
                    configId: value === NONE_IMPORT_CONFIG_VALUE ? "" : value,
                  }))
                }
                disabled={isUploading || configsLoading}
              >
                <SelectTrigger id="default-config">
                  <SelectValue placeholder="Nessuna" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE_IMPORT_CONFIG_VALUE}>Nessuna</SelectItem>
                  {importConfigs.map((config) => (
                    <SelectItem key={config.id} value={String(config.id)}>
                      {config.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <p>
              Questi valori vengono precompilati nelle nuove righe e possono essere applicati
              alle righe vuote esistenti.
            </p>
            <Button
              size="sm"
              variant="ghost"
              onClick={applyDefaultsToEmptyRows}
              disabled={isUploading}
              className="justify-center"
            >
              Applica alle righe vuote
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Coda di import */}
      <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
        <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-border/60">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg font-semibold">
              <ClipboardList className="h-5 w-5 text-primary" />
              Coda di import
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Trascina i file nelle righe, seleziona l&apos;impresa, il round e la
              configurazione di import.
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              In coda: {uploadableRows.length} pronti · {filledRows.length} righe compilate
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 sm:flex-row sm:items-center">
            <Button
              variant="ghost"
              onClick={addEmptyRow}
              disabled={isUploading || configsLoading}
              className="justify-center"
            >
              <Plus className="h-4 w-4" />
              Aggiungi riga
            </Button>
            <Button
              onClick={handleImportAll}
              disabled={!canImportAll}
              className="gap-2 justify-center"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Import in corso...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Importa tutti
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {!hasConfigs && !configsLoading && (
            <p className="rounded-lg border border-dashed border-border/60 bg-muted/40 p-3 text-xs text-muted-foreground">
              Nessuna configurazione di import trovata. Vai alle impostazioni configurazioni
              import per crearne una prima di procedere.
            </p>
          )}

          {configsLoading && (
            <p className="text-sm text-muted-foreground">
              Caricamento configurazioni...
            </p>
          )}

          {rows.map((row, index) => (
            <BatchUploadRow
              key={row.id}
              row={row}
              index={index}
              configs={importConfigs}
              onChange={updateRow}
              onRemove={filledRows.length > 1 ? removeRow : undefined}
              disabled={isUploading}
            />
          ))}

          <Separator />

          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <p>
              Suggerimento: dopo aver trascinato un file, comparirà automaticamente una nuova
              riga vuota pronta per il prossimo caricamento.
            </p>
            {(runStats.success > 0 || runStats.error > 0) && (
              <p>
                Ultima esecuzione: {runStats.success} riuscite · {runStats.error} con errori
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (inline) {
    return content;
  }

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Ritorni di gara (batch)"
        description="Carica più ritorni di gara in sequenza utilizzando le configurazioni salvate."
        backHref={`/commesse/${commessaId}/overview`}
      />
      {content}
    </div>
  );
}
