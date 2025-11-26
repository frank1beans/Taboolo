import { TrendEvoluzioneRound } from "@/components/charts/TrendEvoluzioneRound";
import { WaterfallComposizioneDelta } from "@/components/charts/WaterfallComposizioneDelta";
import { HeatmapCompetitivita } from "@/components/charts/HeatmapCompetitivita";

export default function TestGrafici() {
  // Dati mock per Trend Evoluzione
  const mockTrendData = [
    {
      impresa: "Impresa Alpha",
      color: "hsl(217 91% 60%)",
      offerte: [
        { round: 1, roundLabel: "Round 1", importo: 1200000, delta: 0 },
        { round: 2, roundLabel: "Round 2", importo: 1150000, delta: -4.2 },
        { round: 3, roundLabel: "Round 3", importo: 1080000, delta: -6.1 },
      ],
      deltaComplessivo: -10.0,
    },
    {
      impresa: "Impresa Beta",
      color: "hsl(142 71% 45%)",
      offerte: [
        { round: 1, roundLabel: "Round 1", importo: 1250000, delta: 0 },
        { round: 2, roundLabel: "Round 2", importo: 1220000, delta: -2.4 },
        { round: 3, roundLabel: "Round 3", importo: 1200000, delta: -1.6 },
      ],
      deltaComplessivo: -4.0,
    },
    {
      impresa: "Impresa Gamma",
      color: "hsl(38 92% 55%)",
      offerte: [
        { round: 1, roundLabel: "Round 1", importo: 1180000, delta: 0 },
        { round: 2, roundLabel: "Round 2", importo: 1170000, delta: -0.8 },
        { round: 3, roundLabel: "Round 3", importo: 1165000, delta: -0.4 },
      ],
      deltaComplessivo: -1.3,
    },
  ];

  // Dati mock per Waterfall
  const mockWaterfallData = {
    data: [
      {
        categoria: "Scavi e Movimento Terra",
        importoProgetto: 180000,
        importoOfferta: 165000,
        delta: -15000,
        deltaPercentuale: -8.3,
      },
      {
        categoria: "Opere in C.A.",
        importoProgetto: 420000,
        importoOfferta: 445000,
        delta: 25000,
        deltaPercentuale: 6.0,
      },
      {
        categoria: "Murature e Tramezzi",
        importoProgetto: 280000,
        importoOfferta: 270000,
        delta: -10000,
        deltaPercentuale: -3.6,
      },
      {
        categoria: "Impianti Elettrici",
        importoProgetto: 320000,
        importoOfferta: 285000,
        delta: -35000,
        deltaPercentuale: -10.9,
      },
      {
        categoria: "Impianti Idraulici",
        importoProgetto: 250000,
        importoOfferta: 240000,
        delta: -10000,
        deltaPercentuale: -4.0,
      },
      {
        categoria: "Finiture e Pavimenti",
        importoProgetto: 380000,
        importoOfferta: 350000,
        delta: -30000,
        deltaPercentuale: -7.9,
      },
      {
        categoria: "Serramenti",
        importoProgetto: 170000,
        importoOfferta: 190000,
        delta: 20000,
        deltaPercentuale: 11.8,
      },
    ],
    importoProgettoTotale: 2000000,
    importoOffertaTotale: 1945000,
  };

  // Dati mock per Heatmap
  const mockHeatmapData = {
    categorie: [
      { categoria: "Scavi e Movimento Terra", importoProgetto: 180000 },
      { categoria: "Opere in C.A.", importoProgetto: 420000 },
      { categoria: "Murature e Tramezzi", importoProgetto: 280000 },
      { categoria: "Impianti Elettrici", importoProgetto: 320000 },
      { categoria: "Impianti Idraulici", importoProgetto: 250000 },
      { categoria: "Finiture e Pavimenti", importoProgetto: 380000 },
    ],
    imprese: [
      {
        impresa: "Impresa Alpha",
        categorie: [
          { categoria: "Scavi e Movimento Terra", importoOfferta: 165000, delta: -8.3 },
          { categoria: "Opere in C.A.", importoOfferta: 445000, delta: 6.0 },
          { categoria: "Murature e Tramezzi", importoOfferta: 270000, delta: -3.6 },
          { categoria: "Impianti Elettrici", importoOfferta: 285000, delta: -10.9 },
          { categoria: "Impianti Idraulici", importoOfferta: 240000, delta: -4.0 },
          { categoria: "Finiture e Pavimenti", importoOfferta: 350000, delta: -7.9 },
        ],
      },
      {
        impresa: "Impresa Beta",
        categorie: [
          { categoria: "Scavi e Movimento Terra", importoOfferta: 175000, delta: -2.8 },
          { categoria: "Opere in C.A.", importoOfferta: 410000, delta: -2.4 },
          { categoria: "Murature e Tramezzi", importoOfferta: 265000, delta: -5.4 },
          { categoria: "Impianti Elettrici", importoOfferta: 305000, delta: -4.7 },
          { categoria: "Impianti Idraulici", importoOfferta: 245000, delta: -2.0 },
          { categoria: "Finiture e Pavimenti", importoOfferta: 365000, delta: -3.9 },
        ],
      },
      {
        impresa: "Impresa Gamma",
        categorie: [
          { categoria: "Scavi e Movimento Terra", importoOfferta: 170000, delta: -5.6 },
          { categoria: "Opere in C.A.", importoOfferta: 430000, delta: 2.4 },
          { categoria: "Murature e Tramezzi", importoOfferta: 275000, delta: -1.8 },
          { categoria: "Impianti Elettrici", importoOfferta: 295000, delta: -7.8 },
          { categoria: "Impianti Idraulici", importoOfferta: 235000, delta: -6.0 },
          { categoria: "Finiture e Pavimenti", importoOfferta: 360000, delta: -5.3 },
        ],
      },
    ],
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Test Nuovi Grafici Analisi</h1>
          <p className="text-lg text-muted-foreground">
            Anteprima dei 3 nuovi grafici con dati di esempio
          </p>
        </div>

        {/* Trend Evoluzione Round */}
        <TrendEvoluzioneRound data={mockTrendData} />

        {/* Waterfall Composizione Delta */}
        <WaterfallComposizioneDelta {...mockWaterfallData} />

        {/* Heatmap Competitività */}
        <HeatmapCompetitivita {...mockHeatmapData} />

        {/* Footer */}
        <div className="p-6 bg-muted/30 rounded-lg border">
          <h3 className="font-semibold mb-2">✅ Test Completato</h3>
          <p className="text-sm text-muted-foreground">
            Se vedi tutti e 3 i grafici sopra, l'integrazione è riuscita! Ora puoi integrarli
            con i dati reali nella pagina Analisi.
          </p>
        </div>
      </div>
    </div>
  );
}
