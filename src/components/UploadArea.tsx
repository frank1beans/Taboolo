import { useCallback, useMemo, useState, useId } from "react";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface UploadAreaProps {
  onFileUpload: (file: File) => void | Promise<void>;
  disabled?: boolean;
  submitLabel?: string;
  acceptExtensions?: string[];
  maxSizeMB?: number;
  emptyStateTitle?: string;
  emptyStateDescription?: string;
  hint?: string;
  successMessage?: string | null;
  onFileSelected?: (file: File | null) => void;
}

const DEFAULT_EXTENSIONS = [".xlsx", ".xls"];
const DEFAULT_MAX_SIZE_MB = 100;

export function UploadArea({
  onFileUpload,
  disabled = false,
  submitLabel = "Carica computo metrico",
  acceptExtensions = DEFAULT_EXTENSIONS,
  maxSizeMB = DEFAULT_MAX_SIZE_MB,
  emptyStateTitle = "Trascina qui il file",
  emptyStateDescription = "oppure clicca per selezionarlo",
  hint,
  successMessage = "File pronto per l'import",
  onFileSelected,
}: UploadAreaProps) {
  const uploadId = useId();
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (disabled) return;

      if (event.type === "dragenter" || event.type === "dragover") {
        setIsDragging(true);
      } else if (event.type === "dragleave") {
        setIsDragging(false);
      }
    },
    [disabled],
  );

  const normalizedExtensions = useMemo(
    () => acceptExtensions.map((ext) => ext.toLowerCase()),
    [acceptExtensions],
  );

  const validateFile = useCallback(
    (file: File): boolean => {
      const fileExtension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;

      if (
        normalizedExtensions.length > 0 &&
        !normalizedExtensions.includes(fileExtension)
      ) {
        toast.error("Formato file non valido", {
          description: `Formati supportati: ${normalizedExtensions.join(", ")}`,
        });
        return false;
      }

      const maxSizeBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        toast.error("File troppo grande", {
          description: `La dimensione massima consentita è ${maxSizeMB}MB`,
        });
        return false;
      }

      return true;
    },
    [normalizedExtensions, maxSizeMB],
  );

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (disabled) return;
      setIsDragging(false);

      const files = Array.from(event.dataTransfer.files);
      if (files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
          setSelectedFile(file);
          onFileSelected?.(file);
        }
      }
    },
    [disabled, validateFile, onFileSelected],
  );

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelected?.(file);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      await onFileUpload(selectedFile);
      if (successMessage) {
        toast.success(successMessage, {
          description: `${selectedFile.name} - ${(selectedFile.size / 1024).toFixed(1)} KB`,
        });
      }
      setSelectedFile(null);
      onFileSelected?.(null);
    } catch {
      // Il toast d'errore viene gestito dal chiamante; lasciamo il file selezionato per eventuali retry.
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    onFileSelected?.(null);
  };

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "relative rounded-lg border-2 border-dashed transition-all duration-200",
          disabled && "opacity-60 pointer-events-none",
          isDragging
            ? "border-accent bg-accent/5 scale-105"
            : "border-border hover:border-accent/50 hover:bg-muted/30",
          selectedFile && "border-accent bg-accent/5",
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center py-12 px-6">
          {!selectedFile ? (
            <>
              <div className="mb-4 rounded-full bg-accent/10 p-4">
                <Upload className="h-8 w-8 text-accent" />
              </div>
              <p className="mb-2 text-base font-medium">{emptyStateTitle}</p>
              <p className="mb-4 text-sm text-muted-foreground">
                {emptyStateDescription}
              </p>
              <label htmlFor={uploadId}>
                <Button variant="outline" asChild disabled={disabled}>
                  <span className="cursor-pointer">Seleziona File</span>
                </Button>
                <input
                  id={uploadId}
                  type="file"
                  className="hidden"
                  accept={acceptExtensions.join(",")}
                  onChange={handleFileInput}
                />
              </label>
              <p className="mt-4 text-xs text-muted-foreground">
                {hint
                  ? hint
                  : `Formati supportati: ${acceptExtensions.join(", ")} (max ${maxSizeMB}MB)`}
              </p>
            </>
          ) : (
            <div className="flex w-full items-center justify-between rounded-md border bg-background p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-accent/10 p-2">
                  <FileSpreadsheet className="h-5 w-5 text-accent" />
                </div>
                <div className="flex flex-col">
                  <p className="text-sm font-medium">{selectedFile.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRemove}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {selectedFile && (
        <Button
          onClick={handleUpload}
          className="w-full gap-2 animate-fade-in"
          disabled={disabled}
        >
          <Upload className="h-4 w-4" />
          {submitLabel}
        </Button>
      )}
    </div>
  );
}
