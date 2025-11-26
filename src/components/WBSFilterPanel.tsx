import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ChevronDown,
  ChevronRight,
  Search,
  X,
  MapPin,
  Folder,
  FolderOpen,
  FileText,
  Filter,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FrontendWbsNode } from "@/types/api";
import { formatCurrency } from "@/lib/grid-utils";

export interface WBSFilterPanelProps {
  nodes: FrontendWbsNode[];
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string | null) => void;
  onClose?: () => void;
  title?: string;
  enableSearch?: boolean;
  showAmounts?: boolean;
  autoExpandLevel?: number;
}

interface WBSNodeItemProps {
  node: FrontendWbsNode;
  level: number;
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string) => void;
  searchQuery: string;
  autoExpandLevel: number;
  showAmounts: boolean;
}

const WBSNodeItem = ({
  node,
  level,
  selectedNodeId,
  onNodeSelect,
  searchQuery,
  autoExpandLevel,
  showAmounts,
}: WBSNodeItemProps) => {
  const [isExpanded, setIsExpanded] = useState(level <= autoExpandLevel);

  const hasChildren = node.children && node.children.length > 0;
  const nodeKey = node.id;
  const isSelected = selectedNodeId === nodeKey;

  // Determine if node matches search
  const matchesSearch = useMemo(() => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      node.code?.toLowerCase().includes(query) ||
      node.description?.toLowerCase().includes(query)
    );
  }, [node, searchQuery]);

  // Check if any children match search
  const hasMatchingChildren = useMemo(() => {
    if (!searchQuery || !hasChildren) return false;

    const checkNode = (n: FrontendWbsNode): boolean => {
      const query = searchQuery.toLowerCase();
      const matches =
        n.code?.toLowerCase().includes(query) ||
        n.description?.toLowerCase().includes(query);

      if (matches) return true;
      if (n.children) {
        return n.children.some((child) => checkNode(child));
      }
      return false;
    };

    return node.children.some((child) => checkNode(child));
  }, [node, searchQuery, hasChildren]);

  // Auto-expand if has matching children
  const shouldShow = matchesSearch || hasMatchingChildren;

  // Auto-expand when searching and has matching children
  const actuallyExpanded = searchQuery
    ? hasMatchingChildren || isExpanded
    : isExpanded;

  // Icon based on level and state
  const NodeIcon = useMemo(() => {
    if (node.level <= 5) return MapPin;
    if (hasChildren) {
      return actuallyExpanded ? FolderOpen : Folder;
    }
    return FileText;
  }, [node.level, hasChildren, actuallyExpanded]);

  const iconColor = useMemo(() => {
    if (node.level <= 5) return "text-foreground/70";
    if (hasChildren) return "text-muted-foreground";
    return "text-muted-foreground/80";
  }, [node.level, hasChildren]);

  if (!shouldShow) return null;

  const paddingLeft = `${level * 12 + 8}px`;

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-2 py-2 px-2 cursor-pointer transition-all",
          "hover:bg-muted/60 rounded-md",
          isSelected && "bg-primary/8 ring-1 ring-primary/25 shadow-sm"
        )}
        style={{ paddingLeft }}
        onClick={() => nodeKey && onNodeSelect(nodeKey)}
      >
        {/* Expand/Collapse button */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!actuallyExpanded);
            }}
            className="flex-shrink-0 p-0.5 hover:bg-accent rounded"
          >
            {actuallyExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        ) : (
          <div className="w-5" />
        )}

        {/* Icon */}
        <NodeIcon className={cn("h-4 w-4 flex-shrink-0", iconColor)} />

        {/* Level badge */}
        <Badge
          variant="outline"
          className="text-[11px] font-mono flex-shrink-0 border-border/50"
        >
          L{node.level}
        </Badge>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {node.code && (
              <span className="text-sm font-medium font-mono text-foreground">
                {node.code}
              </span>
            )}
            {node.description && (
              <span className="text-sm text-muted-foreground truncate">
                {node.description}
              </span>
            )}
          </div>
        </div>

        {/* Amount */}
        {showAmounts && node.importo !== null && (
          <span className="text-xs font-mono font-semibold text-primary/80 flex-shrink-0">
            {formatCurrency(node.importo)}
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && actuallyExpanded && (
        <div>
          {node.children.map((child) => (
            <WBSNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              selectedNodeId={selectedNodeId}
              onNodeSelect={onNodeSelect}
              searchQuery={searchQuery}
              autoExpandLevel={autoExpandLevel}
              showAmounts={showAmounts}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export function WBSFilterPanel({
  nodes,
  selectedNodeId,
  onNodeSelect,
  onClose,
  title = "Filtro WBS",
  enableSearch = true,
  showAmounts = true,
  autoExpandLevel = 2,
}: WBSFilterPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const handleClearFilter = () => {
    onNodeSelect(null);
    setSearchQuery("");
  };

  const selectedNode = useMemo(() => {
    const findNode = (
      list: FrontendWbsNode[],
      key: string
    ): FrontendWbsNode | null => {
      for (const node of list) {
        if (node.id === key) return node;
        if (node.children) {
          const found = findNode(node.children, key);
          if (found) return found;
        }
      }
      return null;
    };

    return selectedNodeId ? findNode(nodes, selectedNodeId) : null;
  }, [nodes, selectedNodeId]);

  return (
    <div className="flex flex-col h-full bg-background border-l">
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-muted-foreground" />
            <h3 className="font-semibold text-base">{title}</h3>
          </div>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Search */}
        {enableSearch && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Cerca per codice o descrizione..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-8"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2"
              >
                <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
              </button>
            )}
          </div>
        )}

        {/* Active filter badge */}
        {selectedNode && (
          <div className="flex items-center gap-2 p-2 bg-accent rounded-md">
            <Filter className="h-4 w-4 text-primary flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-xs text-muted-foreground">
                Filtro attivo:
              </div>
              <div className="text-sm font-semibold truncate">
                {selectedNode.code} - {selectedNode.description}
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilter}
              className="flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Tree */}
      <ScrollArea className="flex-1 p-2">
        {nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <Folder className="h-12 w-12 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">
              Nessuna struttura WBS disponibile
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {nodes.map((node) => (
              <WBSNodeItem
                key={node.id}
                node={node}
                level={0}
                selectedNodeId={selectedNodeId}
                onNodeSelect={onNodeSelect}
                searchQuery={searchQuery}
                autoExpandLevel={autoExpandLevel}
                showAmounts={showAmounts}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer stats */}
      <div className="p-4 border-t bg-muted/30">
        <div className="text-xs text-muted-foreground space-y-1">
          <div className="flex justify-between">
            <span>Nodi totali:</span>
            <span className="font-semibold text-foreground">
              {nodes.length}
            </span>
          </div>
          {searchQuery && (
            <div className="flex justify-between">
              <span>Ricerca attiva</span>
              <Badge variant="secondary" className="text-xs">
                "{searchQuery}"
              </Badge>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
