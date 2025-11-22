import { useMemo } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api-client";
import { CommessaStatusBadge } from "@/components/ui/status-badge";

const sectionMap: Record<string, string> = {
  commesse: "Commesse",
  "elenco-prezzi": "Elenco prezzi",
  settings: "Impostazioni",
};

export function TopBar() {
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const params = useParams();

  const segments = location.pathname.split("/").filter(Boolean);
  const isCommessaRoute = segments[0] === "commesse" && segments[1];
  const commessaId = isCommessaRoute ? segments[1] : null;

  // Fetch commessa data if we're in a commessa route
  const { data: commessa } = useQuery({
    queryKey: ["commessa", commessaId, "layout"],
    queryFn: () => api.getCommessa(commessaId!),
    enabled: Boolean(commessaId),
  });

  const currentTitle = useMemo(() => {
    if (!segments.length) return "Dashboard";
    return sectionMap[segments[0]] ?? segments[0];
  }, [segments]);

  const handleThemeToggle = () => setTheme(theme === "dark" ? "light" : "dark");

  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70 h-[44px]" role="banner">
      <div className="flex w-full h-full items-center px-4 gap-3">
        <div className="flex flex-1 items-center gap-3">
          <SidebarTrigger
            className="h-7 w-7 rounded-xl border border-border/60 bg-card/80 p-1 text-muted-foreground shadow-sm transition hover:bg-accent"
            aria-label="Apri/chiudi menu laterale"
          />
          
          {isCommessaRoute && commessa ? (
            <div className="flex items-center gap-2">
              <div className="flex flex-col">
                <h1 className="text-xs font-semibold text-foreground leading-tight">
                  {commessa.nome}
                </h1>
                <div className="flex items-center gap-1">
                  <span className="text-[9px] text-muted-foreground font-mono">{commessa.codice}</span>
                  {commessa.business_unit && (
                    <>
                      <span className="text-[9px] text-muted-foreground">•</span>
                      <span className="text-[9px] text-muted-foreground">{commessa.business_unit}</span>
                    </>
                  )}
                </div>
              </div>
              {commessa.stato && (
                <CommessaStatusBadge
                  status={commessa.stato}
                  size="xs"
                  className="ml-1.5"
                />
              )}
            </div>
          ) : (
            <h1 className="text-sm font-semibold text-foreground">{currentTitle}</h1>
          )}
        </div>

        <div className="flex items-center gap-1.5" role="navigation" aria-label="Azioni principali">
          {!isCommessaRoute ? (
            <>
              <Button 
                size="sm" 
                variant="outline" 
                className="h-7 text-[11px] rounded-xl px-2.5"
                onClick={() => navigate("/commesse")}
              >
                Commesse
              </Button>
              <Button 
                size="sm" 
                variant="default" 
                className="h-7 text-[11px] rounded-xl px-2.5"
                onClick={() => navigate("/commesse?new=true")}
              >
                Nuova commessa
              </Button>
            </>
          ) : (
            <Button 
              size="sm" 
              variant="ghost" 
              className="h-7 text-[11px] px-2.5"
              onClick={() => navigate("/commesse")}
            >
              Portfolio
            </Button>
          )}
          
          {user ? (
            <>
              <Button 
                size="sm" 
                variant="outline" 
                className="h-7 text-[11px] px-2.5" 
                onClick={() => navigate("/profile")}
              >
                Profilo
              </Button>
              <Button 
                size="sm" 
                variant="ghost" 
                className="h-7 text-[11px] px-2.5" 
                onClick={logout}
              >
                Logout
              </Button>
            </>
          ) : null}
          
          <Button
            variant="ghost"
            size="icon"
            onClick={handleThemeToggle}
            className="h-7 w-7 rounded-xl border border-border/60 bg-card/70 shadow-sm transition hover:bg-accent"
            aria-label={theme === "dark" ? "Passa al tema chiaro" : "Passa al tema scuro"}
          >
            <Sun className="h-3.5 w-3.5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" aria-hidden="true" />
            <Moon className="absolute h-3.5 w-3.5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" aria-hidden="true" />
            <span className="sr-only">Cambia tema</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
