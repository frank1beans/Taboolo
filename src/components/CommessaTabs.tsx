import { useEffect, useRef, useState } from "react";
import { NavLink, useParams } from "react-router-dom";
import { ApiCommessaDetail } from "@/types/api";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CommessaTabsProps {
  commessa?: ApiCommessaDetail;
  isLoading?: boolean;
}

const tabs = [
  { to: "overview", label: "Computo & riepilogo" },
  { to: "import", label: "Import" },
  { to: "price-catalog", label: "Elenco prezzi" },
  { to: "preventivo", label: "Preventivo" },
  { to: "analisi", label: "Analisi & confronti" },
  { to: "ritorni-batch", label: "Ritorni batch" },
  { to: "settings", label: "Impostazioni" },
];

export function CommessaTabs({ commessa, isLoading }: CommessaTabsProps) {
  const { id } = useParams();
  const basePath = `/commesse/${id}`;
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [isPinned, setIsPinned] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    if (!sentinelRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => setIsPinned(!entry.isIntersecting),
      { rootMargin: "-72px 0px 0px 0px" },
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div ref={sentinelRef} aria-hidden="true" className="h-px w-full" />
      <div
        className={cn(
          "sticky top-[2.75rem] z-20 rounded-xl border border-border/70 bg-card/95 px-4",
          "transition-all duration-200",
          isPinned ? "shadow-md" : "shadow-sm",
          isCollapsed ? "py-1.5" : "py-2.5 space-y-2",
        )}
      >
        {/* Header con toggle */}
        <div className="flex items-center justify-between gap-2">
          {isCollapsed ? (
            // Vista compatta: solo nome e tabs inline
            <div className="flex items-center gap-3 overflow-hidden">
              <span className="text-sm font-semibold truncate max-w-[200px]">
                {commessa?.nome ?? "-"}
              </span>
              <div className="flex flex-wrap gap-1">
                {tabs.map((tab) => (
                  <NavLink
                    key={tab.to}
                    to={`${basePath}/${tab.to}`}
                    className={({ isActive }) =>
                      cn(
                        "h-7 rounded-md border px-2 text-[10px] font-semibold uppercase tracking-wide transition-colors",
                        "flex items-center justify-center text-center whitespace-nowrap",
                        isActive
                          ? "border-primary bg-primary text-primary-foreground shadow-sm"
                          : "border-border bg-muted/70 text-muted-foreground hover:text-foreground",
                      )
                    }
                    end={tab.to === "overview"}
                  >
                    {tab.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ) : (
            // Vista espansa: header completo
            <div className="flex flex-1 flex-col gap-1.5 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-0">
                <p className="text-[9px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                  Commessa
                </p>
                {isLoading ? (
                  <Skeleton className="mt-0.5 h-5 w-48" />
                ) : (
                  <div>
                    <h1 className="text-base font-semibold tracking-tight text-foreground">
                      {commessa?.nome ?? "-"}
                    </h1>
                    {commessa?.codice && (
                      <p className="text-[10px] text-muted-foreground">{commessa.codice}</p>
                    )}
                  </div>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-muted-foreground">
                {commessa?.business_unit ? (
                  <span className="rounded-lg border border-border/70 px-2 py-0.5">
                    BU: {commessa.business_unit}
                  </span>
                ) : null}
                {commessa?.revisione ? (
                  <span className="rounded-lg border border-border/70 px-2 py-0.5">
                    Revisione {commessa.revisione}
                  </span>
                ) : null}
              </div>
            </div>
          )}

          {/* Toggle button */}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 flex-shrink-0"
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Espandi header" : "Comprimi header"}
          >
            {isCollapsed ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Tabs (solo in vista espansa) */}
        {!isCollapsed && (
          <div className="flex flex-wrap gap-1">
            {tabs.map((tab) => (
              <NavLink
                key={tab.to}
                to={`${basePath}/${tab.to}`}
                className={({ isActive }) =>
                  cn(
                    "h-9 min-w-[110px] rounded-lg border px-3 text-xs font-semibold uppercase tracking-wide transition-colors",
                    "flex items-center justify-center text-center",
                    isActive
                      ? "border-primary bg-primary text-primary-foreground shadow-sm"
                      : "border-border bg-muted/70 text-muted-foreground hover:text-foreground",
                  )
                }
                end={tab.to === "overview"}
              >
                {tab.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
