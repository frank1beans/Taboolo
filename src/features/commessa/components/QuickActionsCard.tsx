import { ReactNode } from "react";
import { Download, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface QuickActionsCardProps {
  headerAction?: ReactNode;
  uploadAction: ReactNode;
  className?: string;
}

export const QuickActionsCard = ({
  headerAction,
  uploadAction,
  className,
}: QuickActionsCardProps) => {
  return (
    <Card className={`rounded-2xl border border-primary/30 bg-primary/5 shadow-md ${className ?? ""}`}>
      <CardHeader className="flex flex-row items-start justify-between pb-4">
        <div className="space-y-1">
          <CardTitle className="text-lg font-semibold normal-case">Azioni rapide</CardTitle>
          <CardDescription>Importa, esporta o genera report</CardDescription>
        </div>
        {headerAction}
      </CardHeader>
      <CardContent className="space-y-3">
        {uploadAction}
        <Button variant="outline" className="w-full justify-start gap-2" disabled>
          <Download className="h-4 w-4" />
          Esporta computi
        </Button>
        <Button variant="outline" className="w-full justify-start gap-2" disabled>
          <BarChart3 className="h-4 w-4" />
          Crea report
        </Button>
      </CardContent>
    </Card>
  );
};
