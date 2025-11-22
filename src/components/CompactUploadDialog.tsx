import { useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { UploadArea } from "@/components/UploadArea";

interface CompactUploadDialogProps {
  onFileUpload: (file: File) => Promise<void>;
  disabled?: boolean;
  title?: string;
  description?: string;
  submitLabel?: string;
}

export function CompactUploadDialog({
  onFileUpload,
  disabled = false,
  title = "Carica computo metrico",
  description = "Importa il file Excel del computo metrico estimativo del progetto.",
  submitLabel,
}: CompactUploadDialogProps) {
  const [open, setOpen] = useState(false);

  const handleUpload = async (file: File) => {
    await onFileUpload(file);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled}>
          <Upload className="mr-2 h-4 w-4" />
          {title}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[620px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <UploadArea
          onFileUpload={handleUpload}
          disabled={disabled}
          submitLabel={submitLabel}
        />
      </DialogContent>
    </Dialog>
  );
}
