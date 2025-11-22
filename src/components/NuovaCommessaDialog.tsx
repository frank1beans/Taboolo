import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Plus } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { BUSINESS_UNITS } from "@/data/businessUnits";

interface NuovaCommessaDialogProps {
  onCommessaCreated?: (commessa: CommessaData) => Promise<void> | void;
}

export interface CommessaData {
  nomeCommessa: string;
  numeroCommessa: string;
  revisione: string;
  anno: string;
  data: Date | undefined;
  businessUnit: string;
  descrizione: string;
}

export function NuovaCommessaDialog({ onCommessaCreated }: NuovaCommessaDialogProps) {
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<CommessaData>({
    nomeCommessa: "",
    numeroCommessa: "",
    revisione: "",
    anno: new Date().getFullYear().toString(),
    data: new Date(),
    businessUnit: "",
    descrizione: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validazione
    if (!formData.nomeCommessa || !formData.numeroCommessa || !formData.descrizione) {
      toast.error("Compila tutti i campi obbligatori");
      return;
    }

    try {
      setIsSubmitting(true);
      await onCommessaCreated?.(formData);

      toast.success("Commessa creata con successo", {
        description: `${formData.nomeCommessa} - ${formData.numeroCommessa}`,
      });

      setFormData({
        nomeCommessa: "",
        numeroCommessa: "",
        revisione: "",
        anno: new Date().getFullYear().toString(),
        data: new Date(),
        businessUnit: "",
        descrizione: "",
      });
      setOpen(false);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossibile creare la commessa";
      toast.error("Errore durante la creazione", {
        description: message,
      });
    } finally {
      setIsSubmitting(false);
    }

  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Nuova Commessa
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Crea Nuova Commessa</DialogTitle>
          <DialogDescription>
            Inserisci i metadati della commessa. I campi contrassegnati con * sono obbligatori.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="nomeCommessa">
                Nome Commessa <span className="text-destructive">*</span>
              </Label>
              <Input
                id="nomeCommessa"
                placeholder="es. Ristrutturazione Palazzo Comunale"
                value={formData.nomeCommessa}
                onChange={(e) =>
                  setFormData({ ...formData, nomeCommessa: e.target.value })
                }
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="numeroCommessa">
                  Numero Commessa <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="numeroCommessa"
                  placeholder="es. 001"
                  value={formData.numeroCommessa}
                  onChange={(e) =>
                    setFormData({ ...formData, numeroCommessa: e.target.value })
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
              <Label htmlFor="descrizione">
                Descrizione <span className="text-destructive">*</span>
              </Label>
              <Input
                id="descrizione"
                placeholder="Breve descrizione della commessa..."
                value={formData.descrizione}
                onChange={(e) =>
                  setFormData({ ...formData, descrizione: e.target.value })
                }
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="anno">Anno</Label>
                <Input
                  id="anno"
                  type="number"
                  placeholder="2024"
                  value={formData.anno}
                  onChange={(e) =>
                    setFormData({ ...formData, anno: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Data</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !formData.data && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {formData.data ? (
                        format(formData.data, "PPP", { locale: it })
                      ) : (
                        <span>Seleziona data</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={formData.data}
                      onSelect={(date) =>
                        setFormData({ ...formData, data: date })
                      }
                      initialFocus
                      locale={it}
                    />
                  </PopoverContent>
                </Popover>
              </div>
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
              {isSubmitting ? "Creazione in corso..." : "Crea Commessa"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
