# 🧩 Esempi d'Uso dei Componenti

## Guida pratica per usare i nuovi componenti UX

---

## 1. Loading States

### Scenario: Caricamento Dashboard

```tsx
import { LoadingState } from "@/components/ui/loading-state";

function Dashboard() {
  const { data, isLoading } = useDashboardStats();

  if (isLoading) {
    return <LoadingState message="Caricamento statistiche..." fullScreen />;
  }

  return <div>{/* Contenuto dashboard */}</div>;
}
```

### Scenario: Caricamento in sezione specifica

```tsx
import { CardSkeleton, StatCardSkeleton } from "@/components/ui/card-skeleton";

function CommesseList() {
  const { data, isLoading } = useCommesse();

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {isLoading ? (
        <>
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </>
      ) : (
        data.map(commessa => <CommessaCard key={commessa.id} {...commessa} />)
      )}
    </div>
  );
}
```

---

## 2. Empty States

### Scenario: Lista commesse vuota

```tsx
import { EmptyState } from "@/components/ui/empty-state";
import { FolderOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";

function CommesseList() {
  const { data } = useCommesse();
  const navigate = useNavigate();

  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={FolderOpen}
        title="Nessuna commessa trovata"
        description="Inizia creando la tua prima commessa per gestire computi metrici e preventivi in modo efficiente."
        actionLabel="Crea Prima Commessa"
        onAction={() => navigate("/commesse/new")}
      />
    );
  }

  return <div>{/* Lista commesse */}</div>;
}
```

### Scenario: Ricerca senza risultati

```tsx
import { Search } from "lucide-react";

function SearchResults({ query, results }) {
  if (results.length === 0) {
    return (
      <EmptyState
        icon={Search}
        title={`Nessun risultato per "${query}"`}
        description="Prova con termini diversi o controlla l'ortografia."
        // Nessuna azione in questo caso
      />
    );
  }

  return <div>{/* Risultati */}</div>;
}
```

---

## 3. Error States

### Scenario: Errore nel caricamento dati

```tsx
import { ErrorState } from "@/components/ui/error-state";

function CommessaDetail({ id }) {
  const { data, isError, refetch } = useCommessa(id);

  if (isError) {
    return (
      <ErrorState
        title="Errore nel caricamento della commessa"
        message="Non siamo riusciti a caricare i dettagli della commessa. Controlla la connessione internet e riprova."
        onRetry={refetch}
      />
    );
  }

  return <div>{/* Dettagli commessa */}</div>;
}
```

### Scenario: Errore critico

```tsx
<ErrorState
  title="Errore critico"
  message="Si è verificato un errore imprevisto. Contatta l'assistenza se il problema persiste."
  showRetry={false}
/>
```

---

## 4. Confirmation Dialogs

### Scenario: Eliminazione commessa

```tsx
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { useState } from "react";
import { toast } from "sonner";

function CommessaActions({ commessa }) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const deleteMutation = useDeleteCommessa();

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(commessa.id);
      toast.success("Commessa eliminata con successo");
      setShowDeleteDialog(false);
    } catch (error) {
      toast.error("Impossibile eliminare la commessa");
    }
  };

  return (
    <>
      <Button
        variant="destructive"
        onClick={() => setShowDeleteDialog(true)}
      >
        Elimina Commessa
      </Button>

      <ConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Eliminare la commessa?"
        description={`Stai per eliminare "${commessa.nome}". Questa azione non può essere annullata. Tutti i dati associati verranno eliminati permanentemente.`}
        confirmLabel="Elimina Definitivamente"
        cancelLabel="Annulla"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </>
  );
}
```

### Scenario: Sovrascrittura dati

```tsx
function ImportDialog() {
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <ConfirmationDialog
      open={showConfirm}
      onOpenChange={setShowConfirm}
      title="Sovrascrivere i dati esistenti?"
      description="L'importazione sovrascriverà i dati correnti. È consigliabile creare un backup prima di procedere."
      confirmLabel="Procedi con l'importazione"
      cancelLabel="Annulla"
      variant="default"
      onConfirm={handleImport}
    />
  );
}
```

---

## 5. Status Badges

### Scenario: Stato commessa

```tsx
import { StatusBadge } from "@/components/ui/status-badge";

function CommessaCard({ commessa }) {
  const getStatus = () => {
    if (commessa.isCompleted) return { status: "success", label: "Completata" };
    if (commessa.hasErrors) return { status: "error", label: "Errori" };
    if (commessa.needsReview) return { status: "warning", label: "Da Revisionare" };
    if (commessa.isProcessing) return { status: "loading", label: "In Elaborazione" };
    return { status: "pending", label: "In Attesa" };
  };

  const { status, label } = getStatus();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{commessa.nome}</CardTitle>
          <StatusBadge status={status} label={label} />
        </div>
      </CardHeader>
    </Card>
  );
}
```

### Scenario: Stato sincronizzazione

```tsx
function SyncIndicator({ isSyncing, lastSync }) {
  if (isSyncing) {
    return <StatusBadge status="loading" label="Sincronizzazione..." />;
  }

  if (lastSync) {
    return <StatusBadge status="success" label="Sincronizzato" />;
  }

  return <StatusBadge status="warning" label="Non sincronizzato" />;
}
```

---

## 6. Info Tooltips

### Scenario: Help su campo complesso

```tsx
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

function MargineField() {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label htmlFor="margine">Margine di Sicurezza (%)</Label>
        <InfoTooltip
          content="Percentuale aggiuntiva applicata ai costi per coprire imprevisti e variazioni di prezzo. Raccomandato tra 10% e 15% per progetti standard."
          side="right"
        />
      </div>
      <Input
        id="margine"
        type="number"
        placeholder="10"
        min="0"
        max="100"
      />
    </div>
  );
}
```

### Scenario: Spiegazione funzionalità avanzata

```tsx
function WBSSettings() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Struttura WBS</CardTitle>
          <InfoTooltip
            content="La Work Breakdown Structure organizza il progetto in fasi gerarchiche. Usa questo strumento per definire macro-categorie e sotto-categorie di lavorazione."
            side="bottom"
          />
        </div>
      </CardHeader>
    </Card>
  );
}
```

---

## 7. Toast Notifications

### Scenario: Feedback azioni utente

```tsx
import { toast } from "sonner";

function SaveButton({ onSave }) {
  const handleSave = async () => {
    try {
      await onSave();
      toast.success("Modifiche salvate con successo!");
    } catch (error) {
      toast.error("Impossibile salvare le modifiche. Riprova.");
    }
  };

  return <Button onClick={handleSave}>Salva</Button>;
}
```

### Scenario: Operazioni in background

```tsx
function ImportFile({ file }) {
  const importMutation = useImportFile();

  const handleImport = async () => {
    const toastId = toast.loading("Importazione in corso...");

    try {
      const result = await importMutation.mutateAsync(file);
      toast.success(
        `File importato con successo! ${result.rows} righe elaborate.`,
        { id: toastId }
      );
    } catch (error) {
      toast.error(
        "Errore durante l'importazione. Controlla il formato del file.",
        { id: toastId }
      );
    }
  };

  return <Button onClick={handleImport}>Importa</Button>;
}
```

---

## 8. Combinazioni Comuni

### Pattern: Lista con tutti gli stati

```tsx
import { LoadingState } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import { EmptyState } from "@/components/ui/empty-state";
import { FolderOpen } from "lucide-react";

function CommesseListComplete() {
  const { data, isLoading, isError, refetch } = useCommesse();
  const navigate = useNavigate();

  // Loading
  if (isLoading) {
    return <LoadingState message="Caricamento commesse..." fullScreen />;
  }

  // Error
  if (isError) {
    return (
      <ErrorState
        title="Errore nel caricamento delle commesse"
        message="Non siamo riusciti a recuperare l'elenco delle commesse."
        onRetry={refetch}
      />
    );
  }

  // Empty
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={FolderOpen}
        title="Nessuna commessa trovata"
        description="Inizia creando la tua prima commessa."
        actionLabel="Crea Commessa"
        onAction={() => navigate("/commesse/new")}
      />
    );
  }

  // Success - mostra dati
  return (
    <div className="grid gap-4">
      {data.map(commessa => (
        <CommessaCard key={commessa.id} {...commessa} />
      ))}
    </div>
  );
}
```

### Pattern: Form con validazione e conferma

```tsx
import { useState } from "react";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { toast } from "sonner";

function CommessaForm({ initialData, onSave }) {
  const [formData, setFormData] = useState(initialData);
  const [showConfirm, setShowConfirm] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!formData.nome) newErrors.nome = "Nome richiesto";
    if (!formData.cliente) newErrors.cliente = "Cliente richiesto";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      setShowConfirm(true);
    }
  };

  const handleConfirm = async () => {
    try {
      await onSave(formData);
      toast.success("Commessa salvata con successo!");
      setShowConfirm(false);
    } catch (error) {
      toast.error("Errore durante il salvataggio");
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Label htmlFor="nome">Nome Commessa</Label>
            <InfoTooltip content="Inserisci un nome descrittivo per identificare facilmente la commessa" />
          </div>
          <Input
            id="nome"
            value={formData.nome}
            onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
            className={errors.nome ? "border-destructive" : ""}
          />
          {errors.nome && (
            <p className="text-sm text-destructive">{errors.nome}</p>
          )}
        </div>

        <Button type="submit" size="lg">
          Salva Commessa
        </Button>
      </form>

      <ConfirmationDialog
        open={showConfirm}
        onOpenChange={setShowConfirm}
        title="Salvare la commessa?"
        description="Conferma per salvare le modifiche apportate alla commessa."
        confirmLabel="Salva"
        cancelLabel="Annulla"
        onConfirm={handleConfirm}
      />
    </>
  );
}
```

---

## 9. Best Practices Riassunte

### ✅ DA FARE

```tsx
// Sempre feedback per operazioni async
const handleDelete = async () => {
  const toastId = toast.loading("Eliminazione in corso...");
  try {
    await deleteCommessa(id);
    toast.success("Eliminato!", { id: toastId });
  } catch {
    toast.error("Errore", { id: toastId });
  }
};

// Sempre conferma per azioni distruttive
<Button onClick={() => setShowConfirm(true)}>Elimina</Button>

// Sempre empty state con azione
if (data.length === 0) {
  return <EmptyState ... actionLabel="Crea" onAction={handleCreate} />;
}

// Sempre tooltip su campi complessi
<Label>
  Campo Complesso
  <InfoTooltip content="Spiegazione chiara" />
</Label>
```

### ❌ DA EVITARE

```tsx
// ❌ Nessun feedback
const handleDelete = async () => {
  await deleteCommessa(id); // Utente non sa cosa sta succedendo
};

// ❌ Eliminazione senza conferma
<Button onClick={deleteCommessa}>Elimina</Button>

// ❌ Empty state senza aiuto
if (data.length === 0) {
  return <p>Nessun dato</p>; // Utente non sa cosa fare
}

// ❌ Campo oscuro senza help
<Input placeholder="???" /> // Utente confuso
```

---

## 🎯 Checklist Rapida

Per ogni nuova feature, assicurati di avere:

- [ ] **LoadingState** durante caricamento
- [ ] **ErrorState** con retry in caso di errore
- [ ] **EmptyState** con CTA se lista vuota
- [ ] **ConfirmationDialog** per azioni distruttive
- [ ] **Toast** per confermare azioni completate
- [ ] **InfoTooltip** su campi/funzioni complesse
- [ ] **StatusBadge** per mostrare stati
- [ ] **Skeleton** invece di schermo bianco

Questo garantisce un'esperienza utente professionale e affidabile! 🚀
