import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Settings2,
  FileText,
  Upload,
  Trash2,
  Save,
  AlertTriangle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import {
  ApiCommessaPreferences,
  ApiSixPreventivoOption,
  ApiImportConfig,
  ApiImportConfigCreate,
} from "@/types/api";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
import { useCommessaContext } from "@/hooks/useCommessaContext";

type ToastFn = ReturnType<typeof useToast>["toast"];

export default function CommessaSettings() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams();
  const commessaId = Number(id);
  const isValidId = Number.isFinite(commessaId);

  const [activeTab, setActiveTab] = useState("general");

  // Queries
  const { commessa } = useCommessaContext();

  const preferencesQuery = useQuery<ApiCommessaPreferences>({
    queryKey: ["commesse", commessaId, "preferences"],
    queryFn: () => api.getCommessaPreferences(commessaId),
    enabled: isValidId,
  });

  const importConfigsQuery = useQuery<ApiImportConfig[]>({
    queryKey: ["import-configs", commessaId],
    queryFn: () => api.listImportConfigs({ commessaId }),
    enabled: isValidId,
  });

  // Mutations
  const updatePreferencesMutation = useMutation({
    mutationFn: (payload: {
      selected_preventivo_id?: string | null;
      selected_price_list_id?: string | null;
      default_wbs_view?: string | null;
    }) => api.updateCommessaPreferences(commessaId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commesse", commessaId, "preferences"] });
      toast({
        title: "Preferenze salvate",
        description: "Le preferenze della commessa sono state aggiornate.",
      });
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Errore",
        description: error.message || "Impossibile salvare le preferenze.",
      });
    },
  });

  const deleteImportConfigMutation = useMutation<void, Error, number>({
    mutationFn: (configId: number) => api.deleteImportConfig(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["import-configs", commessaId] });
      toast({
        title: "Configurazione eliminata",
        description: "La configurazione di import è stata rimossa.",
      });
    },
  });

  const updateImportConfigMutation = useMutation<
    ApiImportConfig,
    Error,
    { configId: number; payload: ApiImportConfigCreate }
  >({
    mutationFn: ({
      configId,
      payload,
    }: {
      configId: number;
      payload: ApiImportConfigCreate;
    }) => api.updateImportConfig(configId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["import-configs", commessaId] });
      toast({
        title: "Configurazione aggiornata",
        description: "Le impostazioni di import sono state salvate.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Errore salvataggio",
        description: error.message || "Impossibile aggiornare la configurazione.",
        variant: "destructive",
      });
    },
  });

  if (!isValidId) {
    return (
      <div className="flex-1 bg-muted/30 p-8 text-sm text-destructive">
        ID commessa non valido. Torna alla lista e riprova.
      </div>
    );
  }

  const preferences = preferencesQuery.data;
  const importConfigs = importConfigsQuery.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Impostazioni Commessa"
        description="Configura preferenze, preventivi, elenco prezzi e gestisci la commessa."
        backHref={`/commesse/${commessaId}/overview`}
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general" className="gap-2">
            <Settings2 className="h-4 w-4" />
            Generale
          </TabsTrigger>
          <TabsTrigger value="preventivo" className="gap-2">
            <FileText className="h-4 w-4" />
            Preventivo/Listini
          </TabsTrigger>
          <TabsTrigger value="import" className="gap-2">
            <Upload className="h-4 w-4" />
            Configurazioni Import
          </TabsTrigger>
          <TabsTrigger value="danger" className="gap-2">
            <Trash2 className="h-4 w-4" />
            Gestione
          </TabsTrigger>
        </TabsList>

        {/* Tab Generale */}
        <TabsContent value="general" className="space-y-4">
          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle>Informazioni Generali</CardTitle>
              <CardDescription>
                Visualizza e modifica le informazioni di base della commessa.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Nome</Label>
                  <div className="text-sm font-medium">{commessa?.nome ?? "—"}</div>
                </div>
                <div className="space-y-2">
                  <Label>Codice</Label>
                  <div className="text-sm font-medium">{commessa?.codice ?? "—"}</div>
                </div>
                <div className="space-y-2">
                  <Label>Business Unit</Label>
                  <div className="text-sm font-medium">{commessa?.business_unit ?? "—"}</div>
                </div>
                <div className="space-y-2">
                  <Label>Stato</Label>
                  <div className="text-sm font-medium uppercase">{commessa?.stato ?? "—"}</div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Descrizione</Label>
                <div className="text-sm text-muted-foreground">
                  {commessa?.descrizione || "Nessuna descrizione disponibile"}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle>Vista WBS Predefinita</CardTitle>
              <CardDescription>
                Seleziona quale vista WBS utilizzare per default nelle analisi.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="wbs-view">Vista Predefinita</Label>
                <Select
                  value={preferences?.default_wbs_view || "wbs6"}
                  onValueChange={(value) =>
                    updatePreferencesMutation.mutate({ default_wbs_view: value })
                  }
                  disabled={updatePreferencesMutation.isPending}
                >
                  <SelectTrigger id="wbs-view">
                    <SelectValue placeholder="Seleziona vista WBS" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="spaziale">WBS Spaziale</SelectItem>
                    <SelectItem value="wbs6">WBS6 (Categorie)</SelectItem>
                    <SelectItem value="wbs7">WBS7 (Sottocategorie)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Questa impostazione verrà utilizzata come default nelle pagine di analisi.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Preventivo/Listini */}
        <TabsContent value="preventivo" className="space-y-4">
          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle>Preventivo STR Vision</CardTitle>
              <CardDescription>
                Seleziona quale preventivo dal file STR Vision utilizzare come riferimento.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="preventivo-select">Preventivo Primario</Label>
                <Input
                  id="preventivo-select"
                  value={preferences?.selected_preventivo_id || ""}
                  onChange={(e) =>
                    updatePreferencesMutation.mutate({
                      selected_preventivo_id: e.target.value || null,
                    })
                  }
                  placeholder="ID del preventivo (es: 'preventivo_1')"
                  disabled={updatePreferencesMutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  Lascia vuoto per usare il preventivo di default dal file STR Vision.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle>Elenco Prezzi</CardTitle>
              <CardDescription>
                Seleziona quale listino prezzi utilizzare come riferimento primario.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="pricelist-select">Listino Prezzi Primario</Label>
                <Input
                  id="pricelist-select"
                  value={preferences?.selected_price_list_id || ""}
                  onChange={(e) =>
                    updatePreferencesMutation.mutate({
                      selected_price_list_id: e.target.value || null,
                    })
                  }
                  placeholder="ID del listino (es: 'listino_1')"
                  disabled={updatePreferencesMutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  Lascia vuoto per usare tutti i listini disponibili.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Configurazioni Import */}
        <TabsContent value="import" className="space-y-4">
          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle>Configurazioni Salvate</CardTitle>
              <CardDescription>
                Gestisci le configurazioni di import per i ritorni di gara Excel.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {importConfigs.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border/60 bg-muted/30 p-8 text-center">
                  <p className="text-sm text-muted-foreground">
                    Nessuna configurazione salvata. Crea una nuova configurazione durante
                    l'import di un ritorno di gara.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {importConfigs.map((config) => (
                    <ImportConfigEditor
                      key={config.id}
                      config={config}
                      toast={toast}
                      onDelete={() => deleteImportConfigMutation.mutate(config.id)}
                      onSave={(payload) =>
                        updateImportConfigMutation.mutateAsync({ configId: config.id, payload })
                      }
                      saving={
                        updateImportConfigMutation.isPending &&
                        updateImportConfigMutation.variables?.configId === config.id
                      }
                      deleting={
                        deleteImportConfigMutation.isPending &&
                        deleteImportConfigMutation.variables === config.id
                      }
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Gestione (Danger Zone) */}
        <TabsContent value="danger" className="space-y-4">
          <Card className="rounded-2xl border-2 border-destructive/50 bg-card shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5" />
                Zona Pericolosa
              </CardTitle>
              <CardDescription>
                Azioni irreversibili che modificano o eliminano la commessa.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Elimina Commessa</h4>
                  <p className="mb-4 text-sm text-muted-foreground">
                    Elimina definitivamente questa commessa e tutti i dati associati
                    (computi, ritorni, configurazioni). Questa azione è irreversibile.
                  </p>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive" className="gap-2">
                        <Trash2 className="h-4 w-4" />
                        Elimina Commessa
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Conferma eliminazione commessa</AlertDialogTitle>
                        <AlertDialogDescription>
                          Stai per eliminare la commessa "{commessa?.nome}" (codice:{" "}
                          {commessa?.codice}). Tutti i computi, ritorni di gara,
                          configurazioni e preferenze verranno eliminati definitivamente.
                          <br />
                          <br />
                          <strong>Questa azione NON può essere annullata.</strong>
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Annulla</AlertDialogCancel>
                        <AlertDialogAction
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                          onClick={() => {
                            // TODO: Implement delete commessa
                            toast({
                              title: "Funzione non implementata",
                              description: "L'eliminazione della commessa verrà implementata.",
                            });
                          }}
                        >
                          Elimina Definitivamente
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

type ImportConfigFormState = {
  nome: string;
  impresa: string;
  sheet_name: string;
  code_columns: string;
  description_columns: string;
  price_column: string;
  quantity_column: string;
  note: string;
};

const buildFormState = (config: ApiImportConfig): ImportConfigFormState => ({
  nome: config.nome ?? "",
  impresa: config.impresa ?? "",
  sheet_name: config.sheet_name ?? "",
  code_columns: (config.code_columns ?? "").toUpperCase(),
  description_columns: (config.description_columns ?? "").toUpperCase(),
  price_column: (config.price_column ?? "").toUpperCase(),
  quantity_column: (config.quantity_column ?? "").toUpperCase(),
  note: config.note ?? "",
});

const normalizeColumnToken = (value: string) =>
  value.replace(/^\$/, "").trim().toUpperCase();

const serializeColumnList = (value: string): string | null => {
  const tokens = value
    .split(/[,;\s]+/)
    .map(normalizeColumnToken)
    .filter(Boolean);
  return tokens.length ? tokens.join(",") : null;
};

const serializeSingleColumn = (value: string): string | null => {
  const token = normalizeColumnToken(value);
  return token ? token : null;
};

interface ImportConfigEditorProps {
  config: ApiImportConfig;
  onDelete: () => void;
  onSave: (payload: ApiImportConfigCreate) => Promise<void | ApiImportConfig>;
  toast: ToastFn;
  saving?: boolean;
  deleting?: boolean;
}

function ImportConfigEditor({
  config,
  onDelete,
  onSave,
  toast,
  saving,
  deleting,
}: ImportConfigEditorProps) {
  const [form, setForm] = useState<ImportConfigFormState>(() => buildFormState(config));
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setForm(buildFormState(config));
    setDirty(false);
  }, [config]);

  const handleChange = (field: keyof ImportConfigFormState, value: string, opts?: { uppercase?: boolean }) => {
    setForm((prev) => ({
      ...prev,
      [field]: opts?.uppercase ? value.toUpperCase() : value,
    }));
    setDirty(true);
  };

  const handleSave = async () => {
    const nome = form.nome.trim();
    if (!nome) {
      toast({
        variant: "destructive",
        title: "Nome obbligatorio",
        description: "Assegna un nome descrittivo alla configurazione.",
      });
      return;
    }
    const codeColumns = serializeColumnList(form.code_columns);
    const descriptionColumns = serializeColumnList(form.description_columns);
    const priceColumn = serializeSingleColumn(form.price_column || "");
    const payload: ApiImportConfigCreate = {
      nome,
      impresa: form.impresa.trim() || null,
      sheet_name: form.sheet_name.trim() || null,
      code_columns: codeColumns,
      description_columns: descriptionColumns,
      price_column: priceColumn,
      quantity_column: serializeSingleColumn(form.quantity_column || ""),
      note: form.note.trim() || null,
    };
    try {
      await onSave(payload);
      setDirty(false);
    } catch {
      /* errors handled upstream */
    }
  };

  const scopeLabel = config.commessa_id ? "Solo questa commessa" : "Configurazione globale";
  const disableSave = saving;

  return (
    <div className="space-y-4 rounded-lg border border-border/60 bg-card p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold">{config.nome}</p>
          <p className="text-xs text-muted-foreground">{scopeLabel}</p>
        </div>
        <div className="text-xs text-muted-foreground">
          Aggiornata il {new Date(config.updated_at).toLocaleDateString("it-IT")} alle{" "}
          {new Date(config.updated_at).toLocaleTimeString("it-IT")}
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <Label>Nome configurazione</Label>
          <Input
            value={form.nome}
            onChange={(e) => handleChange("nome", e.target.value)}
            placeholder="Formato Impresa"
          />
        </div>
        <div className="space-y-1">
          <Label>Impresa associata</Label>
          <Input
            value={form.impresa}
            onChange={(e) => handleChange("impresa", e.target.value)}
            placeholder="Es: EXA"
          />
        </div>
        <div className="space-y-1">
          <Label>Foglio Excel</Label>
          <Input
            value={form.sheet_name}
            onChange={(e) => handleChange("sheet_name", e.target.value)}
            placeholder="Nome del foglio"
          />
        </div>
        <div className="space-y-1">
          <Label>Colonne codice</Label>
          <Input
            value={form.code_columns}
            onChange={(e) => handleChange("code_columns", e.target.value, { uppercase: true })}
            placeholder="Es: A,B"
          />
        </div>
        <div className="space-y-1">
          <Label>Colonne descrizione</Label>
          <Input
            value={form.description_columns}
            onChange={(e) =>
              handleChange("description_columns", e.target.value, { uppercase: true })
            }
            placeholder="Es: C"
          />
        </div>
        <div className="space-y-1">
          <Label>Colonna prezzo unitario</Label>
          <Input
            value={form.price_column}
            onChange={(e) => handleChange("price_column", e.target.value, { uppercase: true })}
            placeholder="Es: J"
          />
        </div>
        <div className="space-y-1">
          <Label>Colonna quantità (opzionale)</Label>
          <Input
            value={form.quantity_column}
            onChange={(e) =>
              handleChange("quantity_column", e.target.value, { uppercase: true })
            }
            placeholder="Es: H"
          />
        </div>
        <div className="md:col-span-2 space-y-1">
          <Label>Note</Label>
          <Textarea
            value={form.note}
            onChange={(e) => handleChange("note", e.target.value)}
            placeholder="Informazioni aggiuntive o istruzioni"
          />
        </div>
      </div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <p className="text-xs text-muted-foreground">
          ID config: {config.id} · Creato il{" "}
          {new Date(config.created_at).toLocaleDateString("it-IT")}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          {dirty && !saving ? (
            <span className="text-xs font-semibold text-amber-600">
              Modifiche non salvate
            </span>
          ) : (
            <span className="text-xs text-muted-foreground">Ultimo salvataggio confermato</span>
          )}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" disabled={deleting}>
                <Trash2 className="mr-2 h-4 w-4" />
                Elimina
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Conferma eliminazione</AlertDialogTitle>
                <AlertDialogDescription>
                  Sei sicuro di voler eliminare la configurazione "{config.nome}"?
                  Questa azione non può essere annullata.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annulla</AlertDialogCancel>
                <AlertDialogAction onClick={onDelete}>Elimina</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <Button onClick={handleSave} disabled={disableSave}>
            {saving ? "Salvataggio..." : "Salva configurazione"}
          </Button>
        </div>
      </div>
    </div>
  );
}
