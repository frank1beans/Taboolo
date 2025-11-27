import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { read, utils, type WorkBook } from "xlsx";
import { AlertTriangle, Loader2, Upload } from "lucide-react";

import { RoundUploadDialog } from "@/components/RoundUploadDialog";
import { UploadArea } from "@/components/UploadArea";
import { CommessaPageHeader } from "@/features/commessa";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import { formatShortDate } from "@/lib/formatters";
import type { ApiBatchSingleFileResult, ApiCommessaDetail } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import RitorniGaraBatch from "../analysis/RitorniGaraBatch";

type RoundDetail = {
  round: number;
  imprese: string[];
};

type BatchImpresaRow = {
  id: string;
  nomeImpresa: string;
  priceColumn: string;
  quantityColumn: string;
  roundNumber: string;
  roundMode: "auto" | "new" | "replace";
};

type ImportMode = "wizard" | "multi-impresa" | "wbs";

const createRow = (nextRound: number): BatchImpresaRow => ({
  id: crypto.randomUUID ? crypto.randomUUID() : String(Math.random()),
  nomeImpresa: "",
  priceColumn: "",
  quantityColumn: "",
  roundNumber: String(nextRound),
  roundMode: "auto",
});

const splitColumns = (value: string) =>
  value
    .split(/[,;\s]+/)
    .map((token) => token.trim().replace(/^\$/, "").toUpperCase())
    .filter(Boolean);

const columnLetter = (index: number): string => {
  let current = index;
  let label = "";
  while (current >= 0) {
    label = String.fromCharCode((current % 26) + 65) + label;
    current = Math.floor(current / 26) - 1;
  }
  return label;
};

const buildColumnOptions = (workbook: WorkBook | null, sheetName: string | null) => {
  if (!workbook || !sheetName) return [];
  const sheet = workbook.Sheets[sheetName];
  if (!sheet) return [];
  const rows = utils.sheet_to_json(sheet, { header: 1, blankrows: false, defval: "" }) as (
    | string
    | number
  )[][];
  const header = (rows[0] ?? []) as (string | number)[];
  const maxColumns = Math.max(header.length, 15);
  return Array.from({ length: maxColumns }).map((_, idx) => {
    const letter = columnLetter(idx);
    const raw = header[idx];
    const label = raw ? String(raw).trim() : "";
    return {
      value: letter,
      label: label ? `${letter} · ${label}` : letter,
    };
  });
};

const findNextRound = (commessa?: ApiCommessaDetail) => {
  const rounds =
    commessa?.computi
      ?.filter((c) => c.round_number != null)
      .map((c) => c.round_number as number) ?? [];
  if (!rounds.length) return 1;
  return Math.max(...rounds) + 1;
};

export default function CommessaImportPage() {
  const { id } = useParams();
  const commessaId = Number(id);
  const commessaIdKey = Number.isFinite(commessaId) ? String(commessaId) : "";
  const { commessa, refetchCommessa } = useCommessaContext();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [importMode, setImportMode] = useState<ImportMode>("wizard");

  // Single file multi-impresa state
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchWorkbook, setBatchWorkbook] = useState<WorkBook | null>(null);
  const [sheetOptions, setSheetOptions] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [columnOptions, setColumnOptions] = useState<{ value: string; label: string }[]>([]);
  const [codeColumnsInput, setCodeColumnsInput] = useState("A");
  const [descriptionColumnsInput, setDescriptionColumnsInput] = useState("B");
  const [progressiveColumn, setProgressiveColumn] = useState("");
  const [rows, setRows] = useState<BatchImpresaRow[]>([createRow(findNextRound(commessa))]);
  const [lastResult, setLastResult] = useState<ApiBatchSingleFileResult | null>(null);
  const [isParsingSheet, setIsParsingSheet] = useState(false);
  const [wbsMode, setWbsMode] = useState<"create" | "update">("create");

  const nextRoundNumber = useMemo(() => findNextRound(commessa), [commessa]);

  const roundDetails: RoundDetail[] = useMemo(() => {
    const map = new Map<number, Set<string>>();
    commessa?.computi
      ?.filter((c) => c.tipo === "ritorno")
      .forEach((computo) => {
        const round = computo.round_number ?? 1;
        if (!map.has(round)) map.set(round, new Set<string>());
        if (computo.impresa) map.get(round)!.add(computo.impresa);
      });
    return Array.from(map.entries())
      .map(([round, impreseSet]) => ({
        round,
        imprese: Array.from(impreseSet).sort((a, b) => a.localeCompare(b, "it-IT")),
      }))
      .sort((a, b) => a.round - b.round);
  }, [commessa?.computi]);

  const existingRounds = useMemo(
    () => roundDetails.map((detail) => detail.round),
    [roundDetails],
  );

  const invalidateCommessaData = useCallback(async () => {
    if (!Number.isFinite(commessaId)) return;
    const promises: Promise<unknown>[] = [Promise.resolve(refetchCommessa())];
    if (commessaIdKey) {
      promises.push(
        queryClient.invalidateQueries({ queryKey: ["confronto", commessaIdKey] }),
        queryClient.invalidateQueries({ queryKey: ["analisi", commessaIdKey] }),
      );
    }
    await Promise.all(promises);
  }, [commessaId, commessaIdKey, queryClient, refetchCommessa]);

  const uploadProjectMutation = useMutation({
    mutationFn: (file: File) => api.uploadComputoProgetto(commessaId, file),
    onSuccess: async () => {
      await invalidateCommessaData();
      toast({
        title: "Computo caricato",
        description: "Il computo metrico è stato importato correttamente.",
      });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Errore durante l'import del file";
      toast({ title: "Upload fallito", description: message, variant: "destructive" });
    },
  });

  const uploadReturnMutation = useMutation({
    mutationFn: (payload: Parameters<typeof api.uploadRitorno>[1]) =>
      api.uploadRitorno(commessaId, payload),
    onSuccess: async () => {
      await invalidateCommessaData();
      toast({
        title: "Ritorno caricato",
        description: "Il ritorno di gara è stato importato correttamente.",
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'import del ritorno";
      toast({ title: "Upload fallito", description: message, variant: "destructive" });
    },
  });

  const uploadSixMutation = useMutation({
    mutationFn: (params: {
      file: File;
      preventivoId?: string;
      enableEmbeddings?: boolean;
      enablePropertyExtraction?: boolean;
    }) =>
      api.importSixFile(commessaId, params.file, params.preventivoId, {
        enableEmbeddings: params.enableEmbeddings,
        enablePropertyExtraction: params.enablePropertyExtraction,
      }),
    onSuccess: async (result) => {
      await invalidateCommessaData();
      const listinoOnly = result?.listino_only;
      const priceItems = result?.price_items ?? 0;
      toast({
        title: listinoOnly ? "Listino STR Vision importato" : "Computo STR Vision importato",
        description: listinoOnly
          ? `Caricati ${priceItems} prezzi dal file STR Vision.`
          : "Il preventivo selezionato è stato caricato con successo.",
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Errore durante l'import del file STR Vision";
      toast({ title: "Import fallito", description: message, variant: "destructive" });
    },
  });

  const sixPreview = useCallback(
    async (file: File) => {
      const preview = await api.previewSixPreventivi(commessaId, file);
      return preview.preventivi ?? [];
    },
    [commessaId],
  );

  const batchSingleFileMutation = useMutation({
    mutationFn: (params: Parameters<typeof api.uploadRitorniBatchSingleFile>[1]) =>
      api.uploadRitorniBatchSingleFile(commessaId, params),
    onSuccess: async (data) => {
      setLastResult(data);
      await invalidateCommessaData();
      toast({
        title: "Import multi-impresa completato",
        description: `${data.success_count} successi, ${data.failed_count} fallimenti`,
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'import multi-impresa";
      toast({ title: "Import fallito", description: message, variant: "destructive" });
    },
  });

  const wbsImportMutation = useMutation({
    mutationFn: (params: { file: File; mode: "create" | "update" }) =>
      api.uploadCommessaWbs(commessaId, params.file, params.mode),
    onSuccess: async (data) => {
      await invalidateCommessaData();
      toast({
        title: "WBS importata",
        description: `Righe: ${data.rows_total} · WBS6: +${data.wbs6_inserted}/${data.wbs6_updated}`,
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'import WBS";
      toast({ title: "Import WBS fallito", description: message, variant: "destructive" });
    },
  });

  const handleBatchFileSelected = useCallback(
    async (file: File | null) => {
      setBatchFile(file);
      setBatchWorkbook(null);
      setSheetOptions([]);
      setSelectedSheet("");
      setColumnOptions([]);
      if (!file) return;
      setIsParsingSheet(true);
      try {
        const buffer = await file.arrayBuffer();
        const workbook = read(buffer, { type: "array" });
        setBatchWorkbook(workbook);
        const names = workbook.SheetNames ?? [];
        setSheetOptions(names);
        setSelectedSheet(names[0] ?? "");
        const options = buildColumnOptions(workbook, names[0] ?? null);
        setColumnOptions(options);
        setCodeColumnsInput(options[0]?.value ?? "A");
        setDescriptionColumnsInput(options[1]?.value ?? "B");
        setProgressiveColumn(options[2]?.value ?? "");
      } catch (error) {
        toast({
          title: "Impossibile leggere il file Excel",
          description: error instanceof Error ? error.message : undefined,
          variant: "destructive",
        });
      } finally {
        setIsParsingSheet(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    const options = buildColumnOptions(batchWorkbook, selectedSheet);
    if (options.length) {
      setColumnOptions(options);
    }
  }, [batchWorkbook, selectedSheet]);

  const addRow = () => setRows((prev) => [...prev, createRow(nextRoundNumber)]);
  const removeRow = (id: string) =>
    setRows((prev) => (prev.length === 1 ? prev : prev.filter((row) => row.id !== id)));
  const updateRow = (id: string, patch: Partial<BatchImpresaRow>) =>
    setRows((prev) => prev.map((row) => (row.id === id ? { ...row, ...patch } : row)));

  const handleSubmitBatchSingleFile = async () => {
    if (!batchFile) {
      toast({ title: "Seleziona un file", description: "Carica l'Excel prima di procedere." });
      return;
    }
    const activeRows = rows.filter((row) => row.nomeImpresa.trim() && row.priceColumn.trim());
    if (!activeRows.length) {
      toast({
        title: "Configura almeno un'impresa",
        description: "Indica nome e colonna prezzo per avviare l'import.",
        variant: "destructive",
      });
      return;
    }
    const impreseConfig = activeRows.map((row) => ({
      nome_impresa: row.nomeImpresa.trim(),
      colonna_prezzo: row.priceColumn.trim().toUpperCase(),
      colonna_quantita: row.quantityColumn.trim()
        ? row.quantityColumn.trim().toUpperCase()
        : null,
      round_number: row.roundNumber ? Number(row.roundNumber) : null,
      round_mode: row.roundMode,
    }));

    const codeCols = splitColumns(codeColumnsInput);
    const descCols = splitColumns(descriptionColumnsInput);
    await batchSingleFileMutation.mutateAsync({
      file: batchFile,
      impreseConfig,
      sheetName: selectedSheet || undefined,
      codeColumns: codeCols.length ? codeCols : undefined,
      descriptionColumns: descCols.length ? descCols : undefined,
      progressiveColumn: progressiveColumn.trim() || undefined,
    });
  };

  const isWizardDisabled =
    uploadProjectMutation.isPending || uploadReturnMutation.isPending || uploadSixMutation.isPending;

  const lastAuditUpdate =
    commessa?.updated_at ?? commessa?.created_at ?? null;

  return (
    <Tabs
      value={importMode}
      onValueChange={(value) => setImportMode(value as ImportMode)}
      className="flex flex-col gap-5"
    >
      <CommessaPageHeader
        commessa={commessa}
        title="Importazioni"
        description="Carica computi, ritorni e WBS da un unico spazio di lavoro."
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary">
              Aggiornato {lastAuditUpdate ? formatShortDate(lastAuditUpdate) : "n/d"}
            </Badge>
            <Badge variant="outline">{roundDetails.length} round attivi</Badge>
          </div>

          <TabsList className="grid w-full grid-cols-3 sm:w-auto">
            <TabsTrigger value="wizard" className="text-xs sm:text-sm">
              Wizard singolo
            </TabsTrigger>
            <TabsTrigger value="multi-impresa" className="text-xs sm:text-sm">
              Excel multi-impresa
            </TabsTrigger>
            <TabsTrigger value="wbs" className="text-xs sm:text-sm">
              WBS da Excel
            </TabsTrigger>
          </TabsList>
        </div>
      </CommessaPageHeader>

      {/* Modalità: Wizard singolo + link batch multi-file */}
      <TabsContent value="wizard" className="space-y-4">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="border-border/70 bg-card/90 shadow-sm">
            <CardHeader className="space-y-1">
              <CardTitle className="text-lg font-semibold">Wizard import singolo</CardTitle>
              <CardDescription>
                Usa il wizard per importare un computo progetto (Excel o STR Vision) o un ritorno singolo.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <RoundUploadDialog
                commessaId={commessa?.id ?? commessaId}
                onUploadProgetto={async ({
                  file,
                  tipo,
                  preventivoId,
                  enableEmbeddings,
                  enablePropertyExtraction,
                }) => {
                  if (tipo === "excel") {
                    await uploadProjectMutation.mutateAsync(file);
                    return;
                  }
                  await uploadSixMutation.mutateAsync({
                    file,
                    preventivoId,
                    enableEmbeddings,
                    enablePropertyExtraction,
                  });
                }}
                onPreviewPreventivi={sixPreview}
                onUploadRitorno={async (params) => {
                  // map incoming `mode` to the API-expected `roundMode` field
                  const paramsObj = params as Parameters<typeof api.uploadRitorno>[1] & {
                    mode?: "replace" | "new";
                  };
                  const { mode, ...rest } = paramsObj;
                  const payload: Parameters<typeof api.uploadRitorno>[1] = {
                    ...rest,
                    roundMode: mode ?? paramsObj.roundMode,
                  };
                  await uploadReturnMutation.mutateAsync(payload);
                }}
                existingRounds={existingRounds}
                roundDetails={roundDetails}
                disabled={isWizardDisabled}
                triggerProps={{ className: "w-full sm:w-auto", variant: "default" }}
              />
              <p className="text-xs text-muted-foreground">
                Copre computo metrico MC, STR Vision (.six/.xml) e ritorni singoli LC/MC.
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/90 shadow-sm">
            <CardHeader className="space-y-1">
              <CardTitle className="text-lg font-semibold">Ritorni batch multi-file</CardTitle>
              <CardDescription>
                Coda di upload per più file separati, uno per impresa. Ora è disponibile anche qui.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <RitorniGaraBatch inline />
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      {/* Modalità: Excel multi-impresa da file unico */}
      <TabsContent value="multi-impresa" className="space-y-4">
        <Card className="border-border/70 bg-card/90 shadow-sm">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg font-semibold">
              Ritorni multi-impresa da file unico
            </CardTitle>
            <CardDescription>
              Carica un solo Excel che contiene colonne prezzo/quantità per più imprese. Ogni impresa viene importata come ritorno separato.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
              <div className="space-y-3">
                <UploadArea
                  onFileUpload={() => Promise.resolve()}
                  onFileSelected={handleBatchFileSelected}
                  submitLabel="Svuota selezione"
                  successMessage={null}
                  hint="Formati: .xlsx, .xls (max 100MB)."
                />
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Foglio Excel</Label>
                    <Select
                      value={selectedSheet || undefined}
                      onValueChange={(value) => setSelectedSheet(value)}
                      disabled={!sheetOptions.length || isParsingSheet}
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={isParsingSheet ? "Analisi fogli..." : "Seleziona foglio"}
                        />
                      </SelectTrigger>
                      <SelectContent>
                        {sheetOptions.map((name) => (
                          <SelectItem key={name} value={name}>
                            {name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Colonna progressivo (MC)</Label>
                    <Select
                      value={progressiveColumn || "__none__"}
                      onValueChange={(value) =>
                        setProgressiveColumn(value === "__none__" ? "" : value)
                      }
                      disabled={!columnOptions.length}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Opzionale" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">Nessuna</SelectItem>
                        {columnOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Colonne codice (comma separated)</Label>
                    <Input
                      value={codeColumnsInput}
                      onChange={(event) => setCodeColumnsInput(event.target.value)}
                      placeholder="A,B"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Colonne descrizione</Label>
                    <Input
                      value={descriptionColumnsInput}
                      onChange={(event) => setDescriptionColumnsInput(event.target.value)}
                      placeholder="C"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2 rounded-lg border border-border/60 bg-muted/20 p-3 text-sm">
                <p className="font-semibold">Come funziona</p>
                <ul className="list-disc space-y-1 pl-4 text-muted-foreground">
                  <li>Colonne codice/descrizione comuni a tutte le imprese.</li>
                  <li>Per ogni impresa scegli colonna prezzo (obbligatoria) e quantità (opzionale).</li>
                  <li>Ogni impresa genera un ritorno separato, con round e modalità dedicati.</li>
                  <li>Transazioni isolate: un errore su un'impresa non blocca le altre.</li>
                </ul>
                {!batchFile && (
                  <div className="flex items-center gap-2 rounded-md border border-dashed border-border/60 bg-background/70 p-3 text-xs text-muted-foreground">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    Seleziona un file per attivare la configurazione colonne.
                  </div>
                )}
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">Imprese da importare</p>
                  <p className="text-xs text-muted-foreground">
                    Nome + colonna prezzo sono obbligatori. Quantità è opzionale (MC mode).
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={addRow}>
                  Aggiungi impresa
                </Button>
              </div>

              <div className="space-y-3">
                {rows.map((row, index) => (
                  <div
                    key={row.id}
                    className="rounded-xl border border-border/60 bg-card/80 p-4 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 text-sm font-semibold">
                        <Badge variant="secondary">Impresa #{index + 1}</Badge>
                        {row.nomeImpresa ? (
                          <span className="text-muted-foreground">{row.nomeImpresa}</span>
                        ) : (
                          <span className="text-muted-foreground">Non impostata</span>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => removeRow(row.id)}
                        disabled={rows.length === 1}
                      >
                        Rimuovi
                      </Button>
                    </div>

                    <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                      <div className="space-y-1">
                        <Label>Nome impresa *</Label>
                        <Input
                          value={row.nomeImpresa}
                          onChange={(event) =>
                            updateRow(row.id, { nomeImpresa: event.target.value })
                          }
                          placeholder="Es. Impresa ABC"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Colonna prezzo *</Label>
                        {columnOptions.length ? (
                          <Select
                            value={row.priceColumn || "__none__"}
                            onValueChange={(value) =>
                              updateRow(row.id, { priceColumn: value === "__none__" ? "" : value })
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Seleziona" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="__none__">Nessuna</SelectItem>
                              {columnOptions.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={row.priceColumn}
                            onChange={(event) =>
                              updateRow(row.id, { priceColumn: event.target.value })
                            }
                            placeholder="Es. E"
                          />
                        )}
                      </div>
                      <div className="space-y-1">
                        <Label>Colonna quantità (opz.)</Label>
                        {columnOptions.length ? (
                          <Select
                            value={row.quantityColumn || "__none__"}
                            onValueChange={(value) =>
                              updateRow(row.id, {
                                quantityColumn: value === "__none__" ? "" : value,
                              })
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Opzionale" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="__none__">Nessuna</SelectItem>
                              {columnOptions.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={row.quantityColumn}
                            onChange={(event) =>
                              updateRow(row.id, { quantityColumn: event.target.value })
                            }
                            placeholder="Es. D"
                          />
                        )}
                      </div>
                      <div className="space-y-1">
                        <Label>Round</Label>
                        <Input
                          type="number"
                          min={1}
                          value={row.roundNumber}
                          onChange={(event) =>
                            updateRow(row.id, { roundNumber: event.target.value })
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Modalità round</Label>
                        <RadioGroup
                          value={row.roundMode}
                          onValueChange={(value) =>
                            updateRow(row.id, {
                              roundMode: value as BatchImpresaRow["roundMode"],
                            })
                          }
                          className="flex flex-row gap-3"
                        >
                          <label className="flex items-center gap-2 text-xs">
                            <RadioGroupItem value="auto" id={`${row.id}-auto`} />
                            <span>Auto</span>
                          </label>
                          <label className="flex items-center gap-2 text-xs">
                            <RadioGroupItem value="new" id={`${row.id}-new`} />
                            <span>Nuovo</span>
                          </label>
                          <label className="flex items-center gap-2 text-xs">
                            <RadioGroupItem value="replace" id={`${row.id}-replace`} />
                            <span>Replace</span>
                          </label>
                        </RadioGroup>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <Button
                  onClick={handleSubmitBatchSingleFile}
                  disabled={batchSingleFileMutation.isPending || !batchFile}
                >
                  {batchSingleFileMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Importa file unico
                </Button>
                <div className="text-xs text-muted-foreground">
                  Richiede: nome impresa + colonna prezzo. Quantità opzionale abilita MC mode.
                </div>
              </div>

              {lastResult && (
                <div className="rounded-lg border border-border/70 bg-muted/20 p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="default">Successi {lastResult.success_count}</Badge>
                    <Badge variant="outline">Fallimenti {lastResult.failed_count}</Badge>
                    <Badge variant="secondary">Totale {lastResult.total}</Badge>
                  </div>
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold">Import riusciti</p>
                      {lastResult.success.length ? (
                        <div className="flex flex-wrap gap-2">
                          {lastResult.success.map((impresa) => (
                            <Badge key={impresa} variant="secondary">
                              {impresa}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">Nessuno</p>
                      )}
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-semibold">Errori</p>
                      {lastResult.failed.length ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Impresa</TableHead>
                              <TableHead>Errore</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {lastResult.failed.map((item, idx) => (
                              <TableRow key={`${item.impresa}-${idx}`}>
                                <TableCell className="font-medium">{item.impresa}</TableCell>
                                <TableCell className="text-xs text-muted-foreground">
                                  {item.error}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="text-xs text-muted-foreground">Nessun errore</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Modalità: Import WBS */}
      <TabsContent value="wbs" className="space-y-4">
        <Card className="border-border/70 bg-card/90 shadow-sm">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg font-semibold">Import WBS da Excel</CardTitle>
            <CardDescription>
              Importa/aggiorna la struttura WBS (spaziale, WBS6, WBS7) da un file Excel dedicato.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-4">
              <Label className="text-sm">Modalità</Label>
              <RadioGroup
                value={wbsMode}
                onValueChange={(value) => setWbsMode(value as "create" | "update")}
                className="flex flex-row gap-4"
              >
                <label className="flex items-center gap-2 text-xs">
                  <RadioGroupItem value="create" id="wbs-create" />
                  <span>Crea</span>
                </label>
                <label className="flex items-center gap-2 text-xs">
                  <RadioGroupItem value="update" id="wbs-update" />
                  <span>Aggiorna</span>
                </label>
              </RadioGroup>
            </div>
            <UploadArea
              onFileUpload={async (file) => {
                await wbsImportMutation.mutateAsync({
                  file,
                  mode: wbsMode,
                });
              }}
              submitLabel="Importa WBS"
              hint="Formati: .xlsx, .xls"
              successMessage={null}
              acceptExtensions={[".xlsx", ".xls", ".xlsm"]}
              disabled={wbsImportMutation.isPending}
            />
            <p className="text-xs text-muted-foreground">
              Usa import in modalità <strong>create</strong> per la prima WBS,{" "}
              <strong>update</strong> per aggiornare codici già presenti.
            </p>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
