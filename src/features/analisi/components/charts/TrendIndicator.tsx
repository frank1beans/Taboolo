import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface TrendIndicatorProps {
  value: number;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
  showValue?: boolean;
  animated?: boolean;
  variant?: "default" | "pill" | "badge";
}

export function TrendIndicator({
  value,
  size = "md",
  showIcon = true,
  showValue = true,
  animated = true,
  variant = "default",
}: TrendIndicatorProps) {
  const isPositive = value > 0;
  const isNeutral = Math.abs(value) < 0.1;

  const sizeClasses = {
    sm: "text-xs gap-1 px-2 py-1",
    md: "text-sm gap-1.5 px-3 py-1.5",
    lg: "text-base gap-2 px-4 py-2",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  const getColorClasses = () => {
    if (isNeutral) {
      return {
        bg: "bg-slate-500/20",
        text: "text-slate-300",
        border: "border-slate-400/30",
        gradient: "from-slate-400 to-slate-500",
      };
    }

    if (isPositive) {
      return {
        bg: "bg-red-500/20",
        text: "text-red-400",
        border: "border-red-400/30",
        gradient: "from-red-400 to-red-600",
      };
    }

    return {
      bg: "bg-emerald-500/20",
      text: "text-emerald-400",
      border: "border-emerald-400/30",
      gradient: "from-emerald-400 to-emerald-600",
    };
  };

  const colors = getColorClasses();

  const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;

  if (variant === "pill") {
    return (
      <div
        className={cn(
          "inline-flex items-center rounded-full font-semibold",
          "border backdrop-blur-sm",
          colors.bg,
          colors.text,
          colors.border,
          sizeClasses[size],
          animated && "transition-all duration-300 hover:scale-105"
        )}
      >
        {showIcon && <Icon className={cn(iconSizes[size], animated && "animate-pulse")} />}
        {showValue && (
          <span className="font-mono">
            {isPositive ? "+" : ""}
            {value.toFixed(1)}%
          </span>
        )}
      </div>
    );
  }

  if (variant === "badge") {
    return (
      <div
        className={cn(
          "relative inline-flex items-center justify-center rounded-lg font-bold overflow-hidden",
          "backdrop-blur-md border",
          colors.border,
          sizeClasses[size],
          animated && "transition-all duration-300 hover:shadow-lg"
        )}
      >
        {/* Gradient background */}
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-br opacity-20",
            `from-${isPositive ? "red" : "emerald"}-500/30 to-${isPositive ? "red" : "emerald"}-600/10`,
            animated && "animate-gradient-shift"
          )}
        />

        <div className="relative flex items-center gap-1.5">
          {showIcon && (
            <Icon className={cn(iconSizes[size], colors.text, animated && "animate-bounce")} />
          )}
          {showValue && (
            <span className={cn("font-mono", colors.text)}>
              {isPositive ? "+" : ""}
              {value.toFixed(1)}%
            </span>
          )}
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5",
        colors.text,
        animated && "transition-all duration-300"
      )}
    >
      {showIcon && <Icon className={cn(iconSizes[size], animated && "animate-pulse")} />}
      {showValue && (
        <span className="font-mono font-semibold">
          {isPositive ? "+" : ""}
          {value.toFixed(1)}%
        </span>
      )}
    </div>
  );
}

interface AnimatedTrendBarProps {
  progetto: number;
  media: number;
  label?: string;
  className?: string;
}

export function AnimatedTrendBar({
  progetto,
  media,
  label,
  className,
}: AnimatedTrendBarProps) {
  const delta = progetto !== 0 ? ((media - progetto) / progetto) * 100 : 0;
  const isPositive = delta > 0;

  const progettoPercent = progetto / (progetto + media) * 100;
  const mediaPercent = 100 - progettoPercent;

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-300">{label}</span>
          <TrendIndicator value={delta} size="sm" variant="pill" />
        </div>
      )}

      <div className="relative h-3 rounded-full overflow-hidden bg-slate-800/50 border border-slate-700/50">
        {/* Progetto bar */}
        <div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-slate-400 to-slate-500 transition-all duration-1000"
          style={{ width: `${progettoPercent}%` }}
        />

        {/* Media bar */}
        <div
          className={cn(
            "absolute top-0 right-0 h-full transition-all duration-1000",
            isPositive
              ? "bg-gradient-to-r from-red-500 to-red-600"
              : "bg-gradient-to-r from-emerald-500 to-emerald-600"
          )}
          style={{ width: `${mediaPercent}%` }}
        />

        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
      </div>

      <div className="flex items-center justify-between text-[10px] text-slate-400">
        <span>Progetto: €{(progetto / 1000).toFixed(0)}k</span>
        <span>Media: €{(media / 1000).toFixed(0)}k</span>
      </div>
    </div>
  );
}

interface PulsatingDotProps {
  variant: "success" | "warning" | "danger" | "info";
  size?: "sm" | "md" | "lg";
}

export function PulsatingDot({ variant, size = "md" }: PulsatingDotProps) {
  const colors = {
    success: "bg-emerald-500",
    warning: "bg-orange-500",
    danger: "bg-red-500",
    info: "bg-blue-500",
  };

  const sizes = {
    sm: "w-2 h-2",
    md: "w-3 h-3",
    lg: "w-4 h-4",
  };

  return (
    <div className="relative inline-flex">
      <div className={cn("rounded-full", colors[variant], sizes[size])} />
      <div
        className={cn(
          "absolute inset-0 rounded-full animate-ping opacity-75",
          colors[variant],
          sizes[size]
        )}
      />
    </div>
  );
}
