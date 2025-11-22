import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ComputoTreeView, ComputoTreeItem } from "@/components/ComputoTreeView";

interface ComputoListCardProps {
  computi: ComputoTreeItem[];
  onDeleteComputo: (computoId: number, computoName: string) => void;
  isDeleting: boolean;
  className?: string;
}

export const ComputoListCard = ({
  computi,
  onDeleteComputo,
  isDeleting,
  className,
}: ComputoListCardProps) => {
  return (
    <Card className={`rounded-2xl border border-border/60 bg-card shadow-md ${className ?? ""}`}>
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <CardTitle className="text-lg font-semibold normal-case">Tutti i computi</CardTitle>
          <CardDescription className="mt-1">
            Naviga il computo di progetto e i ritorni organizzati per round di gara.
          </CardDescription>
        </div>
        <Badge variant="secondary" className="px-3 py-1 text-sm">
          {computi.length} computi
        </Badge>
      </CardHeader>
      <CardContent>
        <ComputoTreeView
          computi={computi}
          onSelectComputo={() => {}}
          onDeleteComputo={onDeleteComputo}
          selectedComputoId={null}
          isDeleting={isDeleting}
        />
      </CardContent>
    </Card>
  );
};
