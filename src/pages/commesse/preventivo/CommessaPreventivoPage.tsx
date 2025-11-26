import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Clock3, Download, Euro, Layers3 } from "lucide-react";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { CommessaPageHeader } from "@/components/CommessaPageHeader";
import { CommessaSummaryStrip } from "@/components/commessa/CommessaSummaryStrip";
import { formatCurrency, formatShortDate, formatDateTime, groupComputi } from "@/lib/formatters";

export default function CommessaPreventivoPage() {
  const { id } = useParams();
  const { commessa } = useCommessaContext();
  const { progetto, ritorni } = groupComputi(commessa?.computi);
  const backHref = id ? `/commesse/${id}/overview` : "/commesse";
  const updatedAt = commessa?.updated_at ?? commessa?.created_at ?? null;

  const summaryMetrics = useMemo(() => {
    const roundValues = Array.from(
      new Set(
        ritorni
          .map((r) => (typeof r.round_number === "number" ? r.round_number : null))
          .filter((value): value is number => value !== null),
      ),
    ).sort((a, b) => a - b);

    const roundsHelper =
      roundValues.length === 0
        ? "Nessun round caricato"
        : roundValues.length === 1
          ? `Round ${roundValues[0]}`
          : `Round ${roundValues[0]} - ${roundValues[roundValues.length - 1]}`;

    return [
      {
        label: "Importo progetto",
        value: progetto.length ? formatCurrency(progetto[0].importo_totale) : "—",
        helper: progetto[0]?.nome,
        icon: <Euro className="h-5 w-5 text-primary" />,
        emphasise: true,
      },
      {
        label: "Computi totali",
        value: String(commessa?.computi?.length ?? 0),
        helper: `${progetto.length} progetto · ${ritorni.length} ritorni`,
        icon: <Layers3 className="h-5 w-5 text-primary" />,
      },
      {
        label: "Round di gara",
        value: String(roundValues.length),
        helper: roundsHelper,
        icon: <BarChart3 className="h-5 w-5 text-primary" />,
      },
      {
        label: "Ultimo aggiornamento",
        value: formatShortDate(updatedAt),
        helper: formatDateTime(updatedAt),
        icon: <Clock3 className="h-5 w-5 text-primary" />,
      },
    ];
  }, [commessa?.computi?.length, progetto, ritorni, updatedAt]);

  const recentActivity = useMemo(() => {
    return [...(commessa?.computi ?? [])]
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )
      .slice(0, 5)
      .map((computo) => ({
        id: computo.id,
        title: computo.nome,
        meta:
          computo.tipo === "progetto"
            ? "Computo di progetto"
            : `Ritorno round ${computo.round_number ?? "-"}`,
        timestamp: formatDateTime(computo.updated_at),
      }));
  }, [commessa?.computi]);

  const primaryComputo = progetto[0];

  return (
    <div className="flex flex-col gap-5">
      <CommessaPageHeader
        commessa={commessa}
        title="Preventivo"
        description="Apri il computo di progetto per calcolare il preventivo o confronta rapidamente i ritorni di gara."
        backHref={backHref}
      >
        <CommessaSummaryStrip metrics={summaryMetrics} />
      </CommessaPageHeader>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="space-y-4">
          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-lg font-semibold">Computo di progetto</CardTitle>
                <CardDescription>
                  Carica o apri il computo principale per ottenere il preventivo dettagliato.
                </CardDescription>
              </div>
              <Badge variant="secondary" className="px-3 py-1 text-sm">
                {progetto.length} computi
              </Badge>
            </CardHeader>
            <CardContent>
              {progetto.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Nessun computo di progetto disponibile. Carica un computo per abilitare il preventivo.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {progetto.map((computo) => (
                    <Card
                      key={computo.id}
                      className="rounded-xl border border-border/60 bg-muted/30 shadow-sm"
                    >
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">{computo.nome}</CardTitle>
                        <CardDescription>Importo: {formatCurrency(computo.importo_totale)}</CardDescription>
                      </CardHeader>
                      <CardContent className="flex items-center justify-between">
                        <Badge variant="secondary">Progetto</Badge>
                        <Button asChild>
                          <Link to={`/commesse/${id}/preventivo/${computo.id}`}>
                            Apri preventivo
                          </Link>
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-lg font-semibold">Ritorni di gara</CardTitle>
                <CardDescription>
                  Seleziona un ritorno per confrontare rapidamente il preventivo con le offerte caricate.
                </CardDescription>
              </div>
              <Badge variant="secondary" className="px-3 py-1 text-sm">
                {ritorni.length} ritorni
              </Badge>
            </CardHeader>
            <CardContent>
              {ritorni.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Nessun ritorno caricato. Aggiungi almeno un ritorno per confrontare le offerte.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {ritorni.map((computo) => (
                    <Card key={computo.id} className="rounded-xl border border-border/60 bg-muted/30 shadow-sm">
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">{computo.nome}</CardTitle>
                        <CardDescription>
                          Importo: {formatCurrency(computo.importo_totale)}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="flex items-center justify-between">
                        <div className="space-y-1 text-xs text-muted-foreground">
                          {computo.impresa && <p>Impresa: {computo.impresa}</p>}
                          {computo.round_number && <p>Round: {computo.round_number}</p>}
                        </div>
                        <Button asChild variant="outline">
                          <Link to={`/commesse/${id}/preventivo/${computo.id}`}>
                            Apri
                          </Link>
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle className="text-lg font-semibold">Azioni rapide</CardTitle>
              <CardDescription>Attiva il preventivo o esporta i dati in pochi clic.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                asChild
                className="w-full justify-between gap-2"
                disabled={!primaryComputo}
              >
                <Link to={primaryComputo ? `/commesse/${id}/preventivo/${primaryComputo.id}` : "#"}>
                  Apri computo principale
                </Link>
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between gap-2"
                disabled={!ritorni.length}
              >
                <BarChart3 className="h-4 w-4" />
                Avvia confronto offerte
              </Button>
              <Button variant="outline" className="w-full justify-between gap-2" disabled>
                <Download className="h-4 w-4" />
                Esporta preventivo
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-border/60 bg-card shadow-md">
            <CardHeader>
              <CardTitle className="text-lg font-semibold">Attività recenti</CardTitle>
              <CardDescription>Ultimi caricamenti o modifiche sulla commessa.</CardDescription>
            </CardHeader>
            <CardContent>
              {recentActivity.length ? (
                <ol className="space-y-4">
                  {recentActivity.map((activity) => (
                    <li key={activity.id} className="flex gap-3">
                      <div className="mt-1 h-2 w-2 rounded-full bg-primary" />
                      <div>
                        <p className="text-sm font-semibold text-foreground">{activity.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {activity.meta} · {activity.timestamp}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Nessuna attività recente disponibile.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

