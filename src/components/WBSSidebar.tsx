import { useState, MouseEvent } from "react";
import { ChevronRight, ChevronDown, Folder, MapPin, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { FrontendWbsNode } from "@/types/api";

interface WBSSidebarProps {
  nodes: FrontendWbsNode[];
  onNodeClick?: (nodeId: string | null) => void;
  selectedNodeId?: string | null;
  onCollapse?: () => void;
}

/**
 * Determina se un livello WBS è spaziale (da 1 a 5)
 */
const isSpazialeLevel = (level: number) => level <= 5;

/**
 * Filtra la struttura WBS mostrando solo i nodi fino al livello 6
 * (livello analitico massimo da considerare).
 */
const filterWbsStructuralTree = (nodes: FrontendWbsNode[]): FrontendWbsNode[] => {
  return nodes
    .filter((node) => node.level <= 7)
    .map((node) => ({
      ...node,
      children: node.children ? filterWbsStructuralTree(node.children) : [],
    }));
};

interface SidebarNodeProps {
  node: FrontendWbsNode;
  level: number;
  onNodeClick?: (nodeId: string | null) => void;
  selectedNodeId?: string | null;
}

/**
 * Nodo della sidebar WBS. Rappresenta un livello spaziale o analitico (fino alla WBS6).
 */
function SidebarNode({ node, level, onNodeClick, selectedNodeId }: SidebarNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = (node.children?.length ?? 0) > 0;
  const isSpaziale = isSpazialeLevel(node.level);
  const isAnalitico = node.level >= 6;
  const isSelected = selectedNodeId === node.id;

  const handleToggle = (event: MouseEvent) => {
    event.stopPropagation();
    setIsExpanded((prev) => !prev);
  };

  const handleSelect = () => {
    if (onNodeClick) {
      onNodeClick(node.id);
    }
  };

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-2 px-2 py-1.5 cursor-pointer transition-all duration-150 rounded-sm",
          "hover:bg-accent/20",
          isSelected && "bg-primary/10 border-l-2 border-primary"
        )}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={handleSelect}
      >
        {hasChildren ? (
          <button
            className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors"
            onClick={handleToggle}
          >
            {isExpanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>
        ) : (
          <div className="w-3.5" />
        )}

        {isSpaziale ? (
          <MapPin className="h-4 w-4 flex-shrink-0 text-blue-500" />
        ) : (
          <Folder className="h-4 w-4 flex-shrink-0 text-primary" />
        )}

        <div className="flex flex-col gap-0.5">
          <span
            className={cn(
              "font-mono text-xs",
              isSpaziale && "text-blue-600 dark:text-blue-400",
              isAnalitico && "text-primary font-semibold"
            )}
          >
            {node.code ?? ""}
          </span>
          <span className="text-xs text-foreground/90 truncate max-w-[200px]">
            {node.description ?? "Senza descrizione"}
          </span>
        </div>

        <span className="ml-auto text-xs font-mono text-muted-foreground">
          {node.importo?.toLocaleString("it-IT", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }) ?? "0,00"}
        </span>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <SidebarNode
              key={child.id}
              node={child}
              level={level + 1}
              onNodeClick={onNodeClick}
              selectedNodeId={selectedNodeId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Sidebar WBS – mostra la struttura fino alla WBS6
 * Allinea il comportamento alla logica di analisi WBS6 del backend.
 */
export function WBSSidebar({ nodes, onNodeClick, selectedNodeId, onCollapse }: WBSSidebarProps) {
  const handleResetFilter = () => {
    if (onNodeClick) onNodeClick(null);
  };

  const filteredNodes = filterWbsStructuralTree(nodes);

  return (
    <div className="flex flex-col h-full bg-background border-l border-border">
      <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
        <h3 className="font-semibold text-sm">Struttura WBS (fino a WBS6)</h3>
        {onCollapse && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onCollapse}
            className="h-8 w-8"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
      </div>

      <div className="px-4 py-2 border-b">
        <Button
          variant={selectedNodeId === null ? "default" : "outline"}
          size="sm"
          className="w-full"
          onClick={handleResetFilter}
        >
          Tutto il computo
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredNodes.length > 0 ? (
          filteredNodes.map((node) => (
            <SidebarNode
              key={node.id}
              node={node}
              level={0}
              onNodeClick={onNodeClick}
              selectedNodeId={selectedNodeId}
            />
          ))
        ) : (
          <div className="p-8 text-center text-muted-foreground text-sm">
            Nessuna struttura WBS disponibile
          </div>
        )}
      </div>
    </div>
  );
}
