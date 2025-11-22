import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Upload, FileText, TrendingUp, Loader2, Settings } from "lucide-react";
import { Link } from "react-router-dom";
import { useDashboardStats } from "@/hooks/useDashboardStats";

const Home = () => {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/30" role="status" aria-live="polite">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">Caricamento dati dashboard in corso...</span>
      </div>
    );
  }

  return (
    <main className="page-container">
      <div className="page-content">
        <div className="page-header">
          <h1 className="text-display mb-2">Dashboard</h1>
          <p className="text-body-sm text-muted-foreground">
            Sistema di gestione computi metrici e analisi gare
          </p>
        </div>

        <section className="stats-grid section-spacing" aria-label="Statistiche principali">
          <Card variant="ghost" role="article" aria-label="Commesse attive">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground/70 font-normal mb-3">Commesse Attive</CardTitle>
              <div className="text-5xl font-light tracking-tighter tabular-nums" aria-label={`${stats?.commesseAttive || 0} commesse attive`}>{stats?.commesseAttive || 0}</div>
              <p className="text-xs font-light text-muted-foreground/60 mt-2 uppercase tracking-wider">In gestione</p>
            </CardHeader>
          </Card>

          <Card variant="ghost" role="article" aria-label="Computi caricati">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground/70 font-normal mb-3">Computi Caricati</CardTitle>
              <div className="text-5xl font-light tracking-tighter tabular-nums" aria-label={`${stats?.computiCaricati || 0} computi caricati`}>{stats?.computiCaricati || 0}</div>
              <p className="text-xs font-light text-muted-foreground/60 mt-2 uppercase tracking-wider">Totale importati</p>
            </CardHeader>
          </Card>

          <Card variant="ghost" role="article" aria-label="Ritorni di gara">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground/70 font-normal mb-3">Ritorni di Gara</CardTitle>
              <div className="text-5xl font-light tracking-tighter tabular-nums" aria-label={`${stats?.ritorni || 0} ritorni di gara`}>{stats?.ritorni || 0}</div>
              <p className="text-xs font-light text-muted-foreground/60 mt-2 uppercase tracking-wider">Offerte analizzate</p>
            </CardHeader>
          </Card>

          <Card variant="ghost" role="article" aria-label="Report generati">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground/70 font-normal mb-3">Report Generati</CardTitle>
              <div className="text-5xl font-light tracking-tighter tabular-nums" aria-label={`${stats?.reportGenerati || 0} report generati`}>{stats?.reportGenerati || 0}</div>
              <p className="text-xs font-light text-muted-foreground/60 mt-2 uppercase tracking-wider">In sviluppo</p>
            </CardHeader>
          </Card>
        </section>

        <section className="content-grid content-grid-2 section-spacing-lg" aria-label="Azioni rapide">
          <Card variant="ghost" role="region" aria-label="Azioni rapide">
            <CardHeader className="p-4 pb-3">
              <CardTitle className="text-xs">Azioni Rapide</CardTitle>
              <CardDescription className="text-xs">Operazioni più comuni</CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-2">
              <Link to="/commesse">
                <Button className="w-full justify-start" variant="outline" size="sm">
                  <FolderOpen className="mr-2 h-3 w-3" />
                  <span className="text-xs font-bold tracking-wider">VISUALIZZA COMMESSE</span>
                </Button>
              </Link>
              <Link to="/settings">
                <Button className="w-full justify-start" variant="outline" size="sm">
                  <Settings className="mr-2 h-3 w-3" />
                  <span className="text-xs font-bold tracking-wider">IMPOSTAZIONI</span>
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card variant="ghost" role="region" aria-label="Attività recente">
            <CardHeader className="p-4 pb-3">
              <CardTitle className="text-xs">Attività Recente</CardTitle>
              <CardDescription className="text-xs">Ultime modifiche al sistema</CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              {!stats?.attivitaRecente || stats.attivitaRecente.length === 0 ? (
                <p className="text-xs font-light text-muted-foreground">Nessuna attività recente</p>
              ) : (
                <ul className="space-y-3" role="list" aria-label="Lista attività recenti">
                  {stats.attivitaRecente.map((item, i) => (
                    <li key={i} className="border-b border-border/40 pb-3 last:border-0 last:pb-0">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-bold uppercase tracking-wider">{item.action}</p>
                          <p className="text-xs font-light text-muted-foreground truncate">{item.commessa}</p>
                        </div>
                        <time className="text-xs font-light text-muted-foreground whitespace-nowrap">{item.time}</time>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
};

export default Home;
