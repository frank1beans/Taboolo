import { ChangeEvent, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowUpRight,
  Building2,
  Download,
  FolderKanban,
  FolderOpen,
  Layers3,
  ListChecks,
  Loader2,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NuovaCommessaDialog, CommessaData } from "@/features/commessa";
import { ExplorerBreadcrumb, FolderGrid } from "@/components/folder-explorer";
import { api } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { formatShortDate } from "@/lib/formatters";
import { STATUS_CONFIG, BADGE_VARIANT_STYLES } from "@/lib/constants";
import { PageShell } from "@/components/layout/PageShell";
import { GenericBadge } from "@/components/ui/status-badge";
import { ApiCommessa, CommessaStato } from "@/types/api";
import { useToast } from "@/hooks/use-toast";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

type FolderContext =
  | { type: "root" }
  | { type: "businessUnit"; value: string | null }
  | { type: "status"; value: CommessaStato };

const Commesse = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState("");
  const [deletingCommessaId, setDeletingCommessaId] = useState<number | null>(null);
  const [exportingCommessaId, setExportingCommessaId] = useState<number | null>(null);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filterType = searchParams.get("filter");
  const filterValue = searchParams.get("value");

  const currentContext: FolderContext = useMemo(() => {
    if (filterType === "businessUnit") {
      return { type: "businessUnit", value: filterValue || null };
    }
    if (filterType === "status") {
      return { type: "status", value: filterValue as CommessaStato };
    }
    return { type: "root" };
  }, [filterType, filterValue]);

  const commesseQuery = useQuery<ApiCommessa[]>({
    queryKey: ["commesse"],
    queryFn: () => api.listCommesse(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: CommessaData) =>
      api.createCommessa({
        nome: payload.nomeCommessa,
        codice: payload.numeroCommessa,
        descrizione: payload.descrizione,
        business_unit: payload.businessUnit || null,
        revisione: payload.revisione || null,
        note: null,
        stato: "setup",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commesse"] });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Impossibile creare la commessa";
      toast({
        title: "Errore", 
        description: message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (commessaId: number) => api.deleteCommessa(commessaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commesse"] });
      toast({
        title: "Commessa eliminata",
        description: "La commessa e stata eliminata correttamente.",
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

  const importBundleMutation = useMutation({
    mutationFn: (params: { file: File; overwrite: boolean }) =>
      api.importCommessaBundle(params.file, { overwrite: params.overwrite }),
    onSuccess: (commessa) => {
      queryClient.invalidateQueries({ queryKey: ["commesse"] });
      toast({
        title: "Pacchetto importato",
        description: `"${commessa.nome}" e stato creato o aggiornato`,
      });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Import fallita";
      toast({
        title: "Impossibile importare il pacchetto",
        description: message,
        variant: "destructive",
      });
    },
  });

  const handleCommessaCreated = async (data: CommessaData) => {
    await createMutation.mutateAsync(data);
  };

  const handleDeleteCommessa = async (commessa: ApiCommessa) => {
    const confirmed = confirm(
      `Sei sicuro di voler eliminare la commessa "${commessa.nome}"?\nTutti i computi associati saranno rimossi.`,
    );
    if (!confirmed) return;
    setDeletingCommessaId(commessa.id);
    try {
      await deleteMutation.mutateAsync(commessa.id);
    } catch (error) {
      console.error("Failed to delete commessa", error);
    } finally {
      setDeletingCommessaId((current) => (current === commessa.id ? null : current));
    }
  };

  const handleExportCommessa = async (commessa: ApiCommessa) => {
    setExportingCommessaId(commessa.id);
    try {
      const { blob, filename } = await api.exportCommessaBundle(commessa.id);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      toast({
        title: "Pacchetto esportato",
        description: `Download di ${filename} completato`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Esportazione fallita";
      toast({
        title: "Impossibile esportare la commessa",
        description: message,
        variant: "destructive",
      });
    } finally {
      setExportingCommessaId((current) => (current === commessa.id ? null : current));
    }
  };

  const handleBundleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await importBundleMutation.mutateAsync({ file, overwrite: overwriteExisting });
    } finally {
      event.target.value = "";
    }
  };

  const triggerBundlePicker = () => {
    fileInputRef.current?.click();
  };

  const getContextLabel = (context: FolderContext) => {
    if (context.type === "businessUnit") {
      return context.value ? context.value : "Senza Business Unit";
    }
    if (context.type === "status") {
      return STATUS_CONFIG[context.value].label;
    }
    return "Portfolio";
  };

  const breadcrumbItems = [{ label: getContextLabel(currentContext) }];

  const handleOpenContext = (context: FolderContext) => {
    const params = new URLSearchParams();
    if (context.type === "businessUnit") {
      params.set("filter", "businessUnit");
      if (context.value) params.set("value", context.value);
    } else if (context.type === "status") {
      params.set("filter", "status");
      params.set("value", context.value);
    }
    navigate(params.toString() ? `/commesse?${params.toString()}` : "/commesse");
    setSearchQuery("");
  };

  const handleBreadcrumbNavigate = () => {
    navigate("/commesse");
    setSearchQuery("");
  };

  const commesse = useMemo(() => commesseQuery.data ?? [], [commesseQuery.data]);

  const recentCommesse = useMemo(() => {
    return [...commesse]
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )
      .slice(0, 5);
  }, [commesse]);

  const businessUnitFolders = useMemo(() => {
    const map = new Map<string, { label: string; value: string | null; items: ApiCommessa[] }>();
    commesse.forEach((commessa) => {
      const value = commessa.business_unit?.trim() || null;
      const key = value ?? "__none__";
      if (!map.has(key)) {
        map.set(key, { label: value ?? "Senza Business Unit", value, items: [] });
      }
      map.get(key)!.items.push(commessa);
    });
    return Array.from(map.values()).sort((a, b) => a.label.localeCompare(b.label));
  }, [commesse]);

  const statusFolders = useMemo(() => {
    return (["setup", "in_corso", "chiusa"] as CommessaStato[]).map((status) => ({
      status,
      count: commesse.filter((c) => c.stato === status).length,
      label: STATUS_CONFIG[status].label,
      description: STATUS_CONFIG[status].description,
      badgeVariant: STATUS_CONFIG[status].badgeVariant,
    }));
  }, [commesse]);

  const commesseForContext = useMemo(() => {
    if (currentContext.type === "businessUnit") {
      return commesse.filter((commessa) => {
        const value = commessa.business_unit?.trim() || null;
        return value === (currentContext.value ?? null);
      });
    }
    if (currentContext.type === "status") {
      return commesse.filter((commessa) => commessa.stato === currentContext.value);
    }
    return [];
  }, [commesse, currentContext]);

  const visibleCommesse = useMemo(() => {
    if (currentContext.type === "root") return [];
    if (!searchQuery.trim()) return commesseForContext;
    const query = searchQuery.toLowerCase();
    return commesseForContext.filter((commessa) =>
      [commessa.nome, commessa.codice, commessa.descrizione]
        .filter(Boolean)
        .some((field) => field!.toLowerCase().includes(query)),
    );
  }, [commesseForContext, currentContext.type, searchQuery]);

  const businessUnitTiles = businessUnitFolders.map((folder) => ({
    id: `bu-${folder.value ?? "none"}`,
    title: folder.label,
    subtitle: `${folder.items.length} commesse`,
    description: "Cartella business unit",
    icon: <Building2 className="h-5 w-5" />,
    meta: folder.value ? "Cartella dedicata" : "Cartella di default",
    onOpen: () => handleOpenContext({ type: "businessUnit", value: folder.value }),
  }));

  const statusTiles = statusFolders.map((folder) => ({
    id: `status-${folder.status}`,
    title: folder.label,
    subtitle: folder.description,
    icon: <Layers3 className="h-5 w-5" />,
    badge: {
      label: folder.label,
      variant: folder.badgeVariant,
    },
    meta: `${folder.count} commesse`,
    onOpen: () => handleOpenContext({ type: "status", value: folder.status }),
  }));

  const commessaTiles = visibleCommesse.map((commessa) => {
    const isDeletingThisCommessa =
      deleteMutation.isPending && deletingCommessaId === commessa.id;
    return {
      id: `commessa-${commessa.id}`,
      title: commessa.nome,
      subtitle: commessa.codice,
      description: commessa.descrizione ?? undefined,
      icon: <FolderKanban className="h-5 w-5" />,
      badge: {
        label: STATUS_CONFIG[commessa.stato].label,
        variant: STATUS_CONFIG[commessa.stato].badgeVariant,
      },
      meta: `Agg. ${formatShortDate(commessa.updated_at)}`,
      onOpen: () => navigate(`/commesse/${commessa.id}/overview`),
      actions: [
        {
          label: "Apri",
          icon: <ArrowUpRight className="h-3 w-3" />,
          onClick: () => navigate(`/commesse/${commessa.id}/overview`),
        },
        {
          label: "WBS",
          icon: <Layers3 className="h-3 w-3" />,
          onClick: () => navigate(`/commesse/${commessa.id}/wbs`),
        },
        {
          label: "Listini",
          icon: <ListChecks className="h-3 w-3" />,
          onClick: () => navigate(`/commesse/${commessa.id}/price-catalog`),
        },
        {
          label: exportingCommessaId === commessa.id ? "Esporto..." : "Esporta bundle",
          icon: exportingCommessaId === commessa.id ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Download className="h-3 w-3" />
          ),
          onClick: () => handleExportCommessa(commessa),
          disabled: exportingCommessaId === commessa.id,
        },
        {
          label: isDeletingThisCommessa ? "Eliminazione..." : "Elimina",
          icon: isDeletingThisCommessa ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Trash2 className="h-3 w-3 text-destructive" />
          ),
          onClick: () => handleDeleteCommessa(commessa),
          disabled: isDeletingThisCommessa,
        },
      ],
    };
  });

  if (commesseQuery.isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/30">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (commesseQuery.isError) {
    const errorMessage =
      commesseQuery.error instanceof Error
        ? commesseQuery.error.message
        : "Errore durante il caricamento delle commesse.";
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/30 p-8">
        <Card className="flex max-w-md flex-col items-center gap-4 rounded-2xl border border-border/60 bg-card p-8 text-center shadow-md">
          <AlertCircle className="h-10 w-10 text-destructive" />
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Impossibile caricare le commesse</h2>
            <p className="text-sm text-muted-foreground">{errorMessage}</p>
          </div>
          <Button
            onClick={() => commesseQuery.refetch()}
            disabled={commesseQuery.isRefetching}
          >
            {commesseQuery.isRefetching ? "Riprovo..." : "Riprova"}
          </Button>
        </Card>
      </div>
    );
  }

  const isRoot = currentContext.type === "root";

  const pageTitle =
    currentContext.type === "businessUnit"
      ? `Business Unit: ${currentContext.value || "Tutte"}`
      : currentContext.type === "status"
        ? `Stato: ${STATUS_CONFIG[currentContext.value].label}`
        : "Commesse";

  const pageDescription =
    currentContext.type === "businessUnit"
      ? `Commesse della Business Unit ${currentContext.value || "Tutte"}`
      : currentContext.type === "status"
        ? STATUS_CONFIG[currentContext.value].description
        : "Gestione completa delle commesse";

  const toolbarContent = (
    <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      {!isRoot ? (
        <div className="relative w-full sm:w-[260px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Cerca in questa cartella..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            className="h-9 pl-9"
          />
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Naviga per cartella o stato, crea una nuova commessa senza perdere l&apos;header.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <NuovaCommessaDialog onCommessaCreated={handleCommessaCreated} />
      </div>
    </div>
  );

  return (
    <PageShell
      title={pageTitle}
      description={pageDescription}
      breadcrumb={<ExplorerBreadcrumb items={breadcrumbItems} onNavigate={handleBreadcrumbNavigate} />}
      toolbar={toolbarContent}
      bodyClassName="flex flex-col gap-3 overflow-hidden"
    >
      <div className="workspace-panel workspace-panel--flush border border-primary/25 bg-primary/5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <h3 className="workspace-section-title">Pacchetti commessa</h3>
            <p className="text-sm text-muted-foreground">
              Importa archivi .mmcomm; l&apos;import non sovrascrive se non abiliti l&apos;opzione.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={triggerBundlePicker}
                disabled={importBundleMutation.isPending}
                className="h-9"
              >
                {importBundleMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                {importBundleMutation.isPending ? "Importo..." : "Importa pacchetto"}
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".mmcomm"
                onChange={handleBundleFileChange}
                className="hidden"
              />
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-primary/25 bg-background/80 px-3 py-2">
              <Switch
                id="overwrite-toggle"
                checked={overwriteExisting}
                onCheckedChange={setOverwriteExisting}
              />
              <div className="space-y-0.5">
                <Label htmlFor="overwrite-toggle" className="text-sm">
                  Sovrascrivi se esiste
                </Label>
                <p className="text-[11px] text-muted-foreground">
                  Disattivato per evitare sostituzioni accidentali.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {isRoot ? (
        <div className="workspace-grid">
          <div className="workspace-panel workspace-panel--scroll space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="workspace-section-title">Business Unit</h3>
                  <p className="text-xs text-muted-foreground">
                    Cartelle generate automaticamente dalle business unit rilevate.
                  </p>
                </div>
                <span className="rounded-md border border-border/60 px-2 py-1 text-[11px] text-muted-foreground">
                  {businessUnitFolders.length} cartelle
                </span>
              </div>
              {businessUnitTiles.length <= 2 ? (
                <div className="space-y-2">
                  {businessUnitFolders.length ? (
                    businessUnitFolders.map((folder) => (
                      <button
                        key={folder.value ?? "none"}
                        type="button"
                        onClick={() => handleOpenContext({ type: "businessUnit", value: folder.value })}
                        className="flex w-full items-center justify-between rounded-xl border border-border/70 bg-background/80 px-4 py-3 text-left transition hover:border-primary/40 hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <div className="rounded-lg bg-primary/10 p-2 text-primary">
                            <Building2 className="h-4 w-4" />
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-foreground">{folder.label}</p>
                            <p className="text-xs text-muted-foreground">
                              {folder.items.length} commesse
                            </p>
                          </div>
                        </div>
                        <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                      </button>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-border/60 bg-muted/30 p-5 text-center text-sm text-muted-foreground">
                      Nessuna business unit disponibile.
                    </div>
                  )}
                </div>
              ) : (
                <FolderGrid
                  items={businessUnitTiles}
                  emptyContent={
                    <Card className="rounded-2xl border border-border/60 bg-muted/30 p-6 text-center text-sm text-muted-foreground">
                      Nessuna business unit disponibile.
                    </Card>
                  }
                />
              )}
            </div>

            <div className="space-y-2 border-t border-dashed border-border/60 pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="workspace-section-title">Stato commesse</h3>
                  <p className="text-xs text-muted-foreground">
                    Naviga per stato operativo e apri rapidamente i progetti.
                  </p>
                </div>
                <span className="rounded-md border border-border/60 px-2 py-1 text-[11px] text-muted-foreground">
                  {commesse.length} totali
                </span>
              </div>
              <FolderGrid items={statusTiles} />
            </div>
          </div>

          {recentCommesse.length ? (
            <div className="workspace-panel workspace-panel--scroll space-y-3">
              <div>
                <h3 className="workspace-section-title">Commesse recenti</h3>
                <p className="text-xs text-muted-foreground">
                  Ultimi aggiornamenti registrati nelle cartelle.
                </p>
              </div>
              <div className="divide-y divide-border/60">
                {recentCommesse.map((commessa) => (
                  <button
                    key={commessa.id}
                    type="button"
                    onClick={() => navigate(`/commesse/${commessa.id}/overview`)}
                    className="flex w-full items-center justify-between gap-3 px-1 py-2 text-left transition hover:bg-muted/40"
                  >
                    <div>
                      <p className="text-sm font-semibold text-foreground">{commessa.nome}</p>
                      <p className="text-xs text-muted-foreground">{commessa.codice}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <GenericBadge
                        label={STATUS_CONFIG[commessa.stato].label}
                        variant={STATUS_CONFIG[commessa.stato].badgeVariant}
                        size="xs"
                      />
                      <span className="text-[10px] text-muted-foreground">
                        Agg. {formatShortDate(commessa.updated_at)}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="workspace-panel workspace-panel--scroll">
          <FolderGrid
            title={getContextLabel(currentContext)}
            description="Seleziona una commessa per aprirla oppure utilizza le azioni rapide disponibili."
            items={commessaTiles}
            emptyContent="Nessuna commessa presente in questa cartella."
          />
        </div>
      )}
    </PageShell>
  );
};

export default Commesse;
