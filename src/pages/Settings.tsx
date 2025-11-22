import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useQuery } from "@tanstack/react-query";
import { Loader2, RefreshCw, AlertTriangle, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import type { ApiCommessa } from "@/types/api";
import type { ApiNlpModelOption, ApiSettings } from "@/types/api";

const settingsSchema = z.object({
  delta_minimo_critico: z.coerce
    .number()
    .min(-1_000_000, "Il valore deve essere maggiore di -1.000.000")
    .max(0, "Il delta minimo deve essere negativo o zero"),
  delta_massimo_critico: z.coerce
    .number()
    .min(0, "Il delta massimo deve essere positivo o zero")
    .max(1_000_000, "Il valore deve essere minore di 1.000.000"),
  percentuale_cme_alto: z.coerce
    .number()
    .min(0, "La percentuale deve essere positiva")
    .max(100, "La percentuale non puA2 superare 100%"),
  percentuale_cme_basso: z.coerce
    .number()
    .min(0, "La percentuale deve essere positiva")
    .max(100, "La percentuale non puA2 superare 100%"),
  nlp_model_id: z.string().min(1, "Seleziona un modello"),
  nlp_batch_size: z.coerce
    .number()
    .min(4, "Il batch non puA2 essere inferiore a 4")
    .max(256, "Il batch non puA2 superare 256"),
  nlp_max_length: z.coerce
    .number()
    .min(64, "La lunghezza minima deve essere almeno 64 token")
    .max(2048, "La lunghezza massima non puA2 superare 2048 token"),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

export default function Settings() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedCommessaId, setSelectedCommessaId] = useState<string>("all");
  const [regenerating, setRegenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedCommessaPropsId, setSelectedCommessaPropsId] = useState<string>("all");
  const [regeneratingProps, setRegeneratingProps] = useState(false);
  const [progressProps, setProgressProps] = useState(0);
  const [selectedCommessaImpreseId, setSelectedCommessaImpreseId] = useState<string>("all");
  const [normalizingImprese, setNormalizingImprese] = useState(false);
  const [availableModels, setAvailableModels] = useState<ApiNlpModelOption[]>([]);
  const [settingsMeta, setSettingsMeta] = useState<ApiSettings | null>(null);
  const [embeddingsOutdated, setEmbeddingsOutdated] = useState(false);

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      delta_minimo_critico: -30000,
      delta_massimo_critico: 1000,
      percentuale_cme_alto: 25,
      percentuale_cme_basso: 50,
      nlp_model_id: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
      nlp_batch_size: 32,
      nlp_max_length: 256,
    },
  });

  const currentModelId = form.watch("nlp_model_id");
  const selectedModel = availableModels.find((model) => model.id === currentModelId);
  const embeddingModelId = settingsMeta?.nlp_embeddings_model_id ?? null;
  const activeEmbeddingModel = availableModels.find(
    (model) => model.id === embeddingModelId,
  );
  const showRegenerationWarning =
    embeddingsOutdated || (embeddingModelId !== null && embeddingModelId !== currentModelId);

  const { data: commesse } = useQuery<ApiCommessa[]>({
    queryKey: ["commesse"],
    queryFn: () => api.listCommesse(),
  });

  useEffect(() => {
    void loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await api.getSettings();
      setAvailableModels(response.nlp_models);
      setEmbeddingsOutdated(response.nlp_embeddings_outdated);
      setSettingsMeta(response.settings);
      form.reset({
        delta_minimo_critico: response.settings.delta_minimo_critico,
        delta_massimo_critico: response.settings.delta_massimo_critico,
        percentuale_cme_alto: response.settings.percentuale_cme_alto,
        percentuale_cme_basso: response.settings.percentuale_cme_basso,
        nlp_model_id: response.settings.nlp_model_id,
        nlp_batch_size: response.settings.nlp_batch_size,
        nlp_max_length: response.settings.nlp_max_length,
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile caricare le impostazioni. Verifica che il backend sia avviato.";
      toast({ title: "Errore", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (
    values: SettingsFormValues,
    options?: { silent?: boolean },
  ): Promise<boolean> => {
    try {
      setSaving(true);
      const response = await api.updateSettings(values);
      setAvailableModels(response.nlp_models);
      setEmbeddingsOutdated(response.nlp_embeddings_outdated);
      setSettingsMeta(response.settings);
      form.reset({
        delta_minimo_critico: response.settings.delta_minimo_critico,
        delta_massimo_critico: response.settings.delta_massimo_critico,
        percentuale_cme_alto: response.settings.percentuale_cme_alto,
        percentuale_cme_basso: response.settings.percentuale_cme_basso,
        nlp_model_id: response.settings.nlp_model_id,
        nlp_batch_size: response.settings.nlp_batch_size,
        nlp_max_length: response.settings.nlp_max_length,
      });
      if (!options?.silent) {
        toast({ title: "Successo", description: "Impostazioni salvate correttamente" });
      }
      return true;
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile salvare le impostazioni. Verifica che il backend sia avviato.";
      toast({ title: "Errore", description: message, variant: "destructive" });
      return false;
    } finally {
      setSaving(false);
    }
  };
  const onSubmit = async (values: SettingsFormValues) => {
    return saveSettings(values);
  };

  const handleRegenerateEmbeddings = async () => {
    try {
      if (form.formState.isDirty) {
        const pendingToast = toast({
          title: "Salvataggio in corso",
          description: "Applico le modifiche prima di rigenerare gli embedding.",
        });
        const saved = await saveSettings(form.getValues(), { silent: true });
        pendingToast.dismiss();
        if (!saved) {
          return;
        }
        toast({
          title: "Impostazioni applicate",
          description: "Il modello selezionato e' stato salvato. Avvio la rigenerazione.",
        });
      }
      setRegenerating(true);
      setProgress(0);

      // Simula il progresso durante l'operazione
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev; // Si ferma al 90% finchA(c) non arriva la risposta
          return prev + 10;
        });
      }, 500);

      const commessaId = selectedCommessaId === "all" ? undefined : Number(selectedCommessaId);
      const result = await api.regenerateEmbeddings(commessaId);

      clearInterval(progressInterval);
      setProgress(100);

      toast({
        title: "Embedding rigenerati con successo",
        description: `${result.updated} voci aggiornate, ${result.skipped} saltate, ${result.errors} errori`,
      });
      void loadSettings();

      // Reset progress dopo un breve ritardo
      setTimeout(() => setProgress(0), 1000);
    } catch (error) {
      setProgress(0);
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile rigenerare gli embedding. Verifica che il backend sia avviato.";
      toast({ title: "Errore", description: message, variant: "destructive" });
    } finally {
      setRegenerating(false);
    }
  };

  const handleNormalizeImprese = async () => {
    try {
      setNormalizingImprese(true);
      const commessaId = selectedCommessaImpreseId === "all" ? undefined : Number(selectedCommessaImpreseId);
      const result = await api.normalizeImprese(commessaId);
      toast({
        title: "Imprese normalizzate",
        description: `${result.updated}/${result.total} computi aggiornati, errori: ${result.errors}`,
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile normalizzare le imprese.";
      toast({ title: "Errore", description: message, variant: "destructive" });
    } finally {
      setNormalizingImprese(false);
    }
  };

  const handleDownloadModel = async () => {
    const saved = await saveSettings(form.getValues(), { silent: true });
    if (saved) {
      toast({
        title: "Modello aggiornato",
        description: `Il modello ${selectedModel?.label ?? form.getValues().nlp_model_id} e pronto all'uso.`,
      });
    }
  };

  const handleRegenerateProperties = async () => {
    try {
      setRegeneratingProps(true);
      setProgressProps(0);

      const progressInterval = setInterval(() => {
        setProgressProps((prev) => (prev >= 90 ? prev : prev + 10));
      }, 500);

      const commessaId = selectedCommessaPropsId === "all" ? undefined : Number(selectedCommessaPropsId);
      const result = await api.regenerateProperties(commessaId);

      clearInterval(progressInterval);
      setProgressProps(100);

      toast({
        title: "Proprietà rigenerate",
        description: `${result.updated} voci aggiornate, ${result.skipped} senza dati, ${result.errors} errori`,
      });

      setTimeout(() => setProgressProps(0), 1000);
    } catch (error) {
      setProgressProps(0);
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile rigenerare le proprietà estratte.";
      toast({ title: "Errore", description: message, variant: "destructive" });
    } finally {
      setRegeneratingProps(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/30">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex-1 space-y-6 bg-muted/30 p-8">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-semibold tracking-tight">Impostazioni</h1>
            <p className="text-sm text-muted-foreground">
              Configura i parametri per l&apos;analisi dei computi e dei ritorni di gara
            </p>
          </div>
        </div>

        <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Parametri Delta Critico</CardTitle>
            <CardDescription>
              Definisci le soglie per identificare automaticamente le voci critiche nei confronti
              tra progetto e offerte delle imprese.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="delta_minimo_critico"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Delta Minimo Critico (EUR)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="-30000.00" {...field} />
                    </FormControl>
                    <FormDescription>
                      Prezzi gara bassi se delta minore di questo valore (valore negativo)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="delta_massimo_critico"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Delta Massimo Critico (EUR)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="1000.00" {...field} />
                    </FormControl>
                    <FormDescription>
                      Prezzi gara alti se delta maggiore di questo valore (valore positivo)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="percentuale_cme_alto"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Percentuale CME Alto (%)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="25.00" {...field} />
                    </FormControl>
                    <FormDescription>
                      CME considerato alto se delta percentuale maggiore di questo valore
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="percentuale_cme_basso"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Percentuale CME Basso (%)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="50.00" {...field} />
                    </FormControl>
                    <FormDescription>
                      CME considerato basso se delta percentuale minore di questo valore
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 border-t border-border/60 pt-4">
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Salva impostazioni
              </Button>
              <Button type="button" variant="outline" onClick={() => form.reset()} disabled={saving}>
                Ripristina
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Ricerca semantica e modelli AI</CardTitle>
            <CardDescription>Configura e controlla lo stato dei modelli utilizzati per gli embedding.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
          <div className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/5 to-primary/10 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="flex items-center gap-2 text-sm font-semibold">
                  <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                  Modello degli embedding salvati
                </p>
                <p className="text-xs text-muted-foreground">Gli embedding nel database sono stati calcolati con questo modello.</p>
              </div>
              {activeEmbeddingModel && (
                <Badge variant="secondary">{activeEmbeddingModel.dimension} dim</Badge>
              )}
            </div>
            <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <p className="text-muted-foreground">Modello</p>
                <p className="font-semibold">{activeEmbeddingModel?.label ?? "Rigenera per applicare il nuovo modello"}</p>
                <p className="font-mono text-xs text-muted-foreground">{activeEmbeddingModel?.id ?? embeddingModelId ?? "N/D"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Lingue supportate</p>
                <p className="font-semibold">{activeEmbeddingModel?.languages ?? "N/D"}</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold">Configurazione modello</h4>
            <FormField
              control={form.control}
              name="nlp_model_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Seleziona modello</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange} disabled={saving}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Scegli un modello" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {availableModels.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div className="flex flex-col items-start">
                            <span className="font-semibold">{model.label}</span>
                            <span className="text-xs text-muted-foreground">{model.speed} aEURc {model.dimension} dim</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>Modelli piu grandi offrono risultati migliori ma richiedono piu risorse.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {selectedModel && (
              <div className="rounded-xl border border-dashed border-border/70 p-3 text-xs text-muted-foreground">
                <p className="text-foreground font-semibold">{selectedModel.label}</p>
                <p className="font-mono">{selectedModel.id}</p>
                <p>
                  {selectedModel.dimension} dim | {selectedModel.speed} | {selectedModel.languages}
                </p>
                <p className="mt-1">{selectedModel.description}</p>
              </div>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="nlp_batch_size"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Batch size</FormLabel>
                    <FormControl>
                      <Input type="number" min={4} max={256} disabled={saving} {...field} />
                    </FormControl>
                    <FormDescription>Elementi processati in parallelo durante il calcolo degli embedding.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="nlp_max_length"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max length</FormLabel>
                    <FormControl>
                      <Input type="number" min={64} max={2048} disabled={saving} {...field} />
                    </FormControl>
                    <FormDescription>Lunghezza massima del testo passato al modello NLP.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="flex flex-wrap gap-3 border-t border-border/60 pt-4">
              <Button type="button" variant="outline" onClick={handleDownloadModel} disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Download className="mr-2 h-4 w-4" />
                Salva e scarica modello
              </Button>
            </div>
          </div>

          {showRegenerationWarning && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Rigenerazione consigliata</AlertTitle>
              <AlertDescription>Gli embedding salvati non sono allineati con il modello selezionato. Rigenera per ottenere risultati coerenti.</AlertDescription>
            </Alert>
          )}

          <div className="border-t pt-4">
            <h4 className="mb-3 text-sm font-semibold">Rigenera embedding</h4>
            <p className="text-sm text-muted-foreground mb-4">Esegui dopo aver cambiato il modello o se gli embedding non sono stati calcolati durante l&apos;importazione.</p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="flex-1">
                <Select value={selectedCommessaId} onValueChange={setSelectedCommessaId} disabled={regenerating}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleziona commessa" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tutte le commesse</SelectItem>
                    {commesse?.map((commessa) => (
                      <SelectItem key={commessa.id} value={String(commessa.id)}>{commessa.codice} - {commessa.nome}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                type="button"
                onClick={handleRegenerateEmbeddings}
                disabled={regenerating}
                variant="default"
              >
                {regenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Rigenerazione in corso...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Rigenera Embedding
                  </>
                )}
              </Button>
            </div>
            {regenerating && (
              <div className="space-y-2 pt-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Progresso</span>
                  <span className="font-mono font-semibold">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Normalizza imprese (ritorni)</CardTitle>
          <CardDescription>
            Rimuove suffissi duplicati (es. “(2)”) e riallinea offerte e computi all'impresa normalizzata.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex-1">
              <Select value={selectedCommessaImpreseId} onValueChange={setSelectedCommessaImpreseId} disabled={normalizingImprese}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona commessa" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le commesse</SelectItem>
                  {commesse?.map((commessa) => (
                    <SelectItem key={commessa.id} value={String(commessa.id)}>
                      {commessa.codice} - {commessa.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              type="button"
              onClick={handleNormalizeImprese}
              disabled={normalizingImprese}
              variant="outline"
            >
              {normalizingImprese ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Normalizzazione...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Normalizza imprese
                </>
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Usa questa azione dopo import multipli per eliminare etichette duplicate e allineare i filtri per impresa.
          </p>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Ricalcolo proprietà estratte</CardTitle>
          <CardDescription>
            Rielabora le voci di elenco prezzi con gli estrattori roBERT per popolare le proprietà mancanti.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Esegui dopo nuovi import o se il dettaglio non mostra proprietà estratte.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex-1">
              <Select value={selectedCommessaPropsId} onValueChange={setSelectedCommessaPropsId} disabled={regeneratingProps}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona commessa" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le commesse</SelectItem>
                  {commesse?.map((commessa) => (
                    <SelectItem key={commessa.id} value={String(commessa.id)}>
                      {commessa.codice} - {commessa.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              type="button"
              onClick={handleRegenerateProperties}
              disabled={regeneratingProps}
              variant="default"
            >
              {regeneratingProps ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Rigenerazione in corso...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Rigenera Proprietà
                </>
              )}
            </Button>
          </div>
          {regeneratingProps && (
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Progresso</span>
                <span className="font-mono font-semibold">{progressProps}%</span>
              </div>
              <Progress value={progressProps} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Guida rapida ai parametri</CardTitle>
          <CardDescription>Come vengono utilizzati questi parametri</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <h4 className="mb-2 text-sm font-semibold">Delta in Euro</h4>
            <p className="text-muted-foreground">
              I valori di delta minimo e massimo vengono usati per identificare voci con scarti
              monetari significativi rispetto al progetto, indipendentemente dalla percentuale.
            </p>
          </div>
          <div>
            <h4 className="mb-2 text-sm font-semibold">Percentuali CME</h4>
            <p className="text-muted-foreground">
              Le percentuali vengono usate per classificare le voci in base allo scarto relativo,
              identificando automaticamente le criticitA  nell&apos;analisi dei ritorni di gara.
            </p>
          </div>
          <div>
            <h4 className="mb-2 text-sm font-semibold">Livelli di criticitA </h4>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>
                <strong>Critica:</strong> Delta oltre le soglie massime definite
              </li>
              <li>
                <strong>Alta:</strong> Delta significativo ma entro le soglie
              </li>
              <li>
                <strong>Media:</strong> Delta moderato (circa 10-25%)
              </li>
              <li>
                <strong>Bassa:</strong> Delta minimo (&lt;10%)
              </li>
            </ul>
          </div>
        </CardContent>
        </Card>
      </form>
    </Form>
  );
}




