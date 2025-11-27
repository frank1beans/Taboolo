import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Search, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { WbsVisibilitySection } from "@/features/wbs/components/WbsVisibilitySection";
import { buildVisibilitySections } from "@/features/wbs/utils";
import { api } from "@/lib/api-client";
import { ApiCommessaWbs, ApiWbsVisibilityEntry } from "@/types/api";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { CommessaPageHeader } from "@/features/commessa";

export default function CommessaWbsSettings() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams();
  const commessaId = Number(id);
  const isValidId = Number.isFinite(commessaId);

  const [search, setSearch] = useState("");

  const visibilityQueryKey = ["commesse", commessaId, "wbs", "visibility"];

  const { commessa } = useCommessaContext();

  const wbsQuery = useQuery<ApiCommessaWbs>({
    queryKey: ["commesse", commessaId, "wbs", "structure"],
    queryFn: () => api.getCommessaWbsStructure(commessaId),
    enabled: isValidId,
  });

  const visibilityQuery = useQuery<ApiWbsVisibilityEntry[]>({
    queryKey: visibilityQueryKey,
    queryFn: () => api.getWbsVisibility(commessaId),
    enabled: isValidId,
  });

  const visibilityMutation = useMutation({
    mutationFn: (payload: { level: number; node_id: number; hidden: boolean }[]) =>
      api.updateWbsVisibility(commessaId, payload),
    onSuccess: (data, variables) => {
      queryClient.setQueryData<ApiWbsVisibilityEntry[]>(visibilityQueryKey, data);
      toast({
        description:
          variables.length > 1
            ? "Visibilità aggiornata per il raggruppatore selezionato."
            : "Preferenza salvata.",
      });
    },
    onError: (error: Error) =>
      toast({
        variant: "destructive",
        description: error.message || "Impossibile aggiornare la visibilità.",
      }),
  });

  const sections = useMemo(
    () =>
      buildVisibilitySections({
        spaziali: wbsQuery.data?.spaziali ?? [],
        wbs6: wbsQuery.data?.wbs6 ?? [],
        wbs7: wbsQuery.data?.wbs7 ?? [],
        visibility: visibilityQuery.data ?? [],
      }),
    [visibilityQuery.data, wbsQuery.data?.spaziali, wbsQuery.data?.wbs6, wbsQuery.data?.wbs7],
  );

  const filteredSections = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) {
      return sections;
    }
    return sections.map((section) => ({
      ...section,
      nodes: section.nodes.filter((node) => {
        const codeMatch = node.code.toLowerCase().includes(term);
        const descriptionMatch = (node.description ?? "").toLowerCase().includes(term);
        return codeMatch || descriptionMatch;
      }),
    }));
  }, [sections, search]);

  const allNodes = useMemo(
    () => sections.flatMap((section) => section.nodes),
    [sections],
  );
  const visibleCount = allNodes.filter((node) => !node.hidden).length;
  const hiddenCount = allNodes.length - visibleCount;

  const isLoading =
    wbsQuery.isLoading || visibilityQuery.isLoading;
  const isFetching = wbsQuery.isFetching || visibilityQuery.isFetching;
  const isMutating = visibilityMutation.isPending;

  const handleToggle = (level: number, nodeId: number, makeVisible: boolean) => {
    visibilityMutation.mutate([{ level, node_id: nodeId, hidden: !makeVisible }]);
  };

  const handleSectionBulk = (level: number, hide: boolean) => {
    const section = sections.find((item) => item.level === level);
    if (!section) return;
    const targets = section.nodes.filter((node) => (hide ? !node.hidden : node.hidden));
    if (!targets.length) return;
    visibilityMutation.mutate(
      targets.map((node) => ({ level, node_id: node.id, hidden: hide })),
    );
  };

  if (!isValidId) {
    return (
      <div className="text-sm text-destructive">Commessa non valida. Torna alla lista e riprova.</div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Visibilità WBS"
        description={
          commessa
            ? `Seleziona i raggruppatori da mostrare per ${commessa.nome}.`
            : "Caricamento commessa in corso..."
        }
        backHref={`/commesse/${commessaId}/overview`}
        variant="compact"
      />

      <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Raggruppatori canonici dal file SIX
          </CardTitle>
          <CardDescription>
            Le WBS sono importate in sola lettura dal file STR Vision. Usa le
            preferenze di visibilità per includere o escludere categorie nelle
            analisi. Tutti i nodi sono visibili di default.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Badge variant="secondary">Totali {allNodes.length}</Badge>
          <Badge variant="default">Visibili {visibleCount}</Badge>
          <Badge variant="outline">Nascosti {hiddenCount}</Badge>
        </CardContent>
      </Card>

      <Card className="rounded-xl border border-border/60 bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Ricerca rapida</CardTitle>
          <CardDescription>
            Filtra i nodi per codice o descrizione. Il filtro è applicato a tutti i
            raggruppatori.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Es. A001, Lotto A, Livello 02..."
              className="pl-9"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {(isLoading || isFetching) && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Sincronizzazione in corso...
        </div>
      )}

      {filteredSections.length === 0 && !isLoading ? (
        <div className="rounded-2xl border border-dashed border-border/60 bg-card p-6 text-center text-sm text-muted-foreground">
          Nessun raggruppatore disponibile. Importa un file STR Vision per iniziare.
        </div>
      ) : (
        filteredSections.map((section) => (
          <WbsVisibilitySection
            key={section.level}
            section={section}
            disabled={isMutating}
            onToggle={(nodeId, visible) => handleToggle(section.level, nodeId, visible)}
            onShowAll={() => handleSectionBulk(section.level, false)}
            onHideAll={() => handleSectionBulk(section.level, true)}
          />
        ))
      )}
    </div>
  );
}
