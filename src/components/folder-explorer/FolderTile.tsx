import { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface FolderTileAction {
  label: string;
  icon: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export interface FolderTileProps {
  id?: string;
  title: string;
  subtitle?: string;
  description?: string;
  meta?: string;
  icon?: ReactNode;
  badge?: {
    label: string;
    variant?: "default" | "success" | "warning" | "info" | "muted";
  };
  onOpen?: () => void;
  actions?: FolderTileAction[];
}

const badgeVariantMap: Record<
  NonNullable<FolderTileProps["badge"]>["variant"],
  string
> = {
  default: "bg-muted text-foreground",
  success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  info: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
  muted: "bg-muted text-muted-foreground",
};

export const FolderTile = ({
  title,
  subtitle,
  description,
  meta,
  icon,
  badge,
  actions = [],
  onOpen,
}: FolderTileProps) => {
  return (
    <div
      className="group relative flex flex-col rounded-xl border bg-background p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg"
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen?.();
        }
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex size-11 items-center justify-center rounded-lg bg-primary/5 text-primary">
          {icon}
        </div>
        {badge ? (
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide",
              badgeVariantMap[badge.variant ?? "default"],
            )}
          >
            {badge.label}
          </span>
        ) : null}
      </div>

      <div className="mt-4 space-y-1">
        <p className="text-base font-semibold leading-tight">{title}</p>
        {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>

      {description ? (
        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">{description}</p>
      ) : null}

      <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
        {meta ? <span>{meta}</span> : <span>&nbsp;</span>}
        {actions.length ? (
          <div className="flex items-center gap-2 opacity-0 transition group-hover:opacity-100">
            {actions.map((action) => (
              <button
                key={action.label}
                type="button"
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-xs font-medium text-muted-foreground hover:border-primary/40 hover:text-foreground",
                  action.disabled && "cursor-not-allowed opacity-60 hover:border-muted",
                )}
                disabled={action.disabled}
                onClick={(event) => {
                  event.stopPropagation();
                  if (!action.disabled) {
                    action.onClick?.();
                  }
                }}
              >
                {action.icon}
                {action.label}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
};
