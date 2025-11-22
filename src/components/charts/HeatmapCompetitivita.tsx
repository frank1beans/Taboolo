import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { TrendingDown, TrendingUp, Minus, Target } from "lucide-react";

interface CategoriaCompetitivita {
  categoria: string;
  importoProgetto: number;
}

interface ImpresaCompetitivita {
  impresa: string;
  categorie: {
    categoria: string;
    importoOfferta: number;
    delta: number; // Percentuale rispetto al progetto
    rank?: number; // Posizione tra le imprese per questa categoria
  }[];
}

interface HeatmapCompetitivitaProps {
  categorie: CategoriaCompetitivita[];
  imprese: ImpresaCompetitivita[];
}

type CellData = {
  impresa: string;
  categoria: string;
  delta: number;
  importo: number;
  rank: number;
  isWinner: boolean;
};

// Funzione per ottenere il colore basato sul delta
const getColorFromDelta = (delta: number): string => {
  // Verde intenso per risparmi > 20%
  if (delta < -20) return "bg-green-700 text-white dark:bg-green-600";
  // Verde per risparmi 10-20%
  if (delta < -10) return "bg-green-600 text-white dark:bg-green-500";
  // Verde chiaro per risparmi 0-10%
  if (delta < 0) return "bg-green-500 text-white dark:bg-green-400";
  // Giallo per variazioni 0-5%
  if (delta < 5) return "bg-yellow-400 text-gray-900 dark:bg-yellow-500";
  // Arancione per aumenti 5-15%
  if (delta < 15) return "bg-orange-500 text-white dark:bg-orange-600";
  // Rosso chiaro per aumenti 15-30%
  if (delta < 30) return "bg-red-600 text-white dark:bg-red-700";
  // Rosso intenso per aumenti > 30%
  return "bg-red-700 text-white dark:bg-red-800";
};

const formatEuro = (value: number): string => {
  if (value >= 1_000_000) {
    return `€${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `€${(value / 1_000).toFixed(0)}k`;
  }
  return `€${value.toLocaleString("it-IT")}`;
};

export function HeatmapCompetitivita({ categorie, imprese }: HeatmapCompetitivitaProps) {
  // Calcola rank per ogni categoria
  const heatmapData = useMemo(() => {
    if (!categorie || !imprese || categorie.length === 0 || imprese.length === 0) {
      return { matrix: [], stats: null };
    }

    const matrix: CellData[][] = [];

    categorie.forEach((cat) => {
      const row: CellData[] = [];

      // Raccoglie tutte le offerte per questa categoria
      const offerteCategoria = imprese
        .map((imp) => {
          const catData = imp.categorie.find((c) => c.categoria === cat.categoria);
          return {
            impresa: imp.impresa,
            delta: catData?.delta ?? 999,
            importo: catData?.importoOfferta ?? 0,
          };
        })
        .filter((o) => o.delta !== 999)
        .sort((a, b) => a.delta - b.delta);

      // Assegna rank
      const rankedOfferte = offerteCategoria.map((off, idx) => ({
        ...off,
        rank: idx + 1,
        isWinner: idx === 0,
      }));

      // Crea le celle per questa riga
      imprese.forEach((imp) => {
        const offerta = rankedOfferte.find((o) => o.impresa === imp.impresa);
        if (offerta) {
          row.push({
            impresa: imp.impresa,
            categoria: cat.categoria,
            delta: offerta.delta,
            importo: offerta.importo,
            rank: offerta.rank,
            isWinner: offerta.isWinner,
          });
        } else {
          row.push({
            impresa: imp.impresa,
            categoria: cat.categoria,
            delta: 0,
            importo: 0,
            rank: 999,
            isWinner: false,
          });
        }
      });

      matrix.push(row);
    });

    // Calcola statistiche per impresa
    const stats = imprese.map((imp) => {
      const celle = matrix.flat().filter((c) => c.impresa === imp.impresa && c.rank !== 999);
      const vittorie = celle.filter((c) => c.isWinner).length;
      const deltaMedio =
        celle.length > 0 ? celle.reduce((sum, c) => sum + c.delta, 0) / celle.length : 0;
      const rankMedio =
        celle.length > 0 ? celle.reduce((sum, c) => sum + c.rank, 0) / celle.length : 999;

      return {
        impresa: imp.impresa,
        vittorie,
        deltaMedio,
        rankMedio,
        categoriePartecipate: celle.length,
      };
    });

    return { matrix, stats };
  }, [categorie, imprese]);

  if (!heatmapData.stats || heatmapData.matrix.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Heatmap Competitività per Categoria
            <InfoTooltip content="Mostra quali imprese sono più competitive su quali categorie WBS. Il verde indica risparmio, il rosso extra-costo." />
          </CardTitle>
          <CardDescription>
            Analisi comparativa della competitività delle imprese
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            Dati insufficienti per mostrare la heatmap di competitività.
          </div>
        </CardContent>
      </Card>
    );
  }

  const { matrix, stats } = heatmapData;

  // Trova la migliore impresa overall
  const bestImpresa = stats.reduce((best, current) =>
    current.deltaMedio < best.deltaMedio ? current : best
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Heatmap Competitività per Categoria
          <InfoTooltip content="Matrice che mostra a colpo d'occhio quali imprese sono più competitive su quali categorie. Verde = competitiva, Rosso = cara. La corona 👑 indica la migliore offerta per categoria." />
        </CardTitle>
        <CardDescription>
          Analisi visuale della competitività delle imprese per macro-categoria
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {stats.map((stat) => {
            const TrendIcon =
              stat.deltaMedio < -5
                ? TrendingDown
                : stat.deltaMedio > 5
                ? TrendingUp
                : Minus;
            const trendColor =
              stat.deltaMedio < -5
                ? "text-green-600"
                : stat.deltaMedio > 5
                ? "text-destructive"
                : "text-muted-foreground";

            return (
              <div
                key={stat.impresa}
                className="p-3 rounded-lg border bg-card hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-2 mb-2">
                  <TrendIcon className={`h-4 w-4 ${trendColor}`} />
                  <p className="text-sm font-medium truncate" title={stat.impresa}>
                    {stat.impresa}
                  </p>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Vittorie:</span>
                    <Badge variant="outline" className="h-5 px-1.5">
                      {stat.vittorie}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Delta medio:</span>
                    <span className={`font-semibold ${trendColor}`}>
                      {stat.deltaMedio > 0 ? "+" : ""}
                      {stat.deltaMedio.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Heatmap Matrix */}
        <div className="overflow-x-auto">
          <div className="min-w-max">
            <table className="w-full border-collapse">
              <thead className="bg-muted/40 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="border-b border-r border-border/60 p-3 text-left">
                    Categoria WBS
                  </th>
                  {imprese.map((imp) => (
                    <th
                      key={imp.impresa}
                      className="border-b border-border/60 p-3 text-center"
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span className="truncate max-w-[100px]" title={imp.impresa}>
                          {imp.impresa}
                        </span>
                        {stats.find((s) => s.impresa === imp.impresa)?.vittorie! > 0 && (
                          <Badge variant="outline" className="h-5 px-1.5 text-xs">
                            {stats.find((s) => s.impresa === imp.impresa)?.vittorie} 👑
                          </Badge>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-muted/30">
                    <td className="border-r border-border/60 bg-background p-3 text-sm font-medium">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate">{categorie[rowIdx].categoria}</span>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {formatEuro(categorie[rowIdx].importoProgetto)}
                        </span>
                      </div>
                    </td>
                    {row.map((cell, cellIdx) => {
                      if (cell.rank === 999) {
                        return (
                          <td
                            key={cellIdx}
                          className="border border-border/60 p-2 text-center bg-muted/20"
                          >
                            <span className="text-xs text-muted-foreground">N/A</span>
                          </td>
                        );
                      }

                      return (
                        <td
                          key={cellIdx}
                          className={`border border-border/60 p-2 text-center ${getColorFromDelta(
                            cell.delta
                          )} cursor-pointer hover:opacity-80 transition-opacity`}
                          title={`${cell.impresa} - ${cell.categoria}\nImporto: ${formatEuro(
                            cell.importo
                          )}\nDelta: ${cell.delta.toFixed(1)}%\nRank: ${cell.rank}°`}
                        >
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-sm font-bold">
                              {cell.delta > 0 ? "+" : ""}
                              {cell.delta.toFixed(1)}%
                            </span>
                            <span className="text-[10px] font-mono opacity-90">
                              {formatEuro(cell.importo)}
                            </span>
                            {cell.isWinner && <span className="text-xs">👑</span>}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-6 p-4 bg-muted/30 rounded-lg border">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-green-700" />
            <span className="text-xs">Risparmio &gt; 20%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-green-500" />
            <span className="text-xs">Risparmio 0-20%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-yellow-400" />
            <span className="text-xs">Allineato ±5%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-orange-500" />
            <span className="text-xs">Extra-costo 5-15%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-red-700" />
            <span className="text-xs">Extra-costo &gt; 15%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">👑</span>
            <span className="text-xs">Miglior offerta</span>
          </div>
        </div>

        {/* Insights */}
        <div className="p-4 bg-muted/30 rounded-lg border">
          <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Insights Strategici
          </h4>
          <ul className="text-sm space-y-2 text-muted-foreground">
            <li>
              • <span className="font-semibold text-green-600">{bestImpresa.impresa}</span> è
              l'impresa più competitiva overall con delta medio di{" "}
              <span className="font-semibold">{bestImpresa.deltaMedio.toFixed(1)}%</span> e{" "}
              <span className="font-semibold">{bestImpresa.vittorie} vittorie</span>
            </li>
            {stats.filter((s) => s.vittorie > 0 && s.impresa !== bestImpresa.impresa).length >
              0 && (
              <li>
                • Imprese specializzate per categoria:{" "}
                {stats
                  .filter((s) => s.vittorie > 0 && s.impresa !== bestImpresa.impresa)
                  .map(
                    (s) =>
                      `${s.impresa} (${s.vittorie} ${
                        s.vittorie === 1 ? "vittoria" : "vittorie"
                      })`
                  )
                  .join(", ")}
              </li>
            )}
            <li className="pt-2 border-t">
              • Considera lo <span className="font-semibold">split dei lotti</span> per
              massimizzare i risparmi: assegna ogni categoria all'impresa più competitiva
              (celle verdi con 👑)
            </li>
            <li>
              • Le celle rosse indicano opportunità di{" "}
              <span className="font-semibold">negoziazione</span> o possibili errori di
              stima
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
