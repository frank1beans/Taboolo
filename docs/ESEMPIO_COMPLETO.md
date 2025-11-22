# 🚀 Esempio Completo: Lista Commesse con UX Perfetta

Questo esempio mostra come creare una pagina completa con tutti gli stati UX gestiti correttamente.

## Prima (❌ Senza Best Practices)

```tsx
// ❌ VERSIONE VECCHIA - Da evitare
function CommessePageOld() {
  const { data } = useCommesse();

  return (
    <div>
      <h1>Commesse</h1>
      {data?.map(c => <div key={c.id}>{c.nome}</div>)}
    </div>
  );
}

// Problemi:
// - Nessun loading state
// - Nessuna gestione errori
// - Nessun empty state
// - Nessuna azione per utente
// - UX scadente
```

## Dopo (✅ Con Best Practices)

```tsx
// ✅ VERSIONE NUOVA - Best Practice
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FolderOpen, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  DataStateHandler,
  ConfirmationDialog,
  StatusBadge,
  InfoTooltip,
} from "@/components/ui";

function CommessePageNew() {
  const navigate = useNavigate();
  const { data, isLoading, isError, refetch } = useCommesse();
  const deleteMutation = useDeleteCommessa();

  // Stato per dialog di conferma
  const [deleteDialog, setDeleteDialog] = useState({
    open: false,
    commessa: null as any,
  });

  // Handler eliminazione
  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(deleteDialog.commessa.id);
      toast.success("Commessa eliminata con successo");
      setDeleteDialog({ open: false, commessa: null });
      refetch();
    } catch (error) {
      toast.error("Impossibile eliminare la commessa");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header con azioni */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold">Commesse</h1>
            <InfoTooltip
              content="Gestisci tutte le tue commesse in un unico posto. Crea, modifica e organizza computi metrici e preventivi."
              side="right"
            />
          </div>
          <p className="text-muted-foreground text-lg">
            Gestione centralizzata di tutti i progetti
          </p>
        </div>

        <Button
          size="lg"
          onClick={() => navigate("/commesse/new")}
          className="gap-2"
        >
          <Plus className="h-5 w-5" />
          Nuova Commessa
        </Button>
      </div>

      {/* Lista con gestione automatica stati */}
      <DataStateHandler
        data={data}
        isLoading={isLoading}
        isError={isError}
        // Empty state config
        emptyIcon={FolderOpen}
        emptyTitle="Nessuna commessa trovata"
        emptyDescription="Inizia creando la tua prima commessa per gestire computi metrici e preventivi in modo efficiente. Potrai importare dati, generare report e confrontare offerte."
        emptyActionLabel="Crea Prima Commessa"
        onEmptyAction={() => navigate("/commesse/new")}
        // Loading config
        loadingMessage="Caricamento elenco commesse..."
        // Error config
        errorTitle="Errore nel caricamento delle commesse"
        errorMessage="Non siamo riusciti a recuperare l'elenco delle commesse. Controlla la connessione internet e riprova."
        onRetry={refetch}
      >
        {(commesse) => (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {commesse.map((commessa) => (
              <Card
                key={commessa.id}
                variant="interactive"
                onClick={() => navigate(`/commesse/${commessa.id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="line-clamp-1">
                        {commessa.nome}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        Cliente: {commessa.cliente}
                      </CardDescription>
                    </div>
                    <StatusBadge
                      status={getCommessaStatus(commessa)}
                      label={getCommessaStatusLabel(commessa)}
                    />
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="space-y-3">
                    {/* Info principali */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-muted-foreground">Computi</p>
                        <p className="font-semibold">{commessa.computiCount}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Importo</p>
                        <p className="font-semibold">
                          {formatCurrency(commessa.importo)}
                        </p>
                      </div>
                    </div>

                    {/* Azioni */}
                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/commesse/${commessa.id}`);
                        }}
                      >
                        Visualizza
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteDialog({
                            open: true,
                            commessa,
                          });
                        }}
                        className="text-destructive hover:bg-destructive/10"
                        aria-label="Elimina commessa"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </DataStateHandler>

      {/* Dialog conferma eliminazione */}
      <ConfirmationDialog
        open={deleteDialog.open}
        onOpenChange={(open) =>
          !open && setDeleteDialog({ open: false, commessa: null })
        }
        title="Eliminare la commessa?"
        description={`Stai per eliminare "${deleteDialog.commessa?.nome}". Questa azione non può essere annullata. Tutti i dati associati (computi, preventivi, analisi) verranno eliminati permanentemente.`}
        confirmLabel="Elimina Definitivamente"
        cancelLabel="Annulla"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </div>
  );
}

// Helper functions
function getCommessaStatus(commessa: any) {
  if (commessa.isCompleted) return "success";
  if (commessa.hasErrors) return "error";
  if (commessa.needsReview) return "warning";
  if (commessa.isProcessing) return "loading";
  return "pending";
}

function getCommessaStatusLabel(commessa: any) {
  if (commessa.isCompleted) return "Completata";
  if (commessa.hasErrors) return "Errori";
  if (commessa.needsReview) return "Da Revisionare";
  if (commessa.isProcessing) return "In Elaborazione";
  return "In Attesa";
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export default CommessePageNew;
```

## Cosa abbiamo ottenuto? 🎯

### 1. **Loading State** ⏳
- Skeleton loader durante caricamento
- Messaggio chiaro "Caricamento elenco commesse..."
- Nessuno schermo bianco

### 2. **Error State** ⚠️
- Messaggio di errore chiaro
- Pulsante "Riprova"
- Istruzioni per risolvere

### 3. **Empty State** 📭
- Icona descrittiva
- Messaggio incoraggiante
- Call-to-action chiaro: "Crea Prima Commessa"
- Descrizione di cosa può fare l'utente

### 4. **Success State** ✅
- Cards ben organizzate
- Status badge colorati
- Informazioni chiare
- Azioni immediate

### 5. **Conferme Azioni Critiche** 🛡️
- Dialog prima di eliminare
- Descrizione chiara delle conseguenze
- Doppia conferma

### 6. **Help Contestuale** 💡
- Tooltip su titolo pagina
- Spiegazione funzionalità

### 7. **Feedback Utente** 📢
- Toast success dopo eliminazione
- Toast error se fallisce
- Aggiornamento immediato lista

### 8. **Accessibilità** ♿
- ARIA labels
- Navigazione da tastiera
- Screen reader friendly
- Focus states visibili

## Differenze Chiave

| Aspetto | Prima ❌ | Dopo ✅ |
|---------|----------|---------|
| **Loading** | Schermo bianco | Skeleton + messaggio |
| **Errori** | Nulla o crash | Error card + retry |
| **Lista vuota** | Nulla | Empty state + CTA |
| **Eliminazione** | Immediata | Conferma + feedback |
| **Help** | Nessuno | Tooltip informativi |
| **Feedback** | Nessuno | Toast notifications |
| **Accessibilità** | Basic | WCAG AA compliant |
| **UX Mobile** | Problematica | Responsive perfetto |

## Esperienza Utente

### Utente 60enne 👴
- ✅ Testi grandi e leggibili
- ✅ Pulsanti grandi e facili da cliccare
- ✅ Messaggi chiari in italiano
- ✅ Conferme prima di eliminare
- ✅ Help sempre disponibile
- ✅ Nessuna sorpresa o schermata oscura

### Utente 20enne 👨‍💻
- ✅ Design moderno e pulito
- ✅ Animazioni fluide
- ✅ Dark mode disponibile
- ✅ Responsive su mobile
- ✅ Fast e performante
- ✅ Tooltip non invasivi

### Entrambi vedono l'app come:
- 🎯 **Affidabile**: Sempre feedback, mai perdita dati
- 🚀 **Moderna**: Design attuale, smooth interactions
- 💪 **Professionale**: Gestione errori, conferme, help
- ⚡ **Veloce**: Loading states, skeleton loaders
- 🎨 **Pulita**: Interfaccia ordinata e consistente

## Altri Esempi Rapidi

### Form con Validazione

```tsx
function CommessaForm() {
  const [showConfirm, setShowConfirm] = useState(false);
  const [formData, setFormData] = useState({ nome: "", cliente: "" });

  return (
    <>
      <form onSubmit={(e) => { e.preventDefault(); setShowConfirm(true); }}>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Label>Nome Commessa</Label>
            <InfoTooltip content="Inserisci un nome descrittivo" />
          </div>
          <Input
            value={formData.nome}
            onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
            placeholder="es. Ristrutturazione Edificio A"
          />
        </div>
        <Button type="submit" size="lg" className="mt-6">
          Salva Commessa
        </Button>
      </form>

      <ConfirmationDialog
        open={showConfirm}
        onOpenChange={setShowConfirm}
        title="Salvare la commessa?"
        description="Conferma per creare la nuova commessa."
        onConfirm={async () => {
          await saveCommessa(formData);
          toast.success("Commessa creata!");
        }}
      />
    </>
  );
}
```

### Importazione File

```tsx
function ImportDialog() {
  const [file, setFile] = useState(null);
  const importMutation = useImportFile();

  const handleImport = async () => {
    const toastId = toast.loading("Importazione in corso...");

    try {
      const result = await importMutation.mutateAsync(file);
      toast.success(
        `✅ File importato! ${result.rows} righe elaborate.`,
        { id: toastId }
      );
    } catch (error) {
      toast.error(
        "❌ Errore importazione. Controlla il formato del file.",
        { id: toastId }
      );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Label>Seleziona File</Label>
        <InfoTooltip content="Formati supportati: .xlsx, .csv, .xls" />
      </div>

      <Input
        type="file"
        accept=".xlsx,.csv,.xls"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <Button
        onClick={handleImport}
        disabled={!file || importMutation.isLoading}
        size="lg"
      >
        {importMutation.isLoading ? "Importazione..." : "Importa File"}
      </Button>
    </div>
  );
}
```

## Conclusione

Questo approccio garantisce:

1. ✅ **Nessuna confusione**: L'utente sa sempre cosa sta succedendo
2. ✅ **Nessuna perdita dati**: Conferme prima di azioni critiche
3. ✅ **Nessuna frustrazione**: Empty states con azioni chiare
4. ✅ **Nessun errore silenzioso**: Sempre feedback visibile
5. ✅ **Massima accessibilità**: Funziona per tutti

**Risultato**: Un'app che sia il 20enne che il 60enne trovano **affidabile, moderna e facile da usare**! 🎉
