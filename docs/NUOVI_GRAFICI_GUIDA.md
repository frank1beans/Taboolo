# 📊 Guida Integrazione Nuovi Grafici Analisi

## 🎯 Grafici Implementati

Sono stati creati **3 nuovi grafici avanzati** per la sezione Analisi:

### 1. **TrendEvoluzioneRound** - Evoluzione Prezzi tra Round
📁 `src/components/charts/TrendEvoluzioneRound.tsx`

**Cosa mostra:**
- Linee temporali che mostrano l'andamento delle offerte di ogni impresa
- Come cambiano i prezzi tra un round e l'altro
- Chi migliora l'offerta, chi rimane stabile, chi aumenta

**Dati richiesti:**
```typescript
interface TrendEvoluzioneData {
  impresa: string;
  color: string;
  offerte: {
    round: number;
    roundLabel?: string;
    importo: number;
    delta?: number; // Delta rispetto round precedente
  }[];
}
```

**Output insights:**
- ✅ Imprese in miglioramento (opportunità negoziazione)
- ⚠️ Imprese con aumenti (da verificare)
- ⏸️ Imprese stabili
- 🏆 Migliore negoziatore

---

### 2. **WaterfallComposizioneDelta** - Composizione Delta
📁 `src/components/charts/WaterfallComposizioneDelta.tsx`

**Cosa mostra:**
- Scomposizione del delta totale categoria per categoria
- Visualizzazione "a cascata" dal progetto all'offerta migliore
- Dove si concentrano risparmi ed extra-costi

**Dati richiesti:**
```typescript
interface WaterfallData {
  categoria: string;
  importoProgetto: number;
  importoOfferta: number;
  delta: number; // Assoluto
  deltaPercentuale: number;
}

// + totali
importoProgettoTotale: number;
importoOffertaTotale: number;
```

**Output insights:**
- 💚 Top 3 categorie con maggior risparmio
- 🔴 Top 3 categorie con maggior extra-costo
- 📊 Percentuale del delta da risparmi vs extra-costi
- 🎯 Suggerimenti su dove negoziare

---

### 3. **HeatmapCompetitivita** - Heatmap Competitività
📁 `src/components/charts/HeatmapCompetitivita.tsx`

**Cosa mostra:**
- Matrice categorie × imprese
- Colori: Verde = competitiva, Rosso = cara
- 👑 Corona sulla migliore offerta per categoria

**Dati richiesti:**
```typescript
interface HeatmapData {
  categorie: {
    categoria: string;
    importoProgetto: number;
  }[];
  imprese: {
    impresa: string;
    categorie: {
      categoria: string;
      importoOfferta: number;
      delta: number; // % vs progetto
    }[];
  }[];
}
```

**Output insights:**
- 🏆 Impresa più competitiva overall
- 🎖️ Specializzazioni per categoria
- 💡 Suggerimenti per split lotti
- ⚠️ Opportunità di negoziazione

---

## 🚀 Come Integrare

### Opzione A: Integrazione Base (con dati attuali)

Usa i dati già disponibili da `useAnalisiData`:

```tsx
import { GraficiAnalisi } from "@/components/GraficiAnalisi";
import { WaterfallComposizioneDelta } from "@/components/charts/WaterfallComposizioneDelta";
import { prepareWaterfallData } from "@/lib/grafici-utils";

function CommessaAnalysisPage() {
  const { data } = useAnalisiData(commessaId);

  // Prepara dati Waterfall
  const waterfallData = prepareWaterfallData(
    data?.analisiPerWbs6 || [],
    data?.importoProgettoTotale || 0,
    data?.importoOffertaTotale || 0
  );

  return (
    <div className="space-y-8">
      {/* Grafici esistenti */}
      <GraficiAnalisi commessaId={commessaId} />

      {/* Nuovo: Waterfall */}
      <WaterfallComposizioneDelta {...waterfallData} />
    </div>
  );
}
```

---

### Opzione B: Integrazione Completa (estendere API)

Per avere **tutti e 3 i grafici** con dati reali, serve estendere l'API backend:

#### 1. Endpoint per Trend Evoluzione

**Nuovo endpoint:**
```python
@router.get("/api/analisi/{commessa_id}/trend-round")
async def get_trend_round(commessa_id: str):
    """
    Ritorna le offerte di ogni impresa per ogni round
    """
    # Query esempio (PostgreSQL)
    query = """
    SELECT
        o.impresa_normalizzata as impresa,
        o.round_numero as round,
        r.nome as round_label,
        SUM(vo.prezzo_totale) as importo_totale
    FROM offerte o
    JOIN voci_offerta vo ON o.id = vo.offerta_id
    LEFT JOIN rounds r ON o.round_numero = r.numero
    WHERE o.commessa_id = :commessa_id
    GROUP BY o.impresa_normalizzata, o.round_numero, r.nome
    ORDER BY o.round_numero, o.impresa_normalizzata
    """

    results = await db.execute(query, {"commessa_id": commessa_id})

    # Organizza per impresa
    imprese_map = {}
    for row in results:
        if row.impresa not in imprese_map:
            imprese_map[row.impresa] = []
        imprese_map[row.impresa].append({
            "round": row.round,
            "roundLabel": row.round_label,
            "importo": row.importo_totale
        })

    # Calcola delta tra round
    for impresa, offerte in imprese_map.items():
        for i, offerta in enumerate(offerte):
            if i > 0:
                prev = offerte[i-1]["importo"]
                curr = offerta["importo"]
                offerta["delta"] = ((curr - prev) / prev) * 100
            else:
                offerta["delta"] = 0

    return [
        {
            "impresa": impresa,
            "color": get_impresa_color(impresa),  # Helper function
            "offerte": offerte
        }
        for impresa, offerte in imprese_map.items()
    ]
```

#### 2. Endpoint per Heatmap

**Nuovo endpoint:**
```python
@router.get("/api/analisi/{commessa_id}/heatmap-competitivita")
async def get_heatmap_competitivita(commessa_id: str):
    """
    Ritorna dati per heatmap: imprese × categorie WBS6
    """
    query = """
    SELECT
        o.impresa_normalizzata as impresa,
        wbs.codice as wbs6_code,
        wbs.descrizione as wbs6_label,
        SUM(vp.prezzo_totale) as importo_progetto,
        AVG(vo.prezzo_unitario) as prezzo_medio_offerta,
        SUM(vo.prezzo_totale) as importo_offerta
    FROM offerte o
    JOIN voci_offerta vo ON o.id = vo.offerta_id
    JOIN voci_progetto vp ON vo.voce_progetto_id = vp.id
    JOIN wbs_6 wbs ON vp.wbs6_id = wbs.id
    WHERE o.commessa_id = :commessa_id
      AND o.round_numero = (
        SELECT MAX(round_numero)
        FROM offerte
        WHERE commessa_id = :commessa_id
      )
    GROUP BY o.impresa_normalizzata, wbs.codice, wbs.descrizione
    """

    results = await db.execute(query, {"commessa_id": commessa_id})

    # Organizza i dati
    categorie_map = {}
    imprese_map = {}

    for row in results:
        # Raccogli categorie
        if row.wbs6_code not in categorie_map:
            categorie_map[row.wbs6_code] = {
                "categoria": row.wbs6_label,
                "importoProgetto": 0
            }
        categorie_map[row.wbs6_code]["importoProgetto"] += row.importo_progetto

        # Raccogli offerte per impresa
        if row.impresa not in imprese_map:
            imprese_map[row.impresa] = []

        delta = ((row.importo_offerta - row.importo_progetto) /
                 row.importo_progetto * 100)

        imprese_map[row.impresa].append({
            "categoria": row.wbs6_label,
            "importoOfferta": row.importo_offerta,
            "delta": delta
        })

    return {
        "categorie": list(categorie_map.values()),
        "imprese": [
            {"impresa": imp, "categorie": cats}
            for imp, cats in imprese_map.items()
        ]
    }
```

#### 3. Hook React per nuovi endpoint

```typescript
// src/hooks/useGraficiAvanzati.ts
import { useQuery } from "@tanstack/react-query";

export function useTrendRound(commessaId: string) {
  return useQuery({
    queryKey: ["trend-round", commessaId],
    queryFn: async () => {
      const res = await fetch(`/api/analisi/${commessaId}/trend-round`);
      if (!res.ok) throw new Error("Errore caricamento trend");
      return res.json();
    },
    enabled: !!commessaId,
  });
}

export function useHeatmapCompetitivita(commessaId: string) {
  return useQuery({
    queryKey: ["heatmap-competitivita", commessaId],
    queryFn: async () => {
      const res = await fetch(
        `/api/analisi/${commessaId}/heatmap-competitivita`
      );
      if (!res.ok) throw new Error("Errore caricamento heatmap");
      return res.json();
    },
    enabled: !!commessaId,
  });
}
```

#### 4. Uso completo

```tsx
import { TrendEvoluzioneRound } from "@/components/charts/TrendEvoluzioneRound";
import { WaterfallComposizioneDelta } from "@/components/charts/WaterfallComposizioneDelta";
import { HeatmapCompetitivita } from "@/components/charts/HeatmapCompetitivita";
import { useTrendRound, useHeatmapCompetitivita } from "@/hooks/useGraficiAvanzati";
import { prepareWaterfallData } from "@/lib/grafici-utils";

function GraficiAnalisiCompleta({ commessaId }: { commessaId: string }) {
  const { data: analisiBase } = useAnalisiData(commessaId);
  const { data: trendData } = useTrendRound(commessaId);
  const { data: heatmapData } = useHeatmapCompetitivita(commessaId);

  // Prepara waterfall da dati esistenti
  const waterfallData = prepareWaterfallData(
    analisiBase?.analisiPerWbs6 || [],
    analisiBase?.importoProgettoTotale || 0,
    analisiBase?.importoOffertaTotale || 0
  );

  return (
    <div className="space-y-8">
      {/* 1. Trend Evoluzione */}
      {trendData && <TrendEvoluzioneRound data={trendData} />}

      {/* 2. Waterfall Delta */}
      <WaterfallComposizioneDelta {...waterfallData} />

      {/* 3. Heatmap Competitività */}
      {heatmapData && <HeatmapCompetitivita {...heatmapData} />}

      {/* Grafici esistenti */}
      <GraficiAnalisi commessaId={commessaId} />
    </div>
  );
}
```

---

### Opzione C: Testing con Mock Data

Per testare subito i grafici senza modificare il backend:

```tsx
import { TrendEvoluzioneRound } from "@/components/charts/TrendEvoluzioneRound";
import { generateMockTrendData } from "@/lib/grafici-utils";

function TestGrafici() {
  // Genera dati di esempio
  const mockTrendData = generateMockTrendData(
    ["Impresa A", "Impresa B", "Impresa C"],
    3 // numero di round
  );

  const mockHeatmapData = {
    categorie: [
      { categoria: "Scavi", importoProgetto: 120000 },
      { categoria: "Murature", importoProgetto: 350000 },
      { categoria: "Impianti", importoProgetto: 280000 },
    ],
    imprese: [
      {
        impresa: "Impresa A",
        categorie: [
          { categoria: "Scavi", importoOfferta: 110000, delta: -8.3 },
          { categoria: "Murature", importoOfferta: 380000, delta: 8.6 },
          { categoria: "Impianti", importoOfferta: 260000, delta: -7.1 },
        ],
      },
      {
        impresa: "Impresa B",
        categorie: [
          { categoria: "Scavi", importoOfferta: 125000, delta: 4.2 },
          { categoria: "Murature", importoOfferta: 340000, delta: -2.9 },
          { categoria: "Impianti", importoOfferta: 275000, delta: -1.8 },
        ],
      },
    ],
  };

  return (
    <div className="space-y-8 p-8">
      <TrendEvoluzioneRound data={mockTrendData} />
      <HeatmapCompetitivita {...mockHeatmapData} />
    </div>
  );
}
```

---

## 📋 Checklist Integrazione

### Fase 1: Testing Immediato ✅
- [ ] Copia i 3 componenti in `src/components/charts/`
- [ ] Copia `grafici-utils.ts` in `src/lib/`
- [ ] Testa con mock data usando Opzione C
- [ ] Verifica responsive e dark mode
- [ ] Testa tooltip e interazioni

### Fase 2: Integrazione Base ✅
- [ ] Integra Waterfall con dati esistenti (Opzione A)
- [ ] Aggiungi alla pagina CommessaAnalysisPage
- [ ] Verifica che funzioni con dati reali

### Fase 3: Estensione Backend 🔄
- [ ] Implementa endpoint `/trend-round`
- [ ] Implementa endpoint `/heatmap-competitivita`
- [ ] Crea hooks React per i nuovi endpoint
- [ ] Testa con dati reali
- [ ] Integra tutti e 3 i grafici (Opzione B)

### Fase 4: Refinement 🎨
- [ ] Aggiungi filtri (round, impresa, categoria)
- [ ] Implementa export grafici in PNG/PDF
- [ ] Ottimizza performance per dataset grandi
- [ ] Aggiungi animazioni di transizione
- [ ] Documenta per il team

---

## 🎯 Benefici Attesi

Con questi grafici, gli utenti potranno:

### Trend Evoluzione
- ✅ Vedere immediatamente chi migliora l'offerta
- ✅ Identificare comportamenti anomali
- ✅ Decidere con chi negoziare ancora

### Waterfall Delta
- ✅ Capire dove si concentrano i risparmi/extra-costi
- ✅ Presentare in modo chiaro agli stakeholder
- ✅ Focalizzare le negoziazioni sulle categorie giuste

### Heatmap
- ✅ Identificare specializzazioni delle imprese
- ✅ Decidere se fare split lotti
- ✅ Individuare opportunità di negoziazione

---

## 📞 Supporto

**Domande?**
1. Consulta gli esempi in `COMPONENT_EXAMPLES.md`
2. Vedi i tipi TypeScript nei file componenti
3. Testa con mock data prima di integrare

**Pronto per partire!** 🚀

Inizia con l'**Opzione C** (mock data) per vedere subito i grafici in azione, poi procedi con l'**Opzione A** (Waterfall) e infine l'**Opzione B** (completa) quando il backend sarà pronto.
