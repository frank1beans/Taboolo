import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, Loader2, Play, Plus } from "lucide-react";

import { BatchUploadRow, BatchUploadRowState } from "@/components/BatchUploadRow";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
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
import { ApiImportConfig } from "@/types/api";

type DefaultMetadata = {
  impresa: string;
  round: string;
  configId: string;
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

export default function RitorniGaraBatch() {
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

  const { data: importConfigs = [], isLoading: configsLoading } = useQuery<ApiImportConfig[]>({
    queryKey: ["import-configs", commessaId, "batch"],
    queryFn: () => api.listImportConfigs({ commessaId }),
    enabled: isValidId,
  });

  const addEmptyRow = useCallback(() => {
    setRows((prev) => [...prev, createEmptyRow(defaults)]);
  }, [defaults]);

  const updateRow = useCallback(
    (rowId: string, updates: Partial<BatchUploadRowState>) => {
      setRows((prev) => {
        const updated = prev.map((row) => {
          if (row.id !== rowId) return row;
          const shouldReset =
            updates.file !== undefined ||
            updates.impresa !== undefined ||
            updates.round !== undefined ||
            updates.configId !== undefined;
          return {
            ...row,
            ...updates,
            status: updates.status ?? (shouldReset ? "idle" : row.status),
            message: updates.message ?? (shouldReset ? undefined : row.message),
          };
        });
        const previousRow = prev.find((row) => row.id === rowId);
        const currentRow = updated.find((row) => row.id === rowId);
        if (!previousRow?.file && currentRow?.file) {
          const lastRow = updated[updated.length - 1];
          if (lastRow.file) {
            updated.push(createEmptyRow(defaults));
          }
        }
        if (updates.configId) {
          const selectedConfig = importConfigs.find((config) => String(config.id) === updates.configId);
          if (selectedConfig?.impresa && !currentRow?.impresa) {
            const rowIndex = updated.findIndex((row) => row.id === rowId);
            if (rowIndex !== -1) {
              updated[rowIndex] = {
                ...updated[rowIndex],
                impresa: selectedConfig.impresa,
              };
            }
          }
        }
        return updated;
      });
    },
    [defaults, importConfigs],
  );

  const removeRow = useCallback((rowId: string) => {
    setRows((prev) => {
      const filtered = prev.filter((row) => row.id !== rowId);
      if (!filtered.length) return [createEmptyRow(defaults)];
      const hasEmptyTail = filtered.some((row) => row.file === null);
      return hasEmptyTail ? filtered : [...filtered, createEmptyRow(defaults)];
    });
  }, [defaults]);

  const applyDefaultsToEmptyRows = useCallback(() => {
    setRows((prev) =>
      prev.map((row) => ({
        ...row,
        impresa: row.impresa || defaults.impresa,
        round: row.round || defaults.round,
        configId: row.configId || defaults.configId,
      })),
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
      if (!sheetName) throw new Error("Seleziona il foglio da utilizzare per l'import");
      const codeColumns = splitTokens(config.code_columns);
      const descriptionColumns = splitTokens(config.description_columns);
      const priceColumn = config.price_column?.trim() || undefined;
      const quantityColumn = config.quantity_column?.trim() || undefined;
      if (!codeColumns.length || !descriptionColumns.length || !priceColumn) {
        throw new Error("Configura colonne codice, descrizione e prezzo nella configurazione");
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
    const uploadQueue = rows.filter((row) => row.file);
    if (!uploadQueue.length) {
      toast({
        title: "Nessun file da importare",
        description: "Aggiungi almeno un file prima di avviare l'import.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    for (const row of uploadQueue) {
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
        toast({
          title: "Import riuscito",
          description: `${row.impresa} · round ${row.round} completato`,
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
        toast({
          title: "Errore import",
          description: message,
          variant: "destructive",
        });
      }
    }
    setIsUploading(false);
  };

  const filledRows = rows.filter((row) => row.file || row.impresa || row.round || row.configId);

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Ritorni di gara (batch)"
        description="Carica più ritorni di gara in sequenza utilizzando le configurazioni salvate."
        backHref={`/commesse/${commessaId}/overview`}
      />

      <Card className="rounded-2xl border border-border/60 bg-card shadow-sm">
        <CardHeader className="flex flex-col gap-2 border-b border-border/60 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">Modalità import</CardTitle>
            <p className="text-sm text-muted-foreground">
              Scegli la modalità più adatta e imposta dei valori di default da riusare nelle righe vuote.
            </p>
          </div>
          <Button variant="outline" asChild size="sm" className="justify-center">
            <Link to={`/commesse/${commessaId}/overview#ritorni`} aria-label="Vai all'import singolo">
              Preferisci import singolo?
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              L'import singolo resta disponibile dal dettaglio commessa: consigliato per piccoli test o un solo file.
              Il batch, invece, aggiunge righe automaticamente dopo ogni file trascinato così da creare una coda.
            </p>
            <p className="text-sm text-muted-foreground">
              Entrambi riutilizzano le configurazioni salvate; qui puoi anche applicare valori predefiniti per ridurre le ripetizioni.
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-sm font-semibold">Impostazioni rapide</h4>
              <Button size="sm" variant="ghost" onClick={applyDefaultsToEmptyRows} disabled={isUploading} className="justify-center">
                Applica alle righe vuote
              </Button>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="default-impresa">Impresa predefinita</Label>
                <Input
                  id="default-impresa"
                  placeholder="Nome impresa"
                  value={defaults.impresa}
                  onChange={(event) => setDefaults((prev) => ({ ...prev, impresa: event.target.value }))}
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
                  onChange={(event) => setDefaults((prev) => ({ ...prev, round: event.target.value }))}
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
            <p className="text-xs text-muted-foreground">
              Questi valori vengono precompilati nelle nuove righe e possono essere applicati alle righe vuote esistenti con il pulsante qui sopra.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
        <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-border/60">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg font-semibold">
              <ClipboardList className="h-5 w-5 text-primary" />
              Coda di import
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Trascina i file nelle righe, seleziona l'impresa, il round e la configurazione import.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={addEmptyRow} disabled={isUploading || configsLoading} className="justify-center">
              <Plus className="h-4 w-4" />
              Aggiungi riga
            </Button>
            <Button
              onClick={handleImportAll}
              disabled={isUploading || !importConfigs.length}
              className="gap-2 justify-center"
            >
              {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Importa tutti
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {configsLoading ? (
            <p className="text-sm text-muted-foreground">Caricamento configurazioni...</p>
          ) : null}
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
          <p className="text-xs text-muted-foreground">
            Suggerimento: dopo aver trascinato un file, comparirà una nuova riga vuota pronta per il prossimo caricamento.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
