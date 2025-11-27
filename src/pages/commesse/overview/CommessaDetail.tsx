import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Clock3, Euro, Layers3, Pencil, Settings2, Trash2 } from "lucide-react";
import { ModificaCommessaDialog } from "@/features/commessa";
import { RoundUploadDialog } from "@/components/RoundUploadDialog";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import { formatCurrency, formatShortDate, formatDateTime, groupComputi } from "@/lib/formatters";
import { ApiImportConfig, ApiSixImportReport } from "@/types/api";
import { CommessaPageHeader } from "@/features/commessa";
import { CommessaSummaryStrip } from "@/features/commessa";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

type RoundDetail = {
  round: number;
  imprese: string[];
};

type ProgettoUploadPayload = {
  file: File;
  tipo: "excel" | "six";
  preventivoId?: string;
  enableEmbeddings?: boolean;
  enablePropertyExtraction?: boolean;
};

type DocumentDraft = {
  tipo: "progetto" | "ritorno" | "listino";
  impresa: string;
  round: string;
  preventivoId: string;
  sheetName: string;
  configId: string;
  mode: "lc" | "mc";
};

const NONE_CONFIG_VALUE = "__none__";

const CommessaDetail = () => {
  const { id } = useParams();
  const commessaId = Number(id);
  const commessaIdKey = Number.isFinite(commessaId) ? String(commessaId) : "";
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [impresaName, setImpresaName] = useState("");
  const [drafts, setDrafts] = useState<Record<number, DocumentDraft>>({});
  const [editingDocId, setEditingDocId] = useState<number | null>(null);

  const { commessa, refetchCommessa } = useCommessaContext();

  const { data: importConfigs = [] } = useQuery<ApiImportConfig[]>({
    queryKey: ["import-configs", commessaIdKey],
    queryFn: () => api.listImportConfigs({ commessaId }),
    enabled: Number.isFinite(commessaId),
    staleTime: 60_000,
  });

  const invalidateCommessaData = useCallback(async () => {
    if (!Number.isFinite(commessaId)) return;
    const promises: Promise<unknown>[] = [
      Promise.resolve(refetchCommessa()),
    ];
    if (commessaIdKey) {
      promises.push(
        queryClient.invalidateQueries({ queryKey: ["confronto", commessaIdKey] }),
        queryClient.invalidateQueries({ queryKey: ["analisi", commessaIdKey] }),
      );
    }
    await Promise.all(promises);
  }, [commessaId, commessaIdKey, queryClient, refetchCommessa]);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadComputoProgetto(commessaId, file),
    onSuccess: async () => {
      await invalidateCommessaData();
      toast({
        title: "Computo caricato",
        description: "Il computo metrico è stato importato correttamente.",
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'import del file";
      toast({
        title: "Upload fallito",
        description: message,
        variant: "destructive",
      });
    },
  });

  const ritornoUploadMutation = useMutation({
    mutationFn: ({
      file,
      impresa,
      roundNumber,
      mode,
      sheetName,
      codeColumns,
      descriptionColumns,
      priceColumn,
      quantityColumn,
      wbs6CodeColumn,
      wbs6DescriptionColumn,
    }: {
      file: File;
      impresa: string;
      roundNumber: number;
      mode: "new" | "replace";
    sheetName: string;
    codeColumns: string[];
    descriptionColumns: string[];
    priceColumn: string;
    quantityColumn?: string;
    wbs6CodeColumn?: string;
    wbs6DescriptionColumn?: string;
    progressColumn?: string;
  }) =>
      api.uploadRitorno(commessaId, {
        file,
        impresa,
        roundMode: mode,
        roundNumber,
        sheetName,
        codeColumns,
        descriptionColumns,
        priceColumn,
        quantityColumn,
      }),
    onSuccess: async () => {
      await invalidateCommessaData();
      toast({
        title: "Ritorno caricato",
        description: "Il ritorno di gara è stato importato correttamente.",
      });
      setImpresaName("");
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'import del ritorno";
      toast({
        title: "Upload fallito",
        description: message,
        variant: "destructive",
      });
    },
  });
  const sixImportMutation = useMutation<ApiSixImportReport, unknown, { file: File; preventivoId?: string; enableEmbeddings?: boolean; enablePropertyExtraction?: boolean }>({
    mutationFn: ({ file, preventivoId, enableEmbeddings, enablePropertyExtraction }) =>
      api.importSixFile(commessaId, file, preventivoId, { enableEmbeddings, enablePropertyExtraction }),
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
      toast({
        title: "Import fallito",
        description: message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (computoId: number) => api.deleteComputo(commessaId, computoId),
    onSuccess: async () => {
      await invalidateCommessaData();
      toast({
        title: "Computo eliminato",
        description: "Il computo è stato eliminato correttamente.",
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'eliminazione";
      toast({
        title: "Eliminazione fallita",
        description: message,
        variant: "destructive",
      });
    },
  });

  const updateCommessaMutation = useMutation({
    mutationFn: (payload: Parameters<typeof api.updateCommessa>[1]) =>
      api.updateCommessa(commessaId, payload),
    onSuccess: async () => {
      await invalidateCommessaData();
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Errore durante l'aggiornamento";
      toast({
        title: "Aggiornamento fallito",
        description: message,
        variant: "destructive",
      });
    },
  });

  const documents = useMemo(() => {
    return (commessa?.computi ?? []).map((c) => {
      const lowerName = (c.file_nome ?? "").toLowerCase();
      const format = lowerName.endsWith(".six") || lowerName.endsWith(".xml")
        ? "STR Vision"
        : lowerName.endsWith(".xlsx") || lowerName.endsWith(".xls")
          ? "Excel"
          : "Non specificato";
      const mode: "lc" | "mc" = c.tipo === "progetto" ? "mc" : "lc";
      return {
        id: c.id,
        nome: c.nome,
        tipo: c.tipo,
        impresa: c.impresa ?? "",
        round: c.round_number ? String(c.round_number) : "",
        source: c.file_nome ?? "—",
        format,
        mode,
      };
    });
  }, [commessa?.computi]);

  useEffect(() => {
    if (!documents.length) {
      setDrafts({});
      return;
    }
    setDrafts((prev) => {
      const next: Record<number, DocumentDraft> = { ...prev };
      documents.forEach((doc) => {
        if (!next[doc.id]) {
          next[doc.id] = {
            tipo: doc.tipo,
            impresa: doc.impresa,
            round: doc.round,
            preventivoId: "",
            sheetName: "",
            configId: "",
            mode: doc.mode,
          };
        }
      });
      return next;
    });
  }, [documents]);

  const updateDraft = useCallback((id: number, patch: Partial<DocumentDraft>) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: { ...prev[id], ...patch },
    }));
  }, []);

  const handleApplyDraft = useCallback(
    (id: number) => {
      const draft = drafts[id];
      if (!draft) return;
      toast({
        title: "Metadati aggiornati",
        description:
          "Le modifiche ai metadati sono applicate localmente. Collega qui l'endpoint backend quando sarà disponibile.",
      });
    },
    [drafts, toast],
  );

  const { progetto, ritorni } = useMemo(
    () => groupComputi(commessa?.computi ?? []),
    [commessa?.computi],
  );

  const handlePreviewPreventivi = async (file: File) => {
    const preview = await api.previewSixPreventivi(commessaId, file);
    return preview.preventivi ?? [];
  };

  const handleUploadProgetto = async ({
    file,
    tipo,
    preventivoId,
    enableEmbeddings,
    enablePropertyExtraction,
  }: ProgettoUploadPayload) => {
    if (tipo === "excel") {
      await uploadMutation.mutateAsync(file);
      return;
    }
    await sixImportMutation.mutateAsync({
      file,
      preventivoId,
      enableEmbeddings,
      enablePropertyExtraction,
    });
  };

  const handleUploadRitorno = async (params: {
    file: File;
    impresa: string;
    roundNumber: number;
    mode: "new" | "replace";
    sheetName: string;
    codeColumns: string[];
    descriptionColumns: string[];
    priceColumn: string;
    quantityColumn?: string;
    wbs6CodeColumn?: string;
    wbs6DescriptionColumn?: string;
    progressColumn?: string;
  }) => {
    await ritornoUploadMutation.mutateAsync(params);
  };


  const roundDetails: RoundDetail[] = useMemo(() => {
    const map = new Map<number, Set<string>>();

    commessa?.computi
      ?.filter((c) => c.tipo === "ritorno")
      .forEach((computo) => {
        const round = computo.round_number ?? 1;
        if (!map.has(round)) {
          map.set(round, new Set<string>());
        }
        if (computo.impresa) {
          map.get(round)!.add(computo.impresa);
        }
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

  const handleDeleteComputo = async (computoId: number, computoName: string) => {
    if (!confirm(`Sei sicuro di voler eliminare il computo "${computoName}"?`)) {
      return;
    }
    await deleteMutation.mutateAsync(computoId);
  };

  const handleUpdateCommessa = async (payload: Parameters<typeof api.updateCommessa>[1]) => {
    await updateCommessaMutation.mutateAsync(payload);
  };

  const updatedAt = commessa?.updated_at ?? commessa?.created_at ?? null;

  const summaryMetrics = useMemo(() => {
    const projectImporto = progetto[0]?.importo_totale ?? null;
    const roundsHelper =
      roundDetails.length === 0
        ? "Nessun round attivo"
        : roundDetails.length === 1
          ? `Round ${roundDetails[0].round}`
          : `Round ${roundDetails[0].round} - ${roundDetails[roundDetails.length - 1].round}`;

    return [
      {
        label: "Importo totale",
        value: projectImporto ? formatCurrency(projectImporto) : "—",
        helper: progetto[0]?.nome ? `da ${progetto[0].nome}` : undefined,
        icon: <Euro className="h-5 w-5 text-primary" />,
        emphasise: true,
      },
      {
        label: "Computi caricati",
        value: String(commessa?.computi?.length ?? 0),
        helper: `${progetto.length} progetto · ${ritorni.length} ritorni`,
        icon: <Layers3 className="h-5 w-5 text-primary" />,
      },
      {
        label: "Round attivi",
        value: String(roundDetails.length),
        helper: roundsHelper,
        icon: <BarChart3 className="h-5 w-5 text-primary" />,
      },
      {
        label: "Ultimo aggiornamento",
        value: formatShortDate(updatedAt),
        helper: formatDateTime(updatedAt),
        icon: <Clock3 className="h-5 w-5 text-primary" />,
      },
    ];
  }, [commessa?.computi?.length, progetto, ritorni, roundDetails, updatedAt]);

  const editingDoc = editingDocId ? documents.find((d) => d.id === editingDocId) : null;

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Computo & riepilogo"
        description="Gestisci i documenti di progetto e i ritorni di gara."
      >
        <CommessaSummaryStrip metrics={summaryMetrics} />
      </CommessaPageHeader>

      {/* Card documenti unificata */}
      <div className="rounded-2xl border border-border/60 bg-card/80 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 px-4 py-3">
          <div className="space-y-0.5">
            <h3 className="text-base font-semibold text-foreground">Documenti</h3>
            <p className="text-sm text-muted-foreground">
              {documents.length} documento/i caricato/i
            </p>
          </div>
          <div className="flex items-center gap-2">
            <RoundUploadDialog
              commessaId={commessa?.id ?? commessaId}
              onUploadProgetto={handleUploadProgetto}
              onPreviewPreventivi={handlePreviewPreventivi}
              onUploadRitorno={handleUploadRitorno}
              existingRounds={existingRounds}
              roundDetails={roundDetails}
              disabled={
                uploadMutation.isPending ||
                ritornoUploadMutation.isPending ||
                sixImportMutation.isPending
              }
              triggerProps={{
                className: "gap-2",
                variant: "default",
              }}
            />
            {commessa && (
              <ModificaCommessaDialog commessa={commessa} onUpdate={handleUpdateCommessa} />
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Tipo</TableHead>
                <TableHead>Documento</TableHead>
                <TableHead>Impresa</TableHead>
                <TableHead className="w-[80px]">Round</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead className="w-[120px] text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                    Nessun documento caricato. Usa il pulsante "Carica" per importare un computo.
                  </TableCell>
                </TableRow>
              )}
              {documents.map((doc) => {
                const computo = commessa?.computi?.find((c) => c.id === doc.id);
                return (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <Badge
                        variant={doc.tipo === "progetto" ? "default" : "secondary"}
                        className={doc.tipo === "progetto" ? "bg-primary/90" : ""}
                      >
                        {doc.tipo === "progetto" ? "Progetto" : "Ritorno"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-0.5">
                        <div className="font-medium text-foreground">{doc.nome}</div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{doc.format}</span>
                          <span>•</span>
                          <span className="truncate max-w-[200px]">{doc.source}</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {doc.impresa || <span className="text-muted-foreground">—</span>}
                    </TableCell>
                    <TableCell className="text-sm">
                      {doc.round || <span className="text-muted-foreground">—</span>}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {computo?.importo_totale ? formatCurrency(computo.importo_totale) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setEditingDocId(doc.id)}
                          title="Modifica metadati"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => handleDeleteComputo(doc.id, doc.nome)}
                          disabled={deleteMutation.isPending}
                          title="Elimina"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Dialog per modifica metadati */}
      <Dialog open={!!editingDocId} onOpenChange={(open) => !open && setEditingDocId(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5" />
              Modifica metadati
            </DialogTitle>
            <DialogDescription>
              {editingDoc?.nome ?? "Documento"}
            </DialogDescription>
          </DialogHeader>

          {editingDoc && drafts[editingDoc.id] && (
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="tipo">Tipo documento</Label>
                <Select
                  value={drafts[editingDoc.id]?.tipo ?? editingDoc.tipo}
                  onValueChange={(value) =>
                    updateDraft(editingDoc.id, { tipo: value as DocumentDraft["tipo"] })
                  }
                >
                  <SelectTrigger id="tipo">
                    <SelectValue placeholder="Tipo documento" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="progetto">Progetto</SelectItem>
                    <SelectItem value="ritorno">Ritorno di gara</SelectItem>
                    <SelectItem value="listino">Listino</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="impresa">Impresa</Label>
                <Input
                  id="impresa"
                  placeholder="Nome impresa"
                  value={drafts[editingDoc.id]?.impresa ?? editingDoc.impresa}
                  onChange={(e) => updateDraft(editingDoc.id, { impresa: e.target.value })}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="round">Round</Label>
                <Input
                  id="round"
                  placeholder="Numero round"
                  value={drafts[editingDoc.id]?.round ?? editingDoc.round}
                  onChange={(e) => updateDraft(editingDoc.id, { round: e.target.value })}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="config">Configurazione import</Label>
                <Select
                  value={drafts[editingDoc.id]?.configId || NONE_CONFIG_VALUE}
                  onValueChange={(value) =>
                    updateDraft(editingDoc.id, { configId: value === NONE_CONFIG_VALUE ? "" : value })
                  }
                >
                  <SelectTrigger id="config">
                    <SelectValue placeholder="Configurazione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE_CONFIG_VALUE}>Nessuna configurazione</SelectItem>
                    {importConfigs.map((config) => (
                      <SelectItem key={config.id} value={String(config.id)}>
                        {config.nome || `Config ${config.id}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>Modalità</Label>
                <ToggleGroup
                  type="single"
                  value={drafts[editingDoc.id]?.mode ?? editingDoc.mode}
                  onValueChange={(value) => {
                    if (!value) return;
                    updateDraft(editingDoc.id, { mode: value as "lc" | "mc" });
                  }}
                  className="justify-start"
                >
                  <ToggleGroupItem value="lc">LC</ToggleGroupItem>
                  <ToggleGroupItem value="mc">MC</ToggleGroupItem>
                </ToggleGroup>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingDocId(null)}>
              Annulla
            </Button>
            <Button
              onClick={() => {
                if (editingDocId) {
                  handleApplyDraft(editingDocId);
                  setEditingDocId(null);
                }
              }}
            >
              Salva modifiche
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CommessaDetail;
