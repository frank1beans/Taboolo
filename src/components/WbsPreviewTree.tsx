import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiWbsNode, ApiAggregatedVoce } from "@/types/api";

interface WbsPreviewTreeProps {
  tree: ApiWbsNode[];
  voci: ApiAggregatedVoce[];
  importoTotale: number;
}

interface TreeNodeProps {
  node: ApiWbsNode;
  level: number;
}

const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "€0,00";
  return `€${value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

function TreeNode({ node, level }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="space-y-1">
      <div
        className={cn(
          "flex items-center justify-between px-3 py-2 rounded-md hover:bg-muted/50 transition-colors",
          level === 0 && "bg-muted font-semibold",
          level > 0 && "ml-4",
        )}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {hasChildren && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-shrink-0 p-0.5 hover:bg-muted rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}
          
          <div className="flex flex-col min-w-0 flex-1">
            <div className="flex items-baseline gap-2">
              {node.code && (
                <span className="font-mono text-xs text-muted-foreground flex-shrink-0">
                  {node.code}
                </span>
              )}
              <span className={cn(
                "truncate",
                level === 0 ? "text-sm font-semibold" : "text-sm",
              )}>
                {node.description || node.code || `Livello ${node.level}`}
              </span>
            </div>
          </div>
        </div>

        <div className="flex-shrink-0 ml-2">
          <span className={cn(
            "font-mono text-sm",
            level === 0 ? "font-bold text-primary" : "text-foreground",
          )}>
            {formatCurrency(node.importo)}
          </span>
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="space-y-1">
          {node.children.map((child, idx) => (
            <TreeNode key={`${child.level}-${child.code}-${idx}`} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function WbsPreviewTree({ tree, voci, importoTotale }: WbsPreviewTreeProps) {
  if (!tree || tree.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Nessun dato WBS disponibile
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-primary/10 border border-primary/20">
        <span className="font-semibold">Totale Preventivo</span>
        <span className="font-bold text-lg text-primary">
          {formatCurrency(importoTotale)}
        </span>
      </div>

      <div className="space-y-1">
        {tree.map((node, idx) => (
          <TreeNode key={`root-${node.level}-${node.code}-${idx}`} node={node} level={0} />
        ))}
      </div>

      <div className="mt-6 text-sm text-muted-foreground">
        <p>{voci.length} voci totali</p>
      </div>
    </div>
  );
}
