import { useState } from "react";
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileText, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { FrontendWbsNode } from "@/types/api";

interface WBSTreeProps {
  nodes: FrontendWbsNode[];
  /** Optional custom max height for the scrollable area (default 70vh) */
  maxHeight?: string;
  className?: string;
}

interface WBSTreeNodeProps {
  node: FrontendWbsNode;
  level: number;
}

const isSpazialeLevel = (level: number) => level <= 5;

function WBSTreeNode({ node, level }: WBSTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isLeaf = !hasChildren;
  const isSpaziale = isSpazialeLevel(node.level);

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-3 px-4 py-3 transition-all duration-150",
          "hover:bg-accent/10 rounded-sm",
          hasChildren && "cursor-pointer",
          level === 0 && "bg-muted/40 font-semibold border-b",
          isLeaf && "text-sm"
        )}
        style={{ paddingLeft: `${level * 1.5 + 1}rem` }}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {hasChildren ? (
          <button className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors">
            {isExpanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>
        ) : (
          <div className="w-3.5" />
        )}

        {hasChildren ? (
          isSpaziale ? (
            <MapPin
              className={cn(
                "h-4 w-4 flex-shrink-0",
                isExpanded ? "text-blue-500" : "text-blue-400"
              )}
            />
          ) : isExpanded ? (
            <FolderOpen className="h-4 w-4 text-primary flex-shrink-0" />
          ) : (
            <Folder className="h-4 w-4 text-primary flex-shrink-0" />
          )
        ) : (
          <FileText className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
        )}

        <span
          className={cn(
            "font-mono min-w-[5rem]",
            level === 0 ? "text-xs font-bold text-foreground" : "text-xs font-light text-muted-foreground",
            isSpaziale && "text-blue-600 dark:text-blue-400"
          )}
        >
          {node.code ?? ""}
        </span>

        <span
          className={cn(
            "flex-1",
            level === 0 ? "text-sm font-bold" : "text-sm font-light",
            isLeaf && "text-foreground/90"
          )}
        >
          {node.description ?? "Senza descrizione"}
        </span>

        <span
          className={cn(
            "font-medium text-right min-w-[8rem] font-mono",
            level === 0 ? "text-sm font-bold text-primary" : "text-xs font-light text-foreground"
          )}
        >
           {node.importo.toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <WBSTreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function WBSTree({ nodes, maxHeight = "70vh", className }: WBSTreeProps) {
  return (
    <div className={cn("border rounded overflow-hidden bg-card h-full flex flex-col", className)}>
      <div className="flex items-center gap-3 px-6 py-4 text-[10px] font-bold uppercase tracking-widest bg-background border-b sticky top-0 z-10">
        <div className="w-3.5" />
        <div className="w-4" />
        <span className="min-w-[5rem] text-muted-foreground/70">Codice</span>
        <span className="flex-1 text-muted-foreground/70">Descrizione</span>
        <span className="min-w-[8rem] text-right text-muted-foreground/70">Importo</span>
      </div>
      <div className="flex-1 overflow-y-auto min-h-[320px]" style={{ maxHeight }}>
        {nodes.length > 0 ? (
          nodes.map((node) => <WBSTreeNode key={node.id} node={node} level={0} />)
        ) : (
          <div className="p-12 text-center text-muted-foreground text-sm font-light">
            Nessuna voce WBS disponibile
          </div>
        )}
      </div>
    </div>
  );
}
