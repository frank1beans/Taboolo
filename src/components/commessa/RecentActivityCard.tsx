import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export type ActivityItem = {
  id: number;
  title: string;
  meta: string;
  timestamp: string;
};

interface RecentActivityCardProps {
  activities: ActivityItem[];
  className?: string;
}

export const RecentActivityCard = ({
  activities,
  className,
}: RecentActivityCardProps) => {
  return (
    <Card className={`rounded-2xl border border-border/60 bg-card shadow-md ${className ?? ""}`}>
      <CardHeader>
        <CardTitle className="text-lg font-semibold normal-case">Attività recenti</CardTitle>
        <CardDescription>Ultime importazioni e modifiche</CardDescription>
      </CardHeader>
      <CardContent>
        {activities.length ? (
          <ol className="space-y-4">
            {activities.map((activity) => (
              <li key={activity.id} className="flex gap-3">
                <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-foreground">{activity.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {activity.meta} - {activity.timestamp}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-muted-foreground">
            Nessuna attività recente sulla commessa.
          </p>
        )}
      </CardContent>
    </Card>
  );
};
