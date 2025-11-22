import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { LoadingState } from "./loading-state";
import { ErrorState } from "./error-state";
import { EmptyState } from "./empty-state";

interface DataStateHandlerProps<T> {
  // Dati e stati
  data: T[] | null | undefined;
  isLoading: boolean;
  isError: boolean;

  // Configurazione empty state
  emptyIcon: LucideIcon;
  emptyTitle: string;
  emptyDescription: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;

  // Configurazione loading
  loadingMessage?: string;

  // Configurazione error
  errorTitle?: string;
  errorMessage?: string;
  onRetry?: () => void;

  // Render dei dati
  children: (data: T[]) => ReactNode;
}

/**
 * Componente che gestisce automaticamente tutti gli stati (loading, error, empty, success)
 *
 * @example
 * ```tsx
 * <DataStateHandler
 *   data={commesse}
 *   isLoading={isLoading}
 *   isError={isError}
 *   emptyIcon={FolderOpen}
 *   emptyTitle="Nessuna commessa"
 *   emptyDescription="Crea la tua prima commessa"
 *   emptyActionLabel="Crea Commessa"
 *   onEmptyAction={() => navigate('/new')}
 *   loadingMessage="Caricamento commesse..."
 *   onRetry={refetch}
 * >
 *   {(data) => data.map(item => <Card key={item.id} {...item} />)}
 * </DataStateHandler>
 * ```
 */
export function DataStateHandler<T>({
  data,
  isLoading,
  isError,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  emptyActionLabel,
  onEmptyAction,
  loadingMessage = "Caricamento in corso...",
  errorTitle = "Errore nel caricamento",
  errorMessage = "Non siamo riusciti a caricare i dati. Riprova tra qualche istante.",
  onRetry,
  children,
}: DataStateHandlerProps<T>) {
  // Loading
  if (isLoading) {
    return <LoadingState message={loadingMessage} fullScreen />;
  }

  // Error
  if (isError) {
    return (
      <ErrorState
        title={errorTitle}
        message={errorMessage}
        onRetry={onRetry}
      />
    );
  }

  // Empty
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyTitle}
        description={emptyDescription}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
      />
    );
  }

  // Success - render children with data
  return <>{children(data)}</>;
}
