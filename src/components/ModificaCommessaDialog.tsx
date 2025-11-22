import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Edit2 } from "lucide-react";
import { toast } from "sonner";
import { ApiCommessaDetail, CommessaStato } from "@/types/api";
import { BUSINESS_UNITS } from "@/data/businessUnits";

interface ModificaCommessaDialogProps {
  commessa: ApiCommessaDetail;
  onUpdate: (payload: {
    nome: string;
    codice: string;
    descrizione?: string | null;
    business_unit?: string | null;
    revisione?: string | null;
    note?: string | null;
    stato?: CommessaStato;
  }) => Promise<void>;
}

const COMMESSA_STATI: CommessaStato[] = ["setup", "in_corso", "chiusa"];

export function ModificaCommessaDialog({ commessa, onUpdate }: ModificaCommessaDialogProps) {
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    nome: "",
    codice: "",
    descrizione: "",
    businessUnit: "",
    revisione: "",
    stato: "setup" as CommessaStato,
  });

  useEffect(() => {
    if (open) {
      setFormData({
        nome: commessa.nome || "",
        codice: commessa.codice || "",
        descrizione: commessa.descrizione || "",
        businessUnit: commessa.business_unit || "",
        revisione: commessa.revisione || "",
        stato: commessa.stato,
      });
    }
  }, [open, commessa]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.nome || !formData.codice) {
      toast.error("Compila tutti i campi obbligatori");
      return;
    }

    try {
      setIsSubmitting(true);
      await onUpdate({
        nome: formData.nome,
        codice: formData.codice,
        descrizione: formData.descrizione,
        business_unit: formData.businessUnit || null,
        revisione: formData.revisione || null,
        note: commessa.note,
        stato: formData.stato,
      });

      toast.success("Commessa aggiornata", {
        description: `${formData.nome} - ${formData.codice}`,
      });
      setOpen(false);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossibile aggiornare la commessa";
      toast.error("Errore durante l'aggiornamento", {
        description: message,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button variant="outline" size="sm" className="gap-2" onClick={() => setOpen(true)}>
        <Edit2 className="h-4 w-4" />
        Modifica metadati
      </Button>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Modifica metadati commessa</DialogTitle>
          <DialogDescription>
            Aggiorna le informazioni della commessa. I campi contrassegnati con * sono obbligatori.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="nome">
                Nome Commessa <span className="text-destructive">*</span>
              </Label>
              <Input
                id="nome"
                placeholder="es. Ristrutturazione Palazzo Comunale"
                value={formData.nome}
                onChange={(e) =>
                  setFormData({ ...formData, nome: e.target.value })
                }
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="codice">
                  Numero Commessa <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="codice"
                  placeholder="es. 001"
                  value={formData.codice}
                  onChange={(e) =>
                    setFormData({ ...formData, codice: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="businessUnit">Business Unit</Label>
                <Select
                  value={formData.businessUnit}
                  onValueChange={(value) =>
                    setFormData({ ...formData, businessUnit: value })
                  }
                >
                  <SelectTrigger id="businessUnit">
                    <SelectValue placeholder="Seleziona business unit" />
                  </SelectTrigger>
                  <SelectContent>
                    {BUSINESS_UNITS.map((unit) => (
                      <SelectItem key={unit} value={unit}>
                        {unit}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stato">Stato</Label>
              <Select
                value={formData.stato}
                onValueChange={(value) =>
                  setFormData({ ...formData, stato: value as CommessaStato })
                }
              >
                <SelectTrigger id="stato">
                  <SelectValue placeholder="Seleziona stato" />
                </SelectTrigger>
                <SelectContent>
                  {COMMESSA_STATI.map((state) => (
                    <SelectItem key={state} value={state}>
                      {state}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="descrizione">
                Descrizione
              </Label>
              <Input
                id="descrizione"
                placeholder="Breve descrizione della commessa..."
                value={formData.descrizione}
                onChange={(e) =>
                  setFormData({ ...formData, descrizione: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="revisione">Revisione</Label>
              <Input
                id="revisione"
                placeholder="es. Rev. A"
                value={formData.revisione}
                onChange={(e) =>
                  setFormData({ ...formData, revisione: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvataggio in corso..." : "Salva modifiche"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
