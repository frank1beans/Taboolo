import { useState } from "react";
import { ChevronDown, ChevronRight, Eye, Trash2, Upload, FolderOpen, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface ComputoTreeItem {
  id: number;
  nome: string;
  tipo: "progetto" | "ritorno";
  impresa?: string;
  round_number?: number;
  importo_totale: number | null;
  created_at: string;
  coerenza_status?: "ok" | "warning";
}

interface ComputoTreeViewProps {
  computi: ComputoTreeItem[];
  onSelectComputo: (computoId: number) => void;
  onDeleteComputo: (computoId: number, name: string) => void;
  selectedComputoId: number | null;
  isDeleting: boolean;
}

interface TreeNode {
  type: "progetto" | "round";
  label: string;
  roundNumber?: number;
  computi: ComputoTreeItem[];
}

const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  return `€${value.toLocaleString("it-IT", { minimumFractionDigits: 2 })}`;
};

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getRoundColor = (roundNumber?: number): string => {
  if (!roundNumber) return "bg-blue-100/70 dark:bg-blue-950/50 border-blue-300 dark:border-blue-800 text-blue-800 dark:text-blue-200";
  const colors = [
    "bg-orange-100/70 dark:bg-orange-950/50 border-orange-300 dark:border-orange-800 text-orange-800 dark:text-orange-200",
    "bg-green-100/70 dark:bg-green-950/50 border-green-300 dark:border-green-800 text-green-800 dark:text-green-200",
    "bg-purple-100/70 dark:bg-purple-950/50 border-purple-300 dark:border-purple-800 text-purple-800 dark:text-purple-200",
    "bg-pink-100/70 dark:bg-pink-950/50 border-pink-300 dark:border-pink-800 text-pink-800 dark:text-pink-200",
  ];
  return colors[(roundNumber - 1) % colors.length];
};

const getRoundBadgeColor = (roundNumber?: number): string => {
  if (!roundNumber) return "bg-blue-200/50 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 border-blue-400 dark:border-blue-700";
  const colors = [
    "bg-orange-200/50 dark:bg-orange-900/50 text-orange-800 dark:text-orange-200 border-orange-400 dark:border-orange-700",
    "bg-green-200/50 dark:bg-green-900/50 text-green-800 dark:text-green-200 border-green-400 dark:border-green-700",
    "bg-purple-200/50 dark:bg-purple-900/50 text-purple-800 dark:text-purple-200 border-purple-400 dark:border-purple-700",
    "bg-pink-200/50 dark:bg-pink-900/50 text-pink-800 dark:text-pink-200 border-pink-400 dark:border-pink-700",
  ];
  return colors[(roundNumber - 1) % colors.length];
};

export function ComputoTreeView({
  computi,
  onSelectComputo,
  onDeleteComputo,
  selectedComputoId,
  isDeleting,
}: ComputoTreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(["progetto"]));

  // Organizza computi in tree structure
  const treeNodes: TreeNode[] = [];

  // Aggiungi progetto
  const progettoComputi = computi.filter((c) => c.tipo === "progetto");
  if (progettoComputi.length > 0) {
    treeNodes.push({
      type: "progetto",
      label: "Computo di progetto",
      computi: progettoComputi,
    });
  }

  // Aggiungi rounds
  const ritorni = computi.filter((c) => c.tipo === "ritorno");
  const roundsMap = new Map<number, ComputoTreeItem[]>();
  
  ritorni.forEach((computo) => {
    const roundNum = computo.round_number ?? 1;
    if (!roundsMap.has(roundNum)) {
      roundsMap.set(roundNum, []);
    }
    roundsMap.get(roundNum)!.push(computo);
  });

  Array.from(roundsMap.entries())
    .sort(([a], [b]) => a - b)
    .forEach(([roundNum, computiInRound]) => {
      treeNodes.push({
        type: "round",
        label: `Round ${roundNum}`,
        roundNumber: roundNum,
        computi: computiInRound,
      });
    });

  const toggleNode = (nodeKey: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeKey)) {
      newExpanded.delete(nodeKey);
    } else {
      newExpanded.add(nodeKey);
    }
    setExpandedNodes(newExpanded);
  };

  const getNodeKey = (node: TreeNode) => {
    return node.type === "progetto" ? "progetto" : `round-${node.roundNumber}`;
  };

  const isExpanded = (node: TreeNode) => {
    return expandedNodes.has(getNodeKey(node));
  };

  return (
    <div className="space-y-2">
      {treeNodes.map((node) => {
        const nodeKey = getNodeKey(node);
        const expanded = isExpanded(node);
        const nodeColor = getRoundColor(node.roundNumber);
        const badgeColor = getRoundBadgeColor(node.roundNumber);

        return (
          <div key={nodeKey} className="space-y-2">
            {/* Folder header */}
            <button
              onClick={() => toggleNode(nodeKey)}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 transition-colors hover:bg-muted/50",
                nodeColor
              )}
            >
              {expanded ? (
                <ChevronDown className="h-4 w-4 flex-shrink-0" />
              ) : (
                <ChevronRight className="h-4 w-4 flex-shrink-0" />
              )}
              <FolderOpen className="h-4 w-4 flex-shrink-0" />
              <span className="font-semibold text-sm flex-1 text-left">{node.label}</span>
              <Badge variant="outline" className={cn("text-xs border", badgeColor)}>
                {node.computi.length} {node.computi.length === 1 ? "computo" : "computi"}
              </Badge>
            </button>

            {/* Children */}
            {expanded && (
              <div className="ml-4 space-y-2 border-l-2 border-muted pl-3">
                {node.computi.map((computo) => {
                  const isSelected = selectedComputoId === computo.id;
                  const displayName = computo.tipo === "progetto" 
                    ? computo.nome 
                    : computo.impresa || "Impresa senza nome";

                  return (
                    <div
                      key={computo.id}
                      className={cn(
                        "flex items-start gap-2 p-3 rounded-lg border transition-colors",
                        isSelected
                          ? "bg-primary/5 border-primary"
                          : "bg-background hover:bg-muted/30 border-border"
                      )}
                    >
                      <FileText className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-sm">{displayName}</span>
                          {computo.tipo === "progetto" ? (
                            <Badge className={cn("text-xs", badgeColor)}>
                              Progetto
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              Round {computo.round_number ?? 1}
                            </Badge>
                          )}
                          {computo.coerenza_status === "ok" && (
                            <span className="text-xs text-green-600">✅ Coerente</span>
                          )}
                          {computo.coerenza_status === "warning" && (
                            <span className="text-xs text-amber-600">⚠️ Variazioni</span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span>{formatDate(computo.created_at)}</span>
                          <span className="font-mono font-medium">
                            {formatCurrency(computo.importo_totale)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onSelectComputo(computo.id)}
                          className="h-8 px-2"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeleteComputo(computo.id, displayName)}
                          disabled={isDeleting}
                          className="h-8 px-2 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {treeNodes.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
          <Upload className="h-12 w-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Nessun computo importato. Carica un file Excel per iniziare.
          </p>
        </div>
      )}
    </div>
  );
}
