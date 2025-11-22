import { ReactNode } from "react";
import { Filter } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ExplorerSidebarItem {
  key: string;
  label: string;
  count?: number;
  icon?: ReactNode;
  onClick?: () => void;
  active?: boolean;
}

export interface ExplorerSidebarSection {
  title: string;
  items: ExplorerSidebarItem[];
}

interface ExplorerSidebarProps {
  sections: ExplorerSidebarSection[];
}

export const ExplorerSidebar = ({ sections }: ExplorerSidebarProps) => {
  return (
    <aside className="hidden w-72 flex-shrink-0 border-r border-border/60 bg-muted/40 p-5 lg:block">
      <div className="mb-6 flex items-center gap-3 rounded-2xl border border-border/60 bg-background/70 px-3 py-2">
        <div className="rounded-xl bg-primary/10 p-2 text-primary">
          <Filter className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-foreground">Filtri</p>
          <p className="text-[0.7rem] text-muted-foreground">Seleziona rapidamente la vista</p>
        </div>
      </div>
      <div className="space-y-6">
        {sections.map((section) => (
          <div key={section.title} className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-foreground">
              {section.title}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={cn(
                    "flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-left transition",
                    item.active
                      ? "bg-background shadow-sm text-foreground"
                      : "text-muted-foreground hover:bg-background/80 hover:text-foreground",
                  )}
                  onClick={item.onClick}
                >
                  <span className="flex items-center gap-2">
                    {item.icon}
                    {item.label}
                  </span>
                  {typeof item.count === "number" ? (
                    <span className="text-xs font-medium text-muted-foreground">
                      {item.count}
                    </span>
                  ) : null}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};
