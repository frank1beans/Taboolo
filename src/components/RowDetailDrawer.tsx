import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface RowDetailDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  data: Record<string, any> | null;
  fields: {
    key: string;
    label: string;
    render?: (value: any, data: Record<string, any>) => React.ReactNode;
  }[];
}

export function RowDetailDrawer({
  open,
  onOpenChange,
  title,
  data,
  fields,
}: RowDetailDrawerProps) {
  if (!data) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl">
        <SheetHeader className="space-y-2">
          <SheetTitle className="text-xl">{title}</SheetTitle>
          <SheetDescription>
            Dettagli completi della voce selezionata
          </SheetDescription>
        </SheetHeader>

        <Separator className="my-4" />

        <ScrollArea className="h-[calc(100vh-140px)] pr-4">
          <div className="space-y-6">
            {fields.map((field) => {
              const value = data[field.key];
              const isEmpty = value == null || value === "" || value === "-";

              return (
                <div key={field.key} className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      {field.label}
                    </span>
                    {isEmpty && (
                      <Badge variant="outline" className="h-5 text-xs">
                        Non disponibile
                      </Badge>
                    )}
                  </div>
                  <div className="rounded-lg bg-muted/30 p-3">
                    {field.render ? (
                      field.render(value, data)
                    ) : isEmpty ? (
                      <span className="text-sm text-muted-foreground">-</span>
                    ) : (
                      <span className="text-sm">{String(value)}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
