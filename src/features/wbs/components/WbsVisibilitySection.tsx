import { Eye, EyeOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { VisibilitySection } from "../types";

interface WbsVisibilitySectionProps {
  section: VisibilitySection;
  disabled?: boolean;
  onToggle: (nodeId: number, visible: boolean) => void;
  onShowAll: () => void;
  onHideAll: () => void;
}

export function WbsVisibilitySection({
  section,
  disabled,
  onToggle,
  onShowAll,
  onHideAll,
}: WbsVisibilitySectionProps) {
  const visibleCount = section.nodes.filter((node) => !node.hidden).length;
  const hiddenCount = section.nodes.length - visibleCount;

  const canShowAll = hiddenCount > 0;
  const canHideAll = visibleCount > 0;

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>{section.title}</CardTitle>
          <CardDescription>
            {section.nodes.length} nodi importati · Visibili {visibleCount} · Nascosti{" "}
            {hiddenCount}
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onShowAll}
            disabled={disabled || !canShowAll}
            className="inline-flex items-center gap-1.5"
          >
            <Eye className="h-4 w-4" />
            Mostra tutto
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onHideAll}
            disabled={disabled || !canHideAll}
            className="inline-flex items-center gap-1.5"
          >
            <EyeOff className="h-4 w-4" />
            Nascondi tutto
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {section.nodes.length === 0 ? (
          <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
            Nessun nodo corrisponde al filtro corrente.
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Codice</TableHead>
                  <TableHead>Descrizione</TableHead>
                  <TableHead className="w-32 text-center">Stato</TableHead>
                  <TableHead className="w-48 text-center">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {section.nodes.map((node) => {
                  const isVisible = !node.hidden;
                  return (
                    <TableRow key={node.id}>
                      <TableCell className="font-mono text-sm font-medium">
                        {node.code || "—"}
                      </TableCell>
                      <TableCell className="text-sm">{node.description || "—"}</TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant={isVisible ? "default" : "outline"}
                          className={isVisible ? "bg-green-600 hover:bg-green-600" : ""}
                        >
                          {isVisible ? "Visibile" : "Nascosta"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-2">
                          <Switch
                            checked={isVisible}
                            onCheckedChange={(checked) => onToggle(node.id, checked)}
                            disabled={disabled}
                          />
                          <span className="text-xs text-muted-foreground">
                            {isVisible ? "Mostrata nelle viste" : "Esclusa dalle viste"}
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
