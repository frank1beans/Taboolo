/**
 * Layout patterns riutilizzabili
 * Da usare insieme a PageShell per strutturare il contenuto
 */

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

// ============= SPLIT LAYOUT =============

interface SplitLayoutProps {
  children: ReactNode;
  sidebar: ReactNode;
  sidebarPosition?: "left" | "right";
  sidebarWidth?: "sm" | "md" | "lg";
  className?: string;
}

const sidebarWidths = {
  sm: "minmax(280px,1fr)",
  md: "minmax(320px,1fr)",
  lg: "minmax(360px,1fr)",
};

export function SplitLayout({
  children,
  sidebar,
  sidebarPosition = "right",
  sidebarWidth = "md",
  className,
}: SplitLayoutProps) {
  const gridTemplate =
    sidebarPosition === "right"
      ? `minmax(0,2fr) ${sidebarWidths[sidebarWidth]}`
      : `${sidebarWidths[sidebarWidth]} minmax(0,2fr)`;

  return (
    <div
      className={cn("grid gap-5 xl:grid-cols-[var(--grid-template)]", className)}
      style={{ "--grid-template": gridTemplate } as React.CSSProperties}
    >
      {sidebarPosition === "left" && <aside className="space-y-4">{sidebar}</aside>}
      <main className="space-y-4">{children}</main>
      {sidebarPosition === "right" && <aside className="space-y-4">{sidebar}</aside>}
    </div>
  );
}

// ============= DATA SECTION =============

interface DataSectionProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function DataSection({
  title,
  description,
  actions,
  children,
  className,
}: DataSectionProps) {
  return (
    <section className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </section>
  );
}

// ============= PANEL =============

interface PanelProps {
  children: ReactNode;
  variant?: "default" | "flush" | "highlight";
  className?: string;
}

export function Panel({ children, variant = "default", className }: PanelProps) {
  return (
    <div
      className={cn(
        "workspace-panel",
        variant === "flush" && "workspace-panel--flush",
        variant === "highlight" && "border-primary/25 bg-primary/5",
        className
      )}
    >
      {children}
    </div>
  );
}

// ============= CARD GRID =============

interface CardGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4;
  gap?: "sm" | "md" | "lg";
  className?: string;
}

const columnClasses = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
};

const gapClasses = {
  sm: "gap-3",
  md: "gap-4",
  lg: "gap-6",
};

export function CardGrid({
  children,
  columns = 3,
  gap = "md",
  className,
}: CardGridProps) {
  return (
    <div className={cn("grid", columnClasses[columns], gapClasses[gap], className)}>
      {children}
    </div>
  );
}

// ============= STACK =============

interface StackProps {
  children: ReactNode;
  gap?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

const stackGaps = {
  xs: "space-y-2",
  sm: "space-y-3",
  md: "space-y-4",
  lg: "space-y-6",
};

export function Stack({ children, gap = "md", className }: StackProps) {
  return <div className={cn(stackGaps[gap], className)}>{children}</div>;
}

// ============= TOOLBAR =============

interface ToolbarProps {
  children: ReactNode;
  className?: string;
}

export function Toolbar({ children, className }: ToolbarProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between",
        className
      )}
    >
      {children}
    </div>
  );
}

interface ToolbarGroupProps {
  children: ReactNode;
  className?: string;
}

export function ToolbarGroup({ children, className }: ToolbarGroupProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {children}
    </div>
  );
}
