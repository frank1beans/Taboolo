import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "./button";
import { Card, CardContent, CardHeader, CardTitle } from "./card";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export function ErrorState({
  title = "Si è verificato un errore",
  message = "Non siamo riusciti a caricare i dati richiesti. Riprova tra qualche istante.",
  onRetry,
  showRetry = true
}: ErrorStateProps) {
  return (
    <Card className="border-destructive/20 bg-destructive-light/30" role="alert" aria-live="assertive">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-destructive/10 p-2">
            <AlertTriangle className="h-6 w-6 text-destructive" aria-hidden="true" />
          </div>
          <CardTitle className="text-xl text-destructive">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-base text-muted-foreground leading-relaxed">{message}</p>
        {showRetry && onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            className="gap-2"
            aria-label="Riprova a caricare i dati"
          >
            <RefreshCcw className="h-4 w-4" aria-hidden="true" />
            Riprova
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
