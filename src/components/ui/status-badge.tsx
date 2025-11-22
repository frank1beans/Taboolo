import { CheckCircle2, XCircle, AlertCircle, Clock, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { STATUS_CONFIG, BADGE_VARIANT_STYLES, type BadgeVariant } from "@/lib/constants";
import type { CommessaStato } from "@/types/api";

type StatusType = "success" | "error" | "warning" | "pending" | "loading";

interface StatusBadgeProps {
  status: StatusType;
  label: string;
  className?: string;
}

const statusConfig = {
  success: {
    icon: CheckCircle2,
    className: "bg-success-light text-success border-success/20",
    ariaLabel: "Completato con successo"
  },
  error: {
    icon: XCircle,
    className: "bg-destructive-light text-destructive border-destructive/20",
    ariaLabel: "Errore"
  },
  warning: {
    icon: AlertCircle,
    className: "bg-warning-light text-warning border-warning/20",
    ariaLabel: "Attenzione"
  },
  pending: {
    icon: Clock,
    className: "bg-muted text-muted-foreground border-border",
    ariaLabel: "In attesa"
  },
  loading: {
    icon: Loader2,
    className: "bg-primary-light text-primary border-primary/20",
    ariaLabel: "Caricamento"
  }
};

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium",
        config.className,
        className
      )}
      role="status"
      aria-label={`${config.ariaLabel}: ${label}`}
    >
      <Icon
        className={cn("h-4 w-4", status === "loading" && "animate-spin")}
        aria-hidden="true"
      />
      <span>{label}</span>
    </Badge>
  );
}

// ============= COMMESSA STATUS BADGE =============

interface CommessaStatusBadgeProps {
  status: CommessaStato;
  size?: "xs" | "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

const sizeStyles = {
  xs: "text-[9px] h-4 px-1.5",
  sm: "text-[10px] h-5 px-2",
  md: "text-xs h-6 px-2.5",
};

export function CommessaStatusBadge({
  status,
  size = "sm",
  showIcon = false,
  className,
}: CommessaStatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-medium uppercase tracking-wide",
        config.className,
        sizeStyles[size],
        className
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {config.label}
    </span>
  );
}

// ============= GENERIC BADGE =============

interface GenericBadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: "xs" | "sm" | "md";
  className?: string;
}

export function GenericBadge({
  label,
  variant = "muted",
  size = "sm",
  className,
}: GenericBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-semibold uppercase tracking-wide",
        BADGE_VARIANT_STYLES[variant],
        sizeStyles[size],
        className
      )}
    >
      {label}
    </span>
  );
}
