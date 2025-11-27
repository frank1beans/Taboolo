import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "glow" | "neon";
  gradient?: "blue" | "purple" | "green" | "red" | "multi";
  hover?: boolean;
}

const gradientColors = {
  blue: "from-blue-500/20 via-blue-600/10 to-transparent",
  purple: "from-purple-500/20 via-purple-600/10 to-transparent",
  green: "from-emerald-500/20 via-emerald-600/10 to-transparent",
  red: "from-red-500/20 via-red-600/10 to-transparent",
  multi: "from-blue-500/20 via-purple-500/20 to-pink-500/20",
};

const glowColors = {
  blue: "shadow-blue-500/20",
  purple: "shadow-purple-500/20",
  green: "shadow-emerald-500/20",
  red: "shadow-red-500/20",
  multi: "shadow-purple-500/30",
};

export function GlassCard({
  children,
  className,
  variant = "default",
  gradient = "multi",
  hover = true,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl",
        "backdrop-blur-xl bg-gradient-to-br",
        "border border-white/10",
        "transition-all duration-500",
        hover && "hover:border-white/20 hover:shadow-2xl",
        variant === "glow" && `shadow-xl ${glowColors[gradient]}`,
        variant === "neon" && "shadow-2xl shadow-purple-500/40 border-purple-400/30",
        className
      )}
    >
      {/* Animated gradient background */}
      <div
        className={cn(
          "absolute inset-0 bg-gradient-to-br opacity-50 -z-10",
          gradientColors[gradient],
          "animate-gradient-shift"
        )}
      />

      {/* Glass effect overlay */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-md -z-10" />

      {/* Top shine effect */}
      {variant !== "default" && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
      )}

      {/* Content */}
      <div className="relative">{children}</div>

      {/* Glow effect for neon variant */}
      {variant === "neon" && (
        <>
          <div className="absolute -top-20 -left-20 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </>
      )}
    </div>
  );
}

interface GlassStatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  gradient?: "blue" | "purple" | "green" | "red" | "multi";
}

export function GlassStatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  gradient = "blue",
}: GlassStatCardProps) {
  return (
    <GlassCard variant="glow" gradient={gradient} className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-300 mb-1">{title}</p>
          <h3 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            {value}
          </h3>
        </div>
        {icon && (
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            {icon}
          </div>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-slate-400 mb-2">{subtitle}</p>
      )}

      {trend && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/10">
          <div
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold",
              trend.isPositive
                ? "bg-emerald-500/20 text-emerald-400"
                : "bg-red-500/20 text-red-400"
            )}
          >
            <span>{trend.isPositive ? "+" : ""}{trend.value}%</span>
          </div>
          <span className="text-xs text-slate-400">vs progetto</span>
        </div>
      )}
    </GlassCard>
  );
}
