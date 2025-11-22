import { useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Clock3, Euro, Layers3 } from "lucide-react";
import { ModificaCommessaDialog } from "@/components/ModificaCommessaDialog";
import { ComputoTreeItem } from "@/components/ComputoTreeView";
import { RoundUploadDialog } from "@/components/RoundUploadDialog";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import { formatCurrency, formatShortDate, formatDateTime, groupComputi } from "@/lib/formatters";
import { ApiSixImportReport } from "@/types/api";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
import {
  CommessaSummaryStrip,
  QuickActionsCard,
  RecentActivityCard,
  ComputoListCard,
  type ActivityItem,
} from "@/components/commessa";
import { useCommessaContext } from "@/hooks/useCommessaContext";

type RoundDetail = {
  round: number;
  imprese: string[];
};

type ProgettoUploadPayload = {
  file: File;
  tipo: "excel" | "six";
  preventivoId?: string;
};

const CommessaDetail = () => {
  const { id } = useParams();
  const commessaId = Number(id);
  const commessaIdKey = Number.isFinite(commessaId) ? String(commessaId) : "";
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [impresaName, setImpresaName] = useState("");

  const { commessa, refetchCommessa } = useCommessaContext();

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
  const sixImportMutation = useMutation<ApiSixImportReport, unknown, { file: File; preventivoId?: string }>({
    mutationFn: ({ file, preventivoId }) => api.importSixFile(commessaId, file, preventivoId),
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
  }: ProgettoUploadPayload) => {
    if (tipo === "excel") {
      await uploadMutation.mutateAsync(file);
      return;
    }
    await sixImportMutation.mutateAsync({ file, preventivoId });
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

  const computoTreeItems: ComputoTreeItem[] = useMemo(() => {
    return (commessa?.computi ?? []).map((c) => ({
      id: c.id,
      nome: c.nome,
      tipo: c.tipo,
      impresa: c.impresa,
      round_number: c.round_number,
      importo_totale: c.importo_totale,
      created_at: c.created_at,
    }));
  }, [commessa?.computi]);

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

  const recentActivity: ActivityItem[] = useMemo(() => {
    return [...(commessa?.computi ?? [])]
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )
      .slice(0, 5)
      .map((computo) => ({
        id: computo.id,
        title: computo.nome,
        meta:
          computo.tipo === "progetto"
            ? "Computo di progetto"
            : `Ritorno round ${computo.round_number ?? "-"}`,
        timestamp: formatDateTime(computo.updated_at),
      }));
  }, [commessa?.computi]);

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Computo e riepilogo"
        description="Gestisci il computo di progetto e i ritorni di gara collegati."
      >
        <CommessaSummaryStrip metrics={summaryMetrics} />
      </CommessaPageHeader>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)]">
        <div className="space-y-4">
          <ComputoListCard
            computi={computoTreeItems}
            onDeleteComputo={handleDeleteComputo}
            isDeleting={deleteMutation.isPending}
          />
        </div>

        <div className="space-y-4">
          <QuickActionsCard
            headerAction={
              commessa && (
                <ModificaCommessaDialog commessa={commessa} onUpdate={handleUpdateCommessa} />
              )
            }
            uploadAction={
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
                  className: "w-full justify-center gap-2",
                  size: "default",
                }}
              />
            }
          />

          <RecentActivityCard activities={recentActivity} />
        </div>
      </div>
    </div>
  );
};

export default CommessaDetail;
