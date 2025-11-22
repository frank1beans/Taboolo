import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

export function LoadingState({
  message = "Caricamento in corso...",
  fullScreen = false,
  className
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4",
        fullScreen ? "flex-1 min-h-[400px]" : "py-12",
        className
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-10 w-10 animate-spin text-primary" aria-hidden="true" />
      <p className="text-base text-muted-foreground font-medium">{message}</p>
      <span className="sr-only">{message}</span>
    </div>
  );
}
