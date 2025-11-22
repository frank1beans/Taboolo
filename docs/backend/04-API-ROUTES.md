# API Routes - Documentazione Completa

## Indice
- [Panoramica](#panoramica)
- [Base URL e Versioning](#base-url-e-versioning)
- [Autenticazione](#autenticazione)
- [Endpoint Commesse](#endpoint-commesse)
- [Endpoint Computi](#endpoint-computi)
- [Endpoint Dashboard](#endpoint-dashboard)
- [Endpoint Settings](#endpoint-settings)
- [Endpoint Import Configs](#endpoint-import-configs)
- [Gestione Errori](#gestione-errori)
- [Rate Limiting e Throttling](#rate-limiting-e-throttling)

## Panoramica

Il backend espone API REST tramite FastAPI con routing modulare organizzato per dominio.

### Routers Disponibili

File: [api/__init__.py](../../backend/app/api/__init__.py)

| Router | Prefix | File | Descrizione |
|--------|--------|------|-------------|
| **Commesse** | `/api/v1/commesse` | [commesse.py](../../backend/app/api/routes/commesse.py) | CRUD commesse, upload, analisi, WBS |
| **Computi** | `/api/v1/computi` | [computi.py](../../backend/app/api/routes/computi.py) | Operazioni su computi |
| **Dashboard** | `/api/v1/dashboard` | [dashboard.py](../../backend/app/api/routes/dashboard.py) | Statistiche e attività |
| **Settings** | `/api/v1/settings` | [settings.py](../../backend/app/api/routes/settings.py) | Impostazioni globali |
| **Import Configs** | `/api/v1/import-configs` | [import_configs.py](../../backend/app/api/routes/import_configs.py) | Template import |

### Convenzioni

- **Base URL**: `http://localhost:8000/api/v1`
- **Formato richieste**: `application/json` (tranne upload → `multipart/form-data`)
- **Formato risposte**: `application/json`
- **Status codes HTTP**: Semantici (200, 201, 204, 400, 404, 500)
- **Validazione**: Pydantic schemas (auto-validazione con 422 Unprocessable Entity)

---

## Base URL e Versioning

```python
# app/core/config.py
api_v1_prefix = "/api/v1"
```

Tutte le rotte sono prefissate con `/api/v1`:

```
http://localhost:8000/api/v1/commesse
http://localhost:8000/api/v1/dashboard/stats
http://localhost:8000/api/v1/settings
```

---

## Autenticazione

**Attualmente non implementata** (sistema interno).

Per implementazioni future:
- OAuth2 + JWT Bearer tokens
- API Keys per integrazioni
- CORS rigoroso (whitelist localhost:5173)

---

## Endpoint Commesse

Router: [routes/commesse.py](../../backend/app/api/routes/commesse.py) (~900 righe)

Base path: `/api/v1/commesse`

### 1. Lista Commesse

**GET** `/`

Recupera tutte le commesse ordinate per data di creazione (più recenti per prime).

#### Response

```json
[
  {
    "id": 1,
    "nome": "Ospedale Milano",
    "codice": "OSP-MI-2025",
    "descrizione": "Nuovo polo ospedaliero",
    "business_unit": "Healthcare",
    "revisione": "Rev. 02",
    "stato": "in_corso",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T14:00:00Z"
  }
]
```

#### Codici di Stato

- `200 OK`: Successo

---

### 2. Crea Commessa

**POST** `/`

Crea una nuova commessa.

#### Request Body

```json
{
  "nome": "Ospedale Milano",
  "codice": "OSP-MI-2025",
  "descrizione": "Costruzione nuovo polo ospedaliero",
  "business_unit": "Healthcare",
  "revisione": "Rev. 02",
  "stato": "setup"
}
```

#### Response

```json
{
  "id": 1,
  "nome": "Ospedale Milano",
  "codice": "OSP-MI-2025",
  "descrizione": "Costruzione nuovo polo ospedaliero",
  "business_unit": "Healthcare",
  "revisione": "Rev. 02",
  "stato": "setup",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Codici di Stato

- `201 Created`: Commessa creata
- `422 Unprocessable Entity`: Validazione fallita

---

### 3. Dettagli Commessa

**GET** `/{commessa_id}`

Recupera dettagli commessa con lista computi.

#### Response

```json
{
  "id": 1,
  "nome": "Ospedale Milano",
  "codice": "OSP-MI-2025",
  "stato": "in_corso",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T14:00:00Z",
  "computi": [
    {
      "id": 1,
      "nome": "Computo Progetto",
      "tipo": "progetto",
      "importo_totale": 15000000.00,
      "created_at": "2025-01-15T11:00:00Z",
      "updated_at": "2025-01-15T11:00:00Z"
    },
    {
      "id": 2,
      "nome": "Offerta Impresa ABC - Round 1",
      "tipo": "ritorno",
      "impresa": "Impresa ABC S.p.A.",
      "round_number": 1,
      "importo_totale": 14250000.00,
      "delta_vs_progetto": -750000.00,
      "percentuale_delta": -5.0,
      "created_at": "2025-01-16T09:00:00Z",
      "updated_at": "2025-01-16T09:00:00Z"
    }
  ]
}
```

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa non trovata

---

### 4. Aggiorna Commessa

**PUT** `/{commessa_id}`

Aggiorna i dati di una commessa esistente.

#### Request Body

```json
{
  "nome": "Ospedale Milano - Aggiornato",
  "stato": "in_corso",
  "revisione": "Rev. 03"
}
```

#### Response

Schema: `CommessaSchema`

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: Commessa non trovata
- `422 Unprocessable Entity`: Validazione fallita

---

### 5. Elimina Commessa

**DELETE** `/{commessa_id}`

Elimina una commessa e tutte le entità correlate (computi, WBS, elenco prezzi).

#### Response

Nessun body (status 204)

#### Codici di Stato

- `204 No Content`: Eliminazione riuscita
- `404 Not Found`: Commessa non trovata

---

### 6. Struttura WBS Commessa

**GET** `/{commessa_id}/wbs`

Recupera la struttura WBS completa (nodi spaziali L1-5, WBS6, WBS7).

#### Response

```json
{
  "commessa_id": 1,
  "spaziali": [
    {
      "id": 1,
      "commessa_id": 1,
      "parent_id": null,
      "level": 1,
      "code": "P00",
      "description": "Edificio Principale",
      "importo_totale": null
    },
    {
      "id": 2,
      "commessa_id": 1,
      "parent_id": 1,
      "level": 2,
      "code": "L00",
      "description": "Piano Interrato",
      "importo_totale": null
    }
  ],
  "wbs6": [
    {
      "id": 1,
      "commessa_id": 1,
      "wbs_spaziale_id": 5,
      "code": "A001",
      "description": "Scavi",
      "label": "A001 - Scavi"
    }
  ],
  "wbs7": [
    {
      "id": 1,
      "commessa_id": 1,
      "wbs6_id": 1,
      "code": "A001.001",
      "description": "Scavi di sbancamento"
    }
  ]
}
```

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa non trovata

---

### 7. Import WBS da Excel

**POST** `/{commessa_id}/wbs/import`

Importa struttura WBS da file Excel (upsert nodi spaziali, WBS6, WBS7).

#### Request (multipart/form-data)

- `file`: File Excel (.xlsx, .xls, .xlsm)

#### Response

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

#### Codici di Stato

- `200 OK`: Import completato
- `400 Bad Request`: File invalido
- `404 Not Found`: Commessa non trovata

---

### 8. Gestione Visibilità WBS

#### 8.1 Ottieni Visibilità

**GET** `/{commessa_id}/wbs/visibility`

Recupera preferenze di visibilità per nodi WBS (nascosti/visibili).

#### Query Parameters

- `kind` (optional): `spaziale` | `wbs6` | `wbs7`

#### Response

```json
[
  {
    "level": 6,
    "node_id": 1,
    "code": "A001",
    "description": "Scavi",
    "hidden": true
  }
]
```

---

#### 8.2 Aggiorna Visibilità

**PUT** `/{commessa_id}/wbs/visibility`

Aggiorna lo stato di visibilità di un nodo WBS.

#### Request Body

```json
{
  "level": 6,
  "node_id": 1,
  "hidden": true
}
```

#### Response

Schema: `WbsVisibilitySchema`

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: Nodo o commessa non trovati

---

### 9. Aggiorna Nodo WBS6

**PUT** `/{commessa_id}/wbs6`

Aggiorna descrizione o label di un nodo WBS6.

#### Request Body

```json
{
  "wbs6_id": 1,
  "description": "Scavi e Movimenti Terra",
  "label": "A001 - Scavi e Movimenti Terra"
}
```

#### Response

Schema: `Wbs6NodeSchema`

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: WBS6 non trovato

---

### 10. Upload Computo Progetto

**POST** `/{commessa_id}/computo/upload`

Carica file computo metrico progetto (Excel).

#### Request (multipart/form-data)

- `file`: File Excel
- `nome`: Nome computo
- `note` (optional): Note

#### Response

```json
{
  "id": 1,
  "nome": "Computo Progetto Rev. 02",
  "tipo": "progetto",
  "importo_totale": 15000000.00,
  "file_nome": "computo_progetto.xlsx",
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Codici di Stato

- `201 Created`: Upload riuscito
- `400 Bad Request`: File invalido o parsing fallito
- `404 Not Found`: Commessa non trovata

---

### 11. Upload Ritorno Offerta

**POST** `/{commessa_id}/ritorno/upload`

Carica ritorno di gara (offerta impresa).

#### Request (multipart/form-data)

- `file`: File Excel
- `nome`: Nome ritorno
- `impresa`: Nome impresa
- `round_number`: Numero round (default: 1)
- `config_id` (optional): ID ImportConfig da usare
- `note` (optional): Note

#### Response

Schema: `ComputoSchema` (tipo="ritorno")

#### Codici di Stato

- `201 Created`: Upload riuscito
- `400 Bad Request`: File invalido o parsing fallito
- `404 Not Found`: Commessa o config non trovati

---

### 12. Confronto Offerte

**GET** `/{commessa_id}/confronto`

**DEPRECATO** - Usare `/confronto-offerte`

---

### 13. Confronto Offerte (Dettagliato)

**GET** `/api/v1/commesse/{commessa_id}/confronto-offerte`

Confronto tabulare progetto vs tutte le offerte (voce per voce).

#### Query Parameters

- `round_number` (optional): Filtra per round
- `impresa` (optional): Filtra per impresa

#### Response

```json
{
  "voci": [
    {
      "codice": "A001.001",
      "descrizione": "Scavo di sbancamento",
      "descrizione_estesa": "Scavo di sbancamento in terreni di qualsiasi natura",
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
  ],
  "imprese": [
    {
      "nome": "Offerta Impresa ABC - Round 1",
      "computo_id": 2,
      "impresa": "Impresa ABC S.p.A.",
      "round_number": 1,
      "etichetta": "Impresa ABC - Round 1",
      "round_label": "Round 1"
    }
  ],
  "rounds": [
    {
      "numero": 1,
      "label": "Round 1",
      "imprese": ["Impresa ABC S.p.A.", "Impresa XYZ S.r.l."],
      "imprese_count": 2
    }
  ]
}
```

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa non trovata o progetto mancante

---

### 14. Analisi Commessa

**GET** `/{commessa_id}/analisi`

Analisi completa con voci critiche, distribuzione variazioni, trend WBS6.

#### Query Parameters

- `round_number` (optional): Filtra per round
- `impresa` (optional): Filtra per impresa

#### Response

Schema: `AnalisiCommessaSchema` (vedi [Schemas](./03-SCHEMAS-PYDANTIC.md#analisicommessaschema))

Contiene:
- `confronto_importi`: Importi totali progetto vs offerte
- `distribuzione_variazioni`: Istogramma criticità (alta/media/bassa)
- `voci_critiche`: Top 50 voci con maggiori variazioni
- `analisi_per_wbs6`: Trend per categoria WBS6
- `rounds`: Metadati round
- `imprese`: Metadati imprese
- `filtri`: Filtri applicati
- `thresholds`: Soglie criticità

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa non trovata o progetto mancante

---

### 15. Analisi Dettagliata WBS6

**GET** `/{commessa_id}/analisi/wbs6/{wbs6_id}`

Analisi dettagliata di una categoria WBS6 (drill-down).

#### Query Parameters

- `round_number` (optional): Filtra per round
- `impresa` (optional): Filtra per impresa

#### Response

Schema: `AnalisiWBS6TrendSchema` (vedi [Schemas](./03-SCHEMAS-PYDANTIC.md#analisiwbs6trendschema))

Contiene:
- Importi aggregati (progetto, media ritorni, delta)
- Conteggi criticità (alta/media/bassa)
- Lista voci dettagliate con statistiche

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa o WBS6 non trovati

---

### 16. Elenco Prezzi Commessa

**GET** `/{commessa_id}/price-catalog`

Recupera elenco prezzi di una commessa (prodotti da STR Vision).

#### Query Parameters

- `skip` (default: 0): Offset paginazione
- `limit` (default: 100, max: 500): Numero risultati

#### Response

```json
[
  {
    "id": 1,
    "commessa_id": 1,
    "commessa_nome": "Ospedale Milano",
    "commessa_codice": "OSP-MI-2025",
    "business_unit": "Healthcare",
    "product_id": "PROD_12345",
    "item_code": "A001.001",
    "item_description": "Scavo di sbancamento",
    "unit_label": "m³",
    "wbs6_code": "A001",
    "wbs6_description": "Scavi",
    "price_lists": {
      "BASE": 12.50,
      "ALTO": 15.00
    },
    "source_file": "preventivo.six",
    "preventivo_id": "PREV_001",
    "created_at": "2025-01-15T12:00:00Z",
    "updated_at": "2025-01-15T12:00:00Z"
  }
]
```

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Commessa non trovata

---

### 17. Elenco Prezzi Globale

**GET** `/price-catalog`

Recupera elenco prezzi da tutte le commesse (cross-commessa).

#### Query Parameters

- `skip` (default: 0): Offset
- `limit` (default: 100, max: 500): Limite
- `commessa_id` (optional): Filtra per commessa
- `business_unit` (optional): Filtra per business unit

#### Response

Schema: `List[PriceListItemSchema]`

#### Codici di Stato

- `200 OK`: Successo

---

### 18. Ricerca Semantica Elenco Prezzi

**GET** `/price-catalog/search`

Ricerca avanzata con embedding semantico + lexical boost.

#### Query Parameters

- `q` (required): Query di ricerca
- `commessa_id` (optional): Filtra per commessa
- `business_unit` (optional): Filtra per business unit
- `wbs6_code` (optional): Filtra per WBS6
- `limit` (default: 50, max: 200): Numero risultati

#### Response

```json
[
  {
    "id": 1,
    "item_code": "A001.001",
    "item_description": "Scavo di sbancamento in terreni di qualsiasi natura",
    "wbs6_code": "A001",
    "wbs6_description": "Scavi",
    "price_lists": {"BASE": 12.50},
    "score": 0.92,
    "match_reason": "semantic_similarity",
    ...
  }
]
```

#### Algoritmo

1. Genera embedding query (384-dim)
2. Cosine similarity con tutti gli embedding
3. Lexical boost (keyword matching: codice, descrizione, WBS6)
4. Score finale = `0.7 * similarity + 0.3 * lexical_boost`
5. Ordina per score decrescente

#### Codici di Stato

- `200 OK`: Successo
- `400 Bad Request`: Query mancante

---

### 19. Sommario Catalogo Prezzi

**GET** `/price-catalog/summary`

Statistiche aggregate catalogo multi-commessa.

#### Response

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
    },
    {
      "label": "Non classificato",
      "value": null,
      "items_count": 2220,
      "commesse": [...]
    }
  ]
}
```

#### Codici di Stato

- `200 OK`: Successo

---

### 20. Preview Preventivi STR Vision

**POST** `/{commessa_id}/six/preview`

Estrae lista preventivi disponibili in un file STR Vision (.six/.xml) senza importare.

#### Request (multipart/form-data)

- `file`: File STR Vision (.six, .xml)

#### Response

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

#### Codici di Stato

- `200 OK`: Successo
- `400 Bad Request`: File invalido o parsing fallito
- `404 Not Found`: Commessa non trovata

---

### 21. Import STR Vision

**POST** `/{commessa_id}/six/import`

Importa file STR Vision (WBS spaziale, WBS6, WBS7, elenco prezzi, computo progetto).

#### Request (multipart/form-data)

- `file`: File STR Vision
- `preventivo_id` (optional): ID preventivo da importare (se file contiene più preventivi)
- `nome` (optional): Nome computo progetto (default: auto-generato)
- `replace_catalog` (default: true): Sostituisci elenco prezzi esistente

#### Response

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

#### Processo

1. Parse XML/ZIP
2. Upsert WBS spaziale (L1-5)
3. Upsert WBS6 (categorie)
4. Upsert WBS7 (raggruppatori)
5. Sostituisci elenco prezzi (DELETE + INSERT bulk)
6. Genera embedding per ogni prodotto (NLP)
7. Crea Computo(tipo="progetto") con voci

#### Codici di Stato

- `200 OK`: Import completato
- `400 Bad Request`: File invalido, parsing fallito, o preventivo non trovato
- `404 Not Found`: Commessa non trovata

---

### 22. Elimina Computo

**DELETE** `/{commessa_id}/computo/{computo_id}`

Elimina un computo (progetto o ritorno) e tutte le voci associate.

#### Codici di Stato

- `204 No Content`: Eliminazione riuscita
- `404 Not Found`: Computo o commessa non trovati

---

### 23. Preferenze Commessa

#### 23.1 Ottieni Preferenze

**GET** `/{commessa_id}/preferences`

Recupera preferenze commessa (preventivo selezionato, listino, view WBS).

#### Response

```json
{
  "id": 1,
  "commessa_id": 1,
  "selected_preventivo_id": "PREV_001",
  "selected_price_list_id": "BASE",
  "default_wbs_view": "wbs6",
  "custom_settings": {
    "theme": "dark",
    "show_advanced_filters": true
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T14:00:00Z"
}
```

#### Codici di Stato

- `200 OK`: Successo (crea record default se non esiste)
- `404 Not Found`: Commessa non trovata

---

#### 23.2 Aggiorna Preferenze

**PUT** `/{commessa_id}/preferences`

Aggiorna preferenze commessa.

#### Request Body

```json
{
  "selected_preventivo_id": "PREV_002",
  "selected_price_list_id": "ALTO",
  "default_wbs_view": "spaziale"
}
```

#### Response

Schema: `CommessaPreferencesRead`

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: Commessa non trovata

---

## Endpoint Computi

Router: [routes/computi.py](../../backend/app/api/routes/computi.py)

Base path: `/api/v1/computi`

### 1. Sommario WBS Computo

**GET** `/{computo_id}/wbs`

Recupera struttura WBS aggregata per un computo (tree gerarchico + voci).

#### Response

```json
{
  "importo_totale": 15000000.00,
  "tree": [
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
  ],
  "voci": [
    {
      "codice": "A001.001",
      "descrizione": "Scavo di sbancamento",
      "quantita_totale": 1500.0,
      "importo_totale": 18750.00,
      "prezzo_unitario": 12.50,
      "unita_misura": "m³",
      "wbs_6_code": "A001",
      "wbs_6_description": "Scavi",
      "wbs_path": [
        {"level": 1, "code": "P00", "description": "Edificio Principale"},
        {"level": 2, "code": "L00", "description": "Piano Interrato"}
      ]
    }
  ]
}
```

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Computo non trovato

---

## Endpoint Dashboard

Router: [routes/dashboard.py](../../backend/app/api/routes/dashboard.py)

Base path: `/api/v1/dashboard`

### 1. Statistiche Dashboard

**GET** `/stats`

Recupera statistiche aggregate e attività recenti.

#### Response

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

#### Logica

- `commesse_attive`: Commesse con stato != "chiusa"
- `computi_caricati`: Totale computi (progetto + ritorni)
- `ritorni`: Computi con tipo="ritorno"
- `report_generati`: Mock (sempre 0, da implementare)
- `attivita_recente`: Ultimi 10 computi caricati (ordinati per created_at DESC)

#### Codici di Stato

- `200 OK`: Successo

---

## Endpoint Settings

Router: [routes/settings.py](../../backend/app/api/routes/settings.py)

Base path: `/api/v1/settings`

### 1. Ottieni Settings

**GET** `/`

Recupera impostazioni globali (singleton).

#### Response

```json
{
  "id": 1,
  "delta_minimo_critico": -30000.0,
  "delta_massimo_critico": 1000.0,
  "percentuale_cme_alto": 25.0,
  "percentuale_cme_basso": 50.0,
  "criticita_media_percent": 25.0,
  "criticita_alta_percent": 50.0,
  "created_at": "2025-01-10T00:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

#### Comportamento

- Se non esiste record Settings, ne crea uno con valori di default
- Singleton: sempre 1 record nel database

#### Codici di Stato

- `200 OK`: Successo

---

### 2. Aggiorna Settings

**PUT** `/`

Aggiorna impostazioni globali (partial update).

#### Request Body

```json
{
  "delta_minimo_critico": -40000.0,
  "criticita_alta_percent": 60.0
}
```

#### Response

Schema: `SettingsRead` (settings aggiornati)

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: Settings non trovati (non dovrebbe mai succedere)

---

## Endpoint Import Configs

Router: [routes/import_configs.py](../../backend/app/api/routes/import_configs.py)

Base path: `/api/v1/import-configs`

### 1. Lista Configurazioni

**GET** `/`

Recupera tutte le configurazioni import.

#### Query Parameters

- `commessa_id` (optional): Filtra per commessa

#### Response

```json
[
  {
    "id": 1,
    "commessa_id": null,
    "nome": "Formato Impresa ABC",
    "impresa": "Impresa ABC S.p.A.",
    "sheet_name": "Offerta Economica",
    "code_columns": "A,B",
    "description_columns": "C,D",
    "price_column": "E",
    "quantity_column": "F",
    "note": "Formato standard utilizzato da Impresa ABC",
    "created_at": "2025-01-10T10:00:00Z",
    "updated_at": "2025-01-10T10:00:00Z"
  }
]
```

#### Codici di Stato

- `200 OK`: Successo

---

### 2. Crea Configurazione

**POST** `/`

Crea una nuova configurazione import.

#### Request Body

```json
{
  "nome": "Formato Impresa XYZ",
  "impresa": "Impresa XYZ S.r.l.",
  "sheet_name": "Foglio1",
  "code_columns": "A",
  "description_columns": "B",
  "price_column": "C",
  "quantity_column": "D",
  "note": "Configurazione custom per Impresa XYZ"
}
```

#### Response

Schema: `ImportConfigRead`

#### Codici di Stato

- `201 Created`: Creazione riuscita
- `422 Unprocessable Entity`: Validazione fallita

---

### 3. Dettagli Configurazione

**GET** `/{config_id}`

Recupera dettagli configurazione.

#### Response

Schema: `ImportConfigRead`

#### Codici di Stato

- `200 OK`: Successo
- `404 Not Found`: Config non trovata

---

### 4. Aggiorna Configurazione

**PUT** `/{config_id}`

Aggiorna configurazione esistente (partial update).

#### Request Body

```json
{
  "nome": "Formato Impresa XYZ - Aggiornato",
  "price_column": "F"
}
```

#### Response

Schema: `ImportConfigRead`

#### Codici di Stato

- `200 OK`: Aggiornamento riuscito
- `404 Not Found`: Config non trovata
- `422 Unprocessable Entity`: Validazione fallita

---

### 5. Elimina Configurazione

**DELETE** `/{config_id}`

Elimina configurazione import.

#### Response

Nessun body (status 204)

#### Codici di Stato

- `204 No Content`: Eliminazione riuscita
- `404 Not Found`: Config non trovata

---

## Gestione Errori

### Status Codes Comuni

| Codice | Descrizione | Quando |
|--------|-------------|--------|
| `200 OK` | Successo (GET, PUT) | Request completata con successo |
| `201 Created` | Risorsa creata (POST) | Nuova entità creata |
| `204 No Content` | Successo senza body (DELETE) | Eliminazione riuscita |
| `400 Bad Request` | Input invalido | File corrotto, parsing fallito, validazione business |
| `404 Not Found` | Risorsa non trovata | ID inesistente |
| `422 Unprocessable Entity` | Validazione Pydantic fallita | Schema request invalido |
| `500 Internal Server Error` | Errore server | Eccezione non gestita |

### Formato Errore Standard

FastAPI HTTPException:

```json
{
  "detail": "Commessa con ID 999 non trovata"
}
```

Validazione Pydantic (422):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "nome"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

### Esempi HTTPException

```python
# 404 Not Found
raise HTTPException(status_code=404, detail="Commessa non trovata")

# 400 Bad Request
raise HTTPException(status_code=400, detail="File Excel corrotto o formato non valido")

# 500 Internal Server Error (automatico se eccezione non gestita)
```

---

## Rate Limiting e Throttling

**Non implementato** (sistema interno).

Per implementazioni future:
- SlowAPI (rate limiting per IP/user)
- Redis per distributed rate limiting
- Limiti suggeriti:
  - `/price-catalog/search`: 60 req/min (computazionalmente costoso)
  - Upload endpoints: 10 req/min
  - Altri endpoints: 300 req/min

---

## CORS Configuration

File: [main.py](../../backend/app/main.py)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**Rigoroso**: No wildcard `*`, solo frontend development whitelisted.

---

## Documentazione Interattiva

### Swagger UI

URL: `http://localhost:8000/docs` (solo se `debug=true`)

- Esplora API
- Testa endpoint
- Visualizza schemi

### ReDoc

URL: `http://localhost:8000/redoc` (solo se `debug=true`)

- Documentazione alternativa
- Layout più pulito

---

## Prossimi Passi

- [Services](./05-SERVICES.md) - Business logic e service layer
- [Parser Excel](./06-PARSER-EXCEL.md) - Logica parsing computi
- [NLP Service](./07-NLP-SERVICE.md) - Embedding e ricerca semantica
- [STR Vision Import](./08-SIX-IMPORT.md) - Parser STR Vision
