import { LucideIcon } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-6 py-16 px-6 text-center",
        className
      )}
      role="region"
      aria-label="Contenuto vuoto"
    >
      <div className="rounded-2xl bg-muted/30 p-6 shadow-sm">
        <Icon className="h-12 w-12 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="space-y-3 max-w-md">
        <h3 className="text-xl font-semibold text-foreground">{title}</h3>
        <p className="text-base text-muted-foreground leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <Button
          onClick={onAction}
          size="lg"
          className="mt-2"
          aria-label={actionLabel}
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
