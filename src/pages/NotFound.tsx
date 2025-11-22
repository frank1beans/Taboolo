// NotFound.tsx
import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-lg">
        <Card variant="elevated">
          <CardHeader className="text-center space-y-2">
            <CardTitle className="text-4xl font-bold tracking-tight">404</CardTitle>
            <p className="text-sm text-muted-foreground">
              La pagina che stai cercando non esiste o è stata spostata.
            </p>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4 pb-6">
            <p className="text-xs font-mono text-muted-foreground">
              Percorso: <span className="font-semibold">{location.pathname}</span>
            </p>
            <Button asChild>
              <Link to="/">Torna alla dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NotFound;
