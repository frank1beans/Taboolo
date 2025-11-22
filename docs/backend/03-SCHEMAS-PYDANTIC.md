# Schemas Pydantic - Documentazione Completa

## Indice
- [Panoramica](#panoramica)
- [Schemi Commessa e Computo](#schemi-commessa-e-computo)
- [Schemi WBS](#schemi-wbs)
- [Schemi Elenco Prezzi](#schemi-elenco-prezzi)
- [Schemi Analisi](#schemi-analisi)
- [Schemi Confronto Offerte](#schemi-confronto-offerte)
- [Schemi Dashboard](#schemi-dashboard)
- [Schemi Import](#schemi-import)
- [Schemi Settings](#schemi-settings)

## Panoramica

File: [backend/app/schemas.py](../../backend/app/schemas.py) (~455 righe)

Gli schemi Pydantic definiscono i contratti delle API (request/response). Tutti gli schemi utilizzano **Pydantic v2** con il pattern:

```python
from pydantic import BaseModel, ConfigDict

class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Supporta ORM models
    # ... campi
```

### Categorie Schemi

| Categoria | Schemi | Descrizione |
|-----------|--------|-------------|
| **Commessa** | CommessaCreate, CommessaSchema, CommessaDetailSchema | CRUD commesse |
| **Computo** | ComputoSchema | Computi progetto/ritorni |
| **Voce** | VoceSchema, AggregatedVoceSchema | Voci di computo |
| **WBS** | WbsSpazialeSchema, Wbs6NodeSchema, Wbs7NodeSchema, CommessaWbsSchema | Work Breakdown Structure |
| **Elenco Prezzi** | PriceListItemSchema, PriceCatalogSummarySchema | Catalogo prodotti |
| **Analisi** | AnalisiCommessaSchema, AnalisiVoceCriticaSchema, AnalisiWBS6TrendSchema | Statistiche e trend |
| **Confronto** | ConfrontoOfferteSchema, ConfrontoVoceSchema | Confronto progetto vs offerte |
| **Dashboard** | DashboardStatsSchema, DashboardActivitySchema | Statistiche dashboard |
| **Import** | ImportConfigSchema, SixImportReportSchema, WbsImportStatsSchema | Import e configurazioni |
| **Settings** | SettingsUpdate, SettingsRead | Impostazioni globali |

---

## Schemi Commessa e Computo

### CommessaCreate

**Uso:** Request body per creazione commessa (POST `/commesse`)

```python
class CommessaCreate(BaseModel):
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato = CommessaStato.setup
```

#### Esempio Request

```json
{
  "nome": "Nuovo Ospedale Milano",
  "codice": "OSP-MI-2025",
  "descrizione": "Costruzione nuovo polo ospedaliero",
  "business_unit": "Healthcare",
  "revisione": "Rev. 02",
  "stato": "setup"
}
```

---

### CommessaSchema

**Uso:** Response per singola commessa (GET `/commesse/{id}`)

```python
class CommessaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato
    created_at: datetime
    updated_at: datetime
```

#### Esempio Response

```json
{
  "id": 1,
  "nome": "Nuovo Ospedale Milano",
  "codice": "OSP-MI-2025",
  "descrizione": "Costruzione nuovo polo ospedaliero",
  "business_unit": "Healthcare",
  "revisione": "Rev. 02",
  "stato": "in_corso",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:20:00Z"
}
```

---

### CommessaDetailSchema

**Uso:** Response dettagliata con computi inclusi (GET `/commesse/{id}`)

```python
class CommessaDetailSchema(CommessaSchema):
    computi: list[ComputoSchema] = []
```

#### Esempio Response

```json
{
  "id": 1,
  "nome": "Nuovo Ospedale Milano",
  "codice": "OSP-MI-2025",
  "stato": "in_corso",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:20:00Z",
  "computi": [
    {
      "id": 1,
      "nome": "Ospedale Milano - Progetto",
      "tipo": "progetto",
      "importo_totale": 15000000.00,
      "created_at": "2025-01-15T11:00:00Z"
    },
    {
      "id": 2,
      "nome": "Offerta Impresa ABC",
      "tipo": "ritorno",
      "impresa": "Impresa ABC S.p.A.",
      "round_number": 1,
      "importo_totale": 14250000.00,
      "delta_vs_progetto": -750000.00,
      "percentuale_delta": -5.0,
      "created_at": "2025-01-16T09:30:00Z"
    }
  ]
}
```

---

### ComputoSchema

**Uso:** Rappresentazione computo (progetto o ritorno)

```python
class ComputoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: ComputoTipo  # "progetto" | "ritorno"
    impresa: Optional[str] = None
    round_number: Optional[int] = None
    importo_totale: Optional[float] = None
    delta_vs_progetto: Optional[float] = None
    percentuale_delta: Optional[float] = None
    note: Optional[str] = None
    file_nome: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

#### Campi Specifici

| Campo | Tipo | Descrizione | Valido per |
|-------|------|-------------|-----------|
| `tipo` | ComputoTipo | "progetto" o "ritorno" | Tutti |
| `impresa` | str? | Nome impresa | Solo ritorni |
| `round_number` | int? | Numero round gara | Solo ritorni |
| `delta_vs_progetto` | float? | Delta assoluto (€) | Solo ritorni |
| `percentuale_delta` | float? | Delta percentuale (%) | Solo ritorni |

---

### VoceSchema

**Uso:** Singola voce di computo con WBS completa

```python
class VoceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    progressivo: Optional[int] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    ordine: int

    # WBS levels (7 livelli)
    wbs_1_code: Optional[str] = None
    wbs_1_description: Optional[str] = None
    # ... fino a wbs_7_code / wbs_7_description
```

#### Esempio

```json
{
  "id": 1,
  "progressivo": 1,
  "codice": "A001.001",
  "descrizione": "Scavo di sbancamento in terreni di qualsiasi natura",
  "unita_misura": "m³",
  "quantita": 1500.0,
  "prezzo_unitario": 12.50,
  "importo": 18750.00,
  "ordine": 1,
  "wbs_1_code": "P00",
  "wbs_1_description": "Lotto 1 - Edificio Principale",
  "wbs_2_code": "L00",
  "wbs_2_description": "Piano Interrato",
  "wbs_6_code": "A001",
  "wbs_6_description": "Scavi",
  "wbs_7_code": "A001.001",
  "wbs_7_description": "Scavi di sbancamento"
}
```

---

### AggregatedVoceSchema

**Uso:** Voce aggregata con path WBS e totali

```python
class AggregatedVoceSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    quantita_totale: float
    importo_totale: float
    prezzo_unitario: Optional[float] = None
    unita_misura: Optional[str] = None
    wbs_6_code: Optional[str] = None
    wbs_6_description: Optional[str] = None
    wbs_7_code: Optional[str] = None
    wbs_7_description: Optional[str] = None
    wbs_path: list[WbsPathEntrySchema] = []
```

#### WbsPathEntrySchema

```python
class WbsPathEntrySchema(BaseModel):
    level: int
    code: Optional[str] = None
    description: Optional[str] = None
```

#### Esempio

```json
{
  "codice": "A001.001",
  "descrizione": "Scavo di sbancamento",
  "quantita_totale": 1500.0,
  "importo_totale": 18750.00,
  "prezzo_unitario": 12.50,
  "unita_misura": "m³",
  "wbs_6_code": "A001",
  "wbs_6_description": "Scavi",
  "wbs_7_code": "A001.001",
  "wbs_7_description": "Scavi di sbancamento",
  "wbs_path": [
    {"level": 1, "code": "P00", "description": "Edificio Principale"},
    {"level": 2, "code": "L00", "description": "Piano Interrato"},
    {"level": 3, "code": "AO01", "description": "Opere di fondazione"}
  ]
}
```

---

## Schemi WBS

### WbsSpazialeSchema

**Uso:** Nodo spaziale WBS (livelli 1-5)

```python
class WbsSpazialeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    parent_id: Optional[int] = None
    level: int
    code: str
    description: Optional[str] = None
    importo_totale: Optional[float] = None
```

---

### Wbs6NodeSchema

**Uso:** Nodo WBS6 (categoria merceologica A###)

```python
class Wbs6NodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    wbs_spaziale_id: Optional[int] = None
    code: str
    description: str
    label: str  # "{code} - {description}"
```

#### Esempio

```json
{
  "id": 1,
  "commessa_id": 1,
  "wbs_spaziale_id": 5,
  "code": "A001",
  "description": "Scavi",
  "label": "A001 - Scavi"
}
```

---

### Wbs7NodeSchema

**Uso:** Nodo WBS7 (raggruppatore EPU A###.###)

```python
class Wbs7NodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    wbs6_id: int
    code: Optional[str] = None
    description: Optional[str] = None
```

---

### CommessaWbsSchema

**Uso:** Struttura WBS completa per commessa (GET `/commesse/{id}/wbs`)

```python
class CommessaWbsSchema(BaseModel):
    commessa_id: int
    spaziali: list[WbsSpazialeSchema]
    wbs6: list[Wbs6NodeSchema]
    wbs7: list[Wbs7NodeSchema]
```

#### Esempio Response

```json
{
  "commessa_id": 1,
  "spaziali": [
    {"id": 1, "level": 1, "code": "P00", "description": "Edificio Principale"},
    {"id": 2, "level": 2, "code": "L00", "description": "Piano Interrato", "parent_id": 1}
  ],
  "wbs6": [
    {"id": 1, "code": "A001", "description": "Scavi", "label": "A001 - Scavi"}
  ],
  "wbs7": [
    {"id": 1, "wbs6_id": 1, "code": "A001.001", "description": "Scavi di sbancamento"}
  ]
}
```

---

### WbsNodeSchema (Tree Gerarchico)

**Uso:** Nodo WBS ricorsivo per tree view

```python
class WbsNodeSchema(BaseModel):
    level: int
    code: Optional[str] = None
    description: Optional[str] = None
    importo: float
    children: list["WbsNodeSchema"] = []
```

#### Esempio Tree

```json
{
  "level": 1,
  "code": "P00",
  "description": "Edificio Principale",
  "importo": 15000000.00,
  "children": [
    {
      "level": 2,
      "code": "L00",
      "description": "Piano Interrato",
      "importo": 3500000.00,
      "children": [
        {
          "level": 6,
          "code": "A001",
          "description": "Scavi",
          "importo": 150000.00,
          "children": []
        }
      ]
    }
  ]
}
```

---

### ComputoWbsSummary

**Uso:** Sommario WBS per computo (GET `/computi/{id}/wbs`)

```python
class ComputoWbsSummary(BaseModel):
    importo_totale: float
    tree: list[WbsNodeSchema]
    voci: list[AggregatedVoceSchema]
```

#### Esempio

```json
{
  "importo_totale": 15000000.00,
  "tree": [
    {
      "level": 1,
      "code": "P00",
      "description": "Edificio Principale",
      "importo": 15000000.00,
      "children": [...]
    }
  ],
  "voci": [
    {
      "codice": "A001.001",
      "descrizione": "Scavo di sbancamento",
      "quantita_totale": 1500.0,
      "importo_totale": 18750.00,
      "wbs_path": [...]
    }
  ]
}
```

---

### WbsVisibilitySchema

**Uso:** Stato visibilità nodo WBS

```python
class WbsVisibilitySchema(BaseModel):
    level: int
    node_id: int
    code: str
    description: Optional[str] = None
    hidden: bool
```

#### Esempio

```json
{
  "level": 6,
  "node_id": 1,
  "code": "A001",
  "description": "Scavi",
  "hidden": true
}
```

---

### WbsVisibilityUpdateSchema

**Uso:** Request body per aggiornamento visibilità (PUT `/commesse/{id}/wbs/visibility`)

```python
class WbsVisibilityUpdateSchema(BaseModel):
    level: int
    node_id: int
    hidden: bool
```

---

## Schemi Elenco Prezzi

### PriceListItemSchema

**Uso:** Voce elenco prezzi

```python
class PriceListItemSchema(BaseModel):
    id: int
    commessa_id: int
    commessa_nome: str
    commessa_codice: str
    business_unit: Optional[str] = None
    product_id: str
    item_code: str
    item_description: Optional[str] = None
    unit_id: Optional[str] = None
    unit_label: Optional[str] = None
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    wbs7_code: Optional[str] = None
    wbs7_description: Optional[str] = None
    price_lists: Optional[dict[str, float]] = None
    extra_metadata: Optional[dict[str, Any]] = None
    source_file: Optional[str] = None
    preventivo_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

#### Esempio

```json
{
  "id": 1,
  "commessa_id": 1,
  "commessa_nome": "Ospedale Milano",
  "commessa_codice": "OSP-MI-2025",
  "business_unit": "Healthcare",
  "product_id": "PROD_12345",
  "item_code": "A001.001",
  "item_description": "Scavo di sbancamento",
  "unit_id": "m3",
  "unit_label": "m³",
  "wbs6_code": "A001",
  "wbs6_description": "Scavi",
  "price_lists": {
    "BASE": 12.50,
    "ALTO": 15.00,
    "BASSO": 10.00
  },
  "extra_metadata": {
    "embedding": [0.123, 0.456, ...],
    "tags": ["scavo", "movimento terra"]
  },
  "source_file": "preventivo_rev02.six",
  "preventivo_id": "PREV_001",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

---

### PriceListItemSearchResultSchema

**Uso:** Risultato ricerca elenco prezzi (con score)

```python
class PriceListItemSearchResultSchema(PriceListItemSchema):
    score: float
    match_reason: Optional[str] = None
```

#### Esempio

```json
{
  ...tutti i campi di PriceListItemSchema...,
  "score": 0.92,
  "match_reason": "semantic_similarity"
}
```

---

### PriceCatalogSummarySchema

**Uso:** Sommario catalogo multi-commessa

```python
class PriceCatalogSummarySchema(BaseModel):
    total_items: int
    total_commesse: int
    business_units: list[PriceCatalogBusinessUnitSummarySchema]

class PriceCatalogBusinessUnitSummarySchema(BaseModel):
    label: str
    value: Optional[str] = None
    items_count: int
    commesse: list[PriceCatalogCommessaSummarySchema]

class PriceCatalogCommessaSummarySchema(BaseModel):
    commessa_id: int
    commessa_nome: str
    commessa_codice: str
    business_unit: Optional[str] = None
    items_count: int
    last_updated: Optional[datetime] = None
```

#### Esempio

```json
{
  "total_items": 5420,
  "total_commesse": 3,
  "business_units": [
    {
      "label": "Healthcare",
      "value": "Healthcare",
      "items_count": 3200,
      "commesse": [
        {
          "commessa_id": 1,
          "commessa_nome": "Ospedale Milano",
          "commessa_codice": "OSP-MI-2025",
          "business_unit": "Healthcare",
          "items_count": 3200,
          "last_updated": "2025-01-15T12:00:00Z"
        }
      ]
    }
  ]
}
```

---

## Schemi Analisi

### AnalisiCommessaSchema

**Uso:** Analisi completa commessa (GET `/commesse/{id}/analisi`)

```python
class AnalisiCommessaSchema(BaseModel):
    confronto_importi: list[AnalisiConfrontoImportoSchema]
    distribuzione_variazioni: list[AnalisiDistribuzioneItemSchema]
    voci_critiche: list[AnalisiVoceCriticaSchema]
    analisi_per_wbs6: list[AnalisiWBS6TrendSchema]
    rounds: list[AnalisiRoundSchema]
    imprese: list[AnalisiImpresaSchema]
    filtri: AnalisiFiltriSchema
    thresholds: AnalisiThresholdsSchema
```

---

### AnalisiConfrontoImportoSchema

**Uso:** Confronto importi totali progetto vs ritorni

```python
class AnalisiConfrontoImportoSchema(BaseModel):
    nome: str
    tipo: ComputoTipo
    importo: float
    delta_percentuale: Optional[float] = None
    impresa: Optional[str] = None
    round_number: Optional[int] = None
```

#### Esempio

```json
[
  {
    "nome": "Progetto",
    "tipo": "progetto",
    "importo": 15000000.00,
    "delta_percentuale": null
  },
  {
    "nome": "Offerta Impresa ABC - Round 1",
    "tipo": "ritorno",
    "importo": 14250000.00,
    "delta_percentuale": -5.0,
    "impresa": "Impresa ABC S.p.A.",
    "round_number": 1
  }
]
```

---

### AnalisiDistribuzioneItemSchema

**Uso:** Istogramma distribuzione criticità

```python
class AnalisiDistribuzioneItemSchema(BaseModel):
    nome: str
    valore: int
    colore: str
```

#### Esempio

```json
[
  {"nome": "Criticità Alta", "valore": 15, "colore": "#dc2626"},
  {"nome": "Criticità Media", "valore": 42, "colore": "#f59e0b"},
  {"nome": "Criticità Bassa", "valore": 120, "colore": "#10b981"}
]
```

---

### AnalisiVoceCriticaSchema

**Uso:** Voce con variazioni significative

```python
class AnalisiVoceCriticaSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    progetto: float
    imprese: dict[str, float]
    delta: float  # Delta percentuale
    criticita: str  # "alta" | "media" | "bassa"
    delta_assoluto: float
    media_prezzo_unitario: Optional[float] = None
    media_importo_totale: Optional[float] = None
    min_offerta: Optional[float] = None
    max_offerta: Optional[float] = None
    impresa_min: Optional[str] = None
    impresa_max: Optional[str] = None
    deviazione_standard: Optional[float] = None
    direzione: str  # "rialzo" | "ribasso" | "neutrale"
```

#### Esempio

```json
{
  "codice": "A001.001",
  "descrizione": "Scavo di sbancamento",
  "descrizione_estesa": "Scavo di sbancamento in terreni di qualsiasi natura",
  "progetto": 18750.00,
  "imprese": {
    "Impresa ABC": 12500.00,
    "Impresa XYZ": 15000.00
  },
  "delta": -30.0,
  "criticita": "alta",
  "delta_assoluto": -5625.00,
  "media_prezzo_unitario": 11.67,
  "media_importo_totale": 13750.00,
  "min_offerta": 12500.00,
  "max_offerta": 15000.00,
  "impresa_min": "Impresa ABC",
  "impresa_max": "Impresa XYZ",
  "deviazione_standard": 1250.00,
  "direzione": "ribasso"
}
```

---

### AnalisiWBS6TrendSchema

**Uso:** Analisi trend per categoria WBS6

```python
class AnalisiWBS6TrendSchema(BaseModel):
    wbs6_id: str
    wbs6_label: str
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    progetto: float
    media_ritorni: float
    delta_percentuale: float
    delta_assoluto: float
    conteggi_criticita: AnalisiWBS6CriticitaSchema
    offerte_considerate: int
    offerte_totali: int
    voci: list[AnalisiWBS6VoceSchema]

class AnalisiWBS6CriticitaSchema(BaseModel):
    alta: int = 0
    media: int = 0
    bassa: int = 0

class AnalisiWBS6VoceSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario_progetto: Optional[float] = None
    importo_totale_progetto: Optional[float] = None
    media_prezzo_unitario: Optional[float] = None
    media_importo_totale: Optional[float] = None
    delta_percentuale: Optional[float] = None
    delta_assoluto: Optional[float] = None
    offerte_considerate: int = 0
    importo_minimo: Optional[float] = None
    importo_massimo: Optional[float] = None
    impresa_min: Optional[str] = None
    impresa_max: Optional[str] = None
    deviazione_standard: Optional[float] = None
    criticita: Optional[str] = None
```

#### Esempio

```json
{
  "wbs6_id": "1",
  "wbs6_label": "A001 - Scavi",
  "wbs6_code": "A001",
  "wbs6_description": "Scavi",
  "progetto": 450000.00,
  "media_ritorni": 380000.00,
  "delta_percentuale": -15.56,
  "delta_assoluto": -70000.00,
  "conteggi_criticita": {
    "alta": 3,
    "media": 7,
    "bassa": 12
  },
  "offerte_considerate": 2,
  "offerte_totali": 2,
  "voci": [
    {
      "codice": "A001.001",
      "descrizione": "Scavo di sbancamento",
      "quantita": 1500.0,
      "prezzo_unitario_progetto": 12.50,
      "importo_totale_progetto": 18750.00,
      "media_prezzo_unitario": 10.00,
      "media_importo_totale": 15000.00,
      "delta_percentuale": -20.0,
      "criticita": "media"
    }
  ]
}
```

---

### AnalisiRoundSchema, AnalisiImpresaSchema

**Uso:** Metadati round e imprese

```python
class AnalisiRoundSchema(BaseModel):
    numero: int
    label: str
    imprese: list[str]
    imprese_count: int

class AnalisiImpresaSchema(BaseModel):
    computo_id: int
    nome: str
    impresa: Optional[str] = None
    etichetta: Optional[str] = None
    round_number: Optional[int] = None
    round_label: Optional[str] = None
```

---

### AnalisiFiltriSchema, AnalisiThresholdsSchema

**Uso:** Informazioni su filtri applicati e soglie

```python
class AnalisiFiltriSchema(BaseModel):
    round_number: Optional[int] = None
    impresa: Optional[str] = None
    impresa_normalizzata: Optional[str] = None
    offerte_totali: int
    offerte_considerate: int
    imprese_attive: list[str]

class AnalisiThresholdsSchema(BaseModel):
    media_percent: float
    alta_percent: float
```

---

## Schemi Confronto Offerte

### ConfrontoOfferteSchema

**Uso:** Confronto dettagliato progetto vs offerte (GET `/commesse/{id}/confronto-offerte`)

```python
class ConfrontoOfferteSchema(BaseModel):
    voci: list[ConfrontoVoceSchema]
    imprese: list[ConfrontoImpresaSchema]
    rounds: list[ConfrontoRoundSchema]
```

---

### ConfrontoVoceSchema

**Uso:** Voce con tutte le offerte a confronto

```python
class ConfrontoVoceSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario_progetto: Optional[float] = None
    importo_totale_progetto: Optional[float] = None
    offerte: dict[str, ConfrontoVoceOffertaSchema]
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    wbs7_code: Optional[str] = None
    wbs7_description: Optional[str] = None

class ConfrontoVoceOffertaSchema(BaseModel):
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo_totale: Optional[float] = None
    note: Optional[str] = None
    criticita: Optional[str] = None
```

#### Esempio

```json
{
  "codice": "A001.001",
  "descrizione": "Scavo di sbancamento",
  "unita_misura": "m³",
  "quantita": 1500.0,
  "prezzo_unitario_progetto": 12.50,
  "importo_totale_progetto": 18750.00,
  "offerte": {
    "Impresa ABC - Round 1": {
      "quantita": 1500.0,
      "prezzo_unitario": 10.00,
      "importo_totale": 15000.00,
      "criticita": "media"
    },
    "Impresa XYZ - Round 1": {
      "quantita": 1500.0,
      "prezzo_unitario": 11.00,
      "importo_totale": 16500.00,
      "criticita": "bassa"
    }
  },
  "wbs6_code": "A001",
  "wbs6_description": "Scavi"
}
```

---

### ConfrontoImpresaSchema, ConfrontoRoundSchema

**Uso:** Metadati imprese e round

```python
class ConfrontoImpresaSchema(BaseModel):
    nome: str
    computo_id: int
    impresa: Optional[str] = None
    round_number: Optional[int] = None
    etichetta: Optional[str] = None
    round_label: Optional[str] = None

class ConfrontoRoundSchema(BaseModel):
    numero: int
    label: str
    imprese: list[str]
    imprese_count: int
```

---

## Schemi Dashboard

### DashboardStatsSchema

**Uso:** Statistiche dashboard (GET `/dashboard/stats`)

```python
class DashboardStatsSchema(BaseModel):
    commesse_attive: int
    computi_caricati: int
    ritorni: int
    report_generati: int
    attivita_recente: list[DashboardActivitySchema]

class DashboardActivitySchema(BaseModel):
    computo_id: int
    computo_nome: str
    tipo: ComputoTipo
    commessa_id: int
    commessa_codice: str
    commessa_nome: str
    created_at: datetime
```

#### Esempio

```json
{
  "commesse_attive": 5,
  "computi_caricati": 18,
  "ritorni": 12,
  "report_generati": 25,
  "attivita_recente": [
    {
      "computo_id": 15,
      "computo_nome": "Offerta Impresa ABC - Round 2",
      "tipo": "ritorno",
      "commessa_id": 1,
      "commessa_codice": "OSP-MI-2025",
      "commessa_nome": "Ospedale Milano",
      "created_at": "2025-01-16T14:30:00Z"
    }
  ]
}
```

---

## Schemi Import

### ImportConfigCreateSchema

**Uso:** Request body creazione config import (POST `/import-configs`)

```python
class ImportConfigCreateSchema(BaseModel):
    nome: str
    impresa: str | None = None
    sheet_name: str | None = None
    code_columns: str | None = None
    description_columns: str | None = None
    price_column: str | None = None
    quantity_column: str | None = None
    note: str | None = None
```

---

### ImportConfigSchema

**Uso:** Response config import (GET `/import-configs/{id}`)

```python
class ImportConfigSchema(ImportConfigCreateSchema):
    id: int
    commessa_id: int | None
    created_at: datetime
    updated_at: datetime
```

---

### SixImportReportSchema

**Uso:** Report import STR Vision (POST `/commesse/{id}/six/import`)

```python
class SixImportReportSchema(BaseModel):
    commessa_id: int
    wbs_spaziali: int
    wbs6: int
    wbs7: int
    voci: int
    importo_totale: float
```

#### Esempio

```json
{
  "commessa_id": 1,
  "wbs_spaziali": 45,
  "wbs6": 120,
  "wbs7": 380,
  "voci": 2450,
  "importo_totale": 15000000.00
}
```

---

### SixPreventiviPreviewSchema

**Uso:** Preview preventivi disponibili in file STR Vision

```python
class SixPreventiviPreviewSchema(BaseModel):
    preventivi: list[SixPreventivoOptionSchema]

class SixPreventivoOptionSchema(BaseModel):
    internal_id: str
    code: Optional[str] = None
    description: Optional[str] = None
```

#### Esempio

```json
{
  "preventivi": [
    {
      "internal_id": "PREV_001",
      "code": "PREV-A",
      "description": "Preventivo Base"
    },
    {
      "internal_id": "PREV_002",
      "code": "PREV-B",
      "description": "Preventivo Alternativo"
    }
  ]
}
```

---

### SixInspectionSchema

**Uso:** Ispezione completa contenuto file STR Vision (.six/.xml) senza import.

```python
class SixInspectionPriceListSchema(BaseModel):
    canonical_id: str
    label: str
    aliases: list[str] = []
    priority: int = 0
    products: int = 0
    rilevazioni: int = 0

class SixInspectionGroupSchema(BaseModel):
    grp_id: str
    code: str
    description: Optional[str] = None
    level: Optional[int] = None

class SixPreventivoInspectSchema(BaseModel):
    internal_id: str
    code: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None
    price_list_id: Optional[str] = None
    rilevazioni: int = 0
    items: int = 0

class SixInspectionSchema(BaseModel):
    preventivi: list[SixPreventivoInspectSchema]
    price_lists: list[SixInspectionPriceListSchema]
    wbs_spaziali: list[SixInspectionGroupSchema]
    wbs6: list[SixInspectionGroupSchema]
    wbs7: list[SixInspectionGroupSchema]
    products_total: int
```

#### Esempio

```json
{
  "preventivi": [
    {
      "internal_id": "10",
      "code": "CME001",
      "description": "Preventivo base",
      "price_list_id": "1",
      "rilevazioni": 120,
      "items": 80
    }
  ],
  "price_lists": [
    {
      "canonical_id": "prezzi_base",
      "label": "Prezzi Base",
      "aliases": ["L1", "L100"],
      "priority": 2,
      "products": 200,
      "rilevazioni": 150
    }
  ],
  "wbs_spaziali": [
    { "grp_id": "w1", "code": "A", "description": "Edificio A", "level": 1 }
  ],
  "wbs6": [
    { "grp_id": "w6", "code": "A001", "description": "Opere civili", "level": 6 }
  ],
  "wbs7": [
    { "grp_id": "w7", "code": "A001.010", "description": "Scavi", "level": 7 }
  ],
  "products_total": 450
}
```

---

### WbsImportStatsSchema

**Uso:** Statistiche import WBS da Excel (POST `/commesse/{id}/wbs/import`)

```python
class WbsImportStatsSchema(BaseModel):
    rows_total: int
    spaziali_inserted: int
    spaziali_updated: int
    wbs6_inserted: int
    wbs6_updated: int
    wbs7_inserted: int
    wbs7_updated: int
```

#### Esempio

```json
{
  "rows_total": 150,
  "spaziali_inserted": 30,
  "spaziali_updated": 5,
  "wbs6_inserted": 80,
  "wbs6_updated": 10,
  "wbs7_inserted": 120,
  "wbs7_updated": 15
}
```

---

## Schemi Settings

### SettingsUpdate

**Uso:** Request body aggiornamento settings (PUT `/settings`)

```python
class SettingsUpdate(BaseModel):
    delta_minimo_critico: Optional[float] = None
    delta_massimo_critico: Optional[float] = None
    percentuale_cme_alto: Optional[float] = None
    percentuale_cme_basso: Optional[float] = None
```

---

### SettingsRead

**Uso:** Response settings (GET `/settings`)

```python
class SettingsRead(SettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

class SettingsBase(SQLModel):
    delta_minimo_critico: float = -30000.0
    delta_massimo_critico: float = 1000.0
    percentuale_cme_alto: float = 25.0
    percentuale_cme_basso: float = 50.0
    criticita_media_percent: float = 25.0
    criticita_alta_percent: float = 50.0
```

---

## Pattern Comuni

### 1. from_attributes per ORM

```python
class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # Permette conversione diretta da SQLModel objects
```

Uso:
```python
commessa = session.get(Commessa, 1)
schema = CommessaSchema.model_validate(commessa)  # Converte automaticamente
```

---

### 2. Nested Schemas

```python
class CommessaDetailSchema(CommessaSchema):
    computi: list[ComputoSchema] = []
```

---

### 3. Optional Fields

```python
impresa: Optional[str] = None  # Campo opzionale (null in JSON)
```

---

### 4. Enumerazioni

```python
from app.db.models import ComputoTipo, CommessaStato

tipo: ComputoTipo  # "progetto" | "ritorno"
stato: CommessaStato  # "setup" | "in_corso" | "chiusa"
```

---

## Prossimi Passi

- [API Routes](./04-API-ROUTES.md) - Endpoint HTTP dettagliati
- [Services](./05-SERVICES.md) - Business logic
- [Parser Excel](./06-PARSER-EXCEL.md) - Parsing computi
