import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { ApiCommessaDetail } from "@/types/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type CommessaPageHeaderProps = {
  commessa?: ApiCommessaDetail;
  title: string;
  description?: string;
  backHref?: string;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  variant?: "default" | "compact";
  className?: string;
};

export function CommessaPageHeader({
  commessa,
  title,
  description,
  backHref,
  actions,
  children,
  variant = "default",
  className,
}: CommessaPageHeaderProps) {
  const containerClasses = cn(
    "workspace-panel workspace-panel--flush",
    "flex flex-col gap-3",
    variant === "compact" && "px-4 py-4",
    className,
  );

  const titleClasses =
    variant === "compact"
      ? "text-base font-semibold text-foreground"
      : "text-xl font-semibold tracking-tight text-foreground";

  const descriptionClasses =
    variant === "compact"
      ? "text-sm text-muted-foreground"
      : "text-base text-muted-foreground";

  return (
    <div className={containerClasses}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          {backHref && (
            <Button
              asChild
              variant="ghost"
              size="icon"
              className="h-9 w-9 shrink-0 rounded-lg"
            >
              <Link to={backHref}>
                <ArrowLeft className="h-4 w-4" />
                <span className="sr-only">Torna indietro</span>
              </Link>
            </Button>
          )}
          <div className="min-w-0 space-y-1">
            <h1 className={titleClasses}>{title}</h1>
            {description && (
              <p className={descriptionClasses}>{description}</p>
            )}
            {commessa?.codice && variant === "default" && (
              <p className="text-sm text-muted-foreground">
                Commessa {commessa.codice}
              </p>
            )}
          </div>
        </div>

        {actions ? <div className="workspace-header-actions">{actions}</div> : null}
      </div>

      {children && (
        <div className="border-t border-border/60 pt-3">{children}</div>
      )}
    </div>
  );
}
