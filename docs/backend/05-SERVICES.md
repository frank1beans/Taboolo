# Services - Business Logic Layer

## Indice
- [Panoramica](#panoramica)
- [Architettura Service Layer](#architettura-service-layer)
- [CommesseService](#commesseservice)
- [ImportService](#importservice)
- [SixImportService](#siximportservice)
- [AnalysisService](#analysisservice)
- [InsightsService](#insightsservice)
- [SemanticEmbeddingService](#SemanticEmbeddingService)
- [PriceCatalogService](#pricecatalogservice)
- [StorageService](#storageservice)
- [WbsImportService](#wbsimportservice)
- [WbsVisibilityService](#wbsvisibilityservice)
- [Pattern e Best Practices](#pattern-e-best-practices)

## Panoramica

Il service layer implementa tutta la business logic dell'applicazione, isolando le API routes dalla complessità delle operazioni.

### Servizi Disponibili

File: [services/__init__.py](../../backend/app/services/__init__.py)

| Servizio | File | Responsabilità | Singleton |
|----------|------|----------------|-----------|
| **CommesseService** | commesse.py | CRUD commesse e computi | No |
| **ImportService** | importer.py | Import Excel computi | Sì (`import_service`) |
| **SixImportService** | six_import_service.py | Import STR Vision | Sì (`six_import_service`) |
| **AnalysisService** | analysis.py | Aggregazioni WBS | No |
| **InsightsService** | insights.py | Analisi e confronti | No |
| **SemanticEmbeddingService** | nlp.py | Embedding NLP | Sì (`semantic_embedding_service`) |
| **PriceCatalogService** | price_catalog.py | Gestione elenco prezzi | Sì (`price_catalog_service`) |
| **StorageService** | storage.py | File management | Sì (`storage_service`) |
| **WbsImportService** | wbs_import.py | Import WBS Excel | No |
| **WbsVisibilityService** | wbs_visibility.py | Visibilità WBS | No |

### Import Pattern

```python
from app.services import (
    CommesseService,
    import_service,          # Singleton
    six_import_service,      # Singleton
    semantic_embedding_service,       # Singleton
    price_catalog_service,   # Singleton
    storage_service,         # Singleton
)

# Uso
commesse = CommesseService.list_commesse(session)
computo = import_service.import_computo_progetto(session, commessa_id, file, nome)
```

---

## Architettura Service Layer

### Design Principles

1. **Single Responsibility**: Ogni servizio gestisce un singolo dominio
2. **Dependency Injection**: Session passata come parametro (no global state)
3. **Separation of Concerns**: Business logic separata da API e database
4. **Composition over Inheritance**: Servizi usano altri servizi (no ereditarietà)
5. **Transactional Boundaries**: Caller gestisce commit/rollback

### Flusso Dati

```
┌─────────────────────────────────────────────────────────┐
│                  API Routes Layer                       │
│  - Validazione input (Pydantic)                         │
│  - Gestione errori HTTP                                 │
│  - Serializzazione response                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                Service Layer (questo)                   │
│  - Business logic                                       │
│  - Orchestrazione                                       │
│  - Validazione business rules                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│               Database Layer (SQLModel)                 │
│  - ORM queries                                          │
│  - Transaction management                               │
│  - Data persistence                                     │
└─────────────────────────────────────────────────────────┘
```

---

## CommesseService

File: [services/commesse.py](../../backend/app/services/commesse.py)

**Responsabilità**: CRUD per commesse e computi.

### Metodi Pubblici

#### 1. list_commesse

```python
@staticmethod
def list_commesse(session: Session) -> Sequence[Commessa]
```

Recupera tutte le commesse ordinate per data di creazione (più recenti per prime).

**Esempio:**
```python
commesse = CommesseService.list_commesse(session)
for c in commesse:
    print(f"{c.codice}: {c.nome}")
```

---

#### 2. get_commessa

```python
@staticmethod
def get_commessa(session: Session, commessa_id: int) -> Commessa | None
```

Recupera una commessa per ID.

**Returns**: `Commessa` o `None` se non trovata.

---

#### 3. get_commessa_with_computi

```python
@staticmethod
def get_commessa_with_computi(
    session: Session,
    commessa_id: int
) -> tuple[Commessa | None, list[Computo]]
```

Recupera commessa con lista computi associati (ordinati per created_at DESC).

**Returns**: Tupla `(commessa, computi)` o `(None, [])` se non trovata.

**Esempio:**
```python
commessa, computi = CommesseService.get_commessa_with_computi(session, 1)
if commessa:
    progetto = [c for c in computi if c.tipo == ComputoTipo.progetto]
    ritorni = [c for c in computi if c.tipo == ComputoTipo.ritorno]
```

---

#### 4. create_commessa

```python
@staticmethod
def create_commessa(
    session: Session,
    payload: CommessaCreate
) -> Commessa
```

Crea una nuova commessa.

**Esempio:**
```python
payload = CommessaCreate(
    nome="Ospedale Milano",
    codice="OSP-MI-2025",
    business_unit="Healthcare"
)
commessa = CommesseService.create_commessa(session, payload)
session.commit()
```

---

#### 5. update_commessa

```python
@staticmethod
def update_commessa(
    session: Session,
    commessa_id: int,
    payload: CommessaCreate
) -> Commessa | None
```

Aggiorna commessa esistente (partial update).

**Returns**: Commessa aggiornata o `None` se non trovata.

---

#### 6. add_computo

```python
@staticmethod
def add_computo(
    session: Session,
    commessa: Commessa,
    nome: str,
    tipo: ComputoTipo,
    impresa: str | None = None,
    round_number: int | None = None,
    file_nome: str | None = None,
    file_percorso: str | None = None,
    note: str | None = None
) -> Computo
```

Crea un nuovo computo (progetto o ritorno) associato a una commessa.

**Esempio:**
```python
computo = CommesseService.add_computo(
    session,
    commessa=commessa,
    nome="Computo Progetto Rev. 02",
    tipo=ComputoTipo.progetto,
    file_nome="computo.xlsx",
    file_percorso="storage/commessa_0001/computo.xlsx"
)
session.commit()
```

---

#### 7. delete_computo

```python
@staticmethod
def delete_computo(
    session: Session,
    commessa_id: int,
    computo_id: int
) -> Computo | None
```

Elimina un computo e tutte le voci associate (cascade).

**Returns**: Computo eliminato o `None` se non trovato.

**Implementazione:**
```python
# 1. Verifica esistenza
computo = session.get(Computo, computo_id)
if not computo or computo.commessa_id != commessa_id:
    return None

# 2. Elimina voci
session.exec(delete(VoceComputo).where(VoceComputo.computo_id == computo_id))

# 3. Elimina file
if computo.file_percorso:
    storage_service.delete_file(computo.file_percorso)

# 4. Elimina computo
session.delete(computo)
session.commit()
```

---

#### 8. delete_commessa

```python
@staticmethod
def delete_commessa(
    session: Session,
    commessa_id: int
) -> Commessa | None
```

Elimina commessa e tutte le entità correlate (cascade completo).

**Entità eliminate:**
- Computi e VoceComputo
- WbsSpaziale, Wbs6, Wbs7, WbsVisibility
- PriceListItem
- CommessaPreferences
- ImportConfig
- Directory file storage

---

## ImportService

File: [services/importer.py](../../backend/app/services/importer.py) (~800 righe)

**Responsabilità**: Import computi da Excel con matching intelligente.

### Metodi Pubblici

#### 1. import_computo_progetto

```python
def import_computo_progetto(
    session: Session,
    commessa_id: int,
    file: Path,
    originale_nome: str,
    nome: str | None = None
) -> Computo
```

Importa computo metrico progetto da file Excel.

**Processo:**
1. Parse Excel → `parse_computo_excel(file)`
2. Crea Computo (tipo="progetto")
3. Persist voci → `persist_project_from_parsed()`
4. Calcola `importo_totale`
5. Commit

**Esempio:**
```python
computo = import_service.import_computo_progetto(
    session,
    commessa_id=1,
    file=Path("storage/commessa_0001/computo.xlsx"),
    originale_nome="computo_progetto.xlsx",
    nome="Computo Progetto Rev. 02"
)
print(f"Importate {len(computo.voci)} voci, totale: €{computo.importo_totale}")
```

---

#### 2. import_computo_ritorno

```python
def import_computo_ritorno(
    session: Session,
    commessa_id: int,
    impresa: str,
    file: Path,
    originale_nome: str,
    nome: str | None = None,
    round_number: int = 1,
    round_mode: Literal["new", "update"] = "new",
    sheet_name: str | None = None,
    sheet_code_columns: str | None = None,
    sheet_description_columns: str | None = None,
    sheet_price_column: str | None = None,
    sheet_quantity_column: str | None = None
) -> Computo
```

Importa ritorno di gara con matching intelligente contro progetto.

**Processo:**
1. Carica computo progetto
2. Parse Excel (standard o custom config)
3. **Matching voci** progetto vs ritorno:
   - Codice esatto
   - Descrizione simile (token-based)
   - WBS matching (livelli 6-7)
   - Fallback a gruppi aggregati
4. Verifica delta prezzi eccessivi → warning
5. **Zero-guard**: Forza prezzi zero per voci specifiche (oneri CM, coord., sicurezza)
6. Crea Computo (tipo="ritorno")
7. Persist voci matched
8. Calcola delta vs progetto

**Esempio:**
```python
computo = import_service.import_computo_ritorno(
    session,
    commessa_id=1,
    impresa="Impresa ABC S.p.A.",
    file=Path("storage/commessa_0001/offerta_abc.xlsx"),
    originale_nome="offerta_impresa_abc_round1.xlsx",
    round_number=1
)

print(f"Delta vs progetto: {computo.percentuale_delta:.2f}%")
print(f"Warnings: {len(computo.warnings)}")
```

**Parametri Custom Mapping:**
- `sheet_name`: Nome foglio da parsare
- `sheet_code_columns`: Colonne codice (es: "A,B" → concatena)
- `sheet_description_columns`: Colonne descrizione
- `sheet_price_column`: Colonna prezzo unitario
- `sheet_quantity_column`: Colonna quantità

---

#### 3. persist_project_from_parsed

```python
def persist_project_from_parsed(
    session: Session,
    commessa_id: int,
    computo: Computo,
    parsed_voci: list[dict[str, Any]]
) -> list[VoceComputo]
```

Persiste voci progetto normalizzate (usato internamente da import_computo_progetto e six_import_service).

**Logica:**
- Normalizza WBS codes (A### → A###.000)
- Crea VoceComputo per ogni voce
- Bulk insert (`session.add_all()`)
- Calcola `global_code` = `{commessa_code}#{codice}`

---

### Algoritmo Matching Intelligente

**Criteri di matching (in ordine di priorità):**

1. **Exact Code Match**
   ```python
   if ritorno.codice == progetto.codice:
       return Match(score=1.0, method="exact_code")
   ```

2. **WBS6 + Token Similarity**
   ```python
   if ritorno.wbs_6_code == progetto.wbs_6_code:
       similarity = jaccard_similarity(tokens_ritorno, tokens_progetto)
       if similarity > 0.5:
           return Match(score=similarity, method="wbs6_token")
   ```

3. **WBS7 Match**
   ```python
   if ritorno.wbs_7_code and ritorno.wbs_7_code == progetto.wbs_7_code:
       return Match(score=0.9, method="wbs7_exact")
   ```

4. **Description Token Similarity**
   ```python
   tokens_r = tokenize(ritorno.descrizione)
   tokens_p = tokenize(progetto.descrizione)
   similarity = jaccard_similarity(tokens_r, tokens_p)
   if similarity > 0.6:
       return Match(score=similarity, method="description_token")
   ```

5. **Fallback to Group Aggregates**
   ```python
   # Se voce ritorno non matcha ma appartiene a gruppo WBS6
   # → aggrega tutte le voci progetto dello stesso WBS6
   if not matched and ritorno.wbs_6_code:
       grouped_voci = filter(lambda v: v.wbs_6_code == ritorno.wbs_6_code, progetto_voci)
       return AggregatedMatch(voci=grouped_voci)
   ```

**Warning Generation:**
- Voci ritorno non matchate → `"Voce non trovata in progetto"`
- Voci progetto non coperte → `"Voce progetto mancante in ritorno"`
- Delta prezzo > 50% → `"Prezzo deviato oltre soglia"`

---

### Zero-Guard Protection

**Descrizioni che forzano prezzo zero:**
```python
ZERO_GUARD_KEYWORDS = [
    "oneri cm",
    "coordinamento",
    "coord. sicurezza",
    "costi sicurezza",
    "piano sicurezza"
]

if any(keyword in descrizione.lower() for keyword in ZERO_GUARD_KEYWORDS):
    voce.prezzo_unitario = 0.0
    voce.importo = 0.0
```

**Rationale**: Evita che imprese "gonfino" prezzi su voci amministrative/sicurezza.

---

## SixImportService

File: [services/six_import_service.py](../../backend/app/services/six_import_service.py) (~800 righe)

**Responsabilità**: Import file STR Vision (.six, .xml).

### Metodi Pubblici

#### 1. import_six_file

```python
def import_six_file(
    session: Session,
    commessa_id: int,
    file_path: Path,
    preventivo_id: str | None = None,
    nome_computo: str | None = None,
    replace_catalog: bool = True
) -> dict[str, Any]
```

Importa file STR Vision completo (WBS, elenco prezzi, computo progetto).

**Processo:**
1. **Parse XML** → `SixParser.parse(file_path)`
   - Estrae WBS spaziale (L1-5)
   - Estrae WBS6 (categorie A###)
   - Estrae WBS7 (raggruppatori A###.###)
   - Estrae prodotti + listini
   - Estrae misurazioni + quantità

2. **Selezione Preventivo**
   ```python
   if not preventivo_id:
       preventivo = parsed.preventivi[0]  # Default: primo
   else:
       preventivo = find_preventivo(parsed.preventivi, preventivo_id)
       if not preventivo:
           raise PreventivoSelectionError("Preventivo non trovato")
   ```

3. **Upsert WBS Spaziale**
   ```python
   for node in parsed.wbs_spaziale:
       wbs = session.get(WbsSpaziale, node.id)
       if wbs:
           # Update
           wbs.code = node.code
           wbs.description = node.description
       else:
           # Insert
           wbs = WbsSpaziale(**node)
           session.add(wbs)
   ```

4. **Upsert WBS6 e WBS7**
   - Normalizza codici (rimuovi duplicati)
   - Crea nodi con `label = f"{code} - {description}"`

5. **Replace Elenco Prezzi**
   ```python
   price_catalog_service.replace_catalog(
       session,
       commessa=commessa,
       entries=parsed.products,
       source_file=file_path.name,
       preventivo_id=preventivo_id,
       price_list_labels=parsed.price_list_labels,
       preferred_lists=["BASE", "LISTINO_01"]
   )
   ```

6. **Crea Computo Progetto**
   ```python
   voci_progetto = build_voci_from_measurements(parsed.measurements, products)
   computo = import_service.persist_project_from_parsed(
       session,
       commessa_id,
       computo,
       voci_progetto
   )
   ```

**Returns:**
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

#### 2. inspect_content

```python
@staticmethod
def inspect_content(
    file_bytes: bytes,
    filename: str | None = None
) -> list[dict[str, Any]]
```

Estrae lista preventivi disponibili in un file STR Vision (senza importare).

**Returns:**
```python
[
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
```

**Uso:**
```python
with open("file.six", "rb") as f:
    preventivi = six_import_service.inspect_content(f.read(), "file.six")

for p in preventivi:
    print(f"{p['code']}: {p['description']}")
```

---

#### 3. inspect_details

```python
@staticmethod
def inspect_details(
    file_bytes: bytes,
    filename: str | None = None
) -> dict[str, Any]
```

Ispezione completa del file SIX/XML: restituisce preventivi, listini (con alias/priorità), WBS (spaziali, WBS6, WBS7) e conteggio prodotti senza importare nulla.

**Returns:**
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
  "wbs_spaziali": [ { "grp_id": "w1", "code": "A", "level": 1 } ],
  "wbs6": [ { "grp_id": "w6", "code": "A001", "level": 6 } ],
  "wbs7": [ { "grp_id": "w7", "code": "A001.010", "level": 7 } ],
  "products_total": 450
}
```

**Uso:**
```python
with open("file.six", "rb") as f:
    overview = six_import_service.inspect_details(f.read(), "file.six")
    for pl in overview["price_lists"]:
        print(pl["canonical_id"], pl["products"])
```

---

### SixParser (Modulo Interno)

**Responsabilità**: Parse XML STR Vision con namespace handling.

**Struttura XML Tipica:**
```xml
<SIXfile xmlns="http://www.acca.it/SIX">
  <PweDocumento>
    <PweDatiGenerali>
      <PwePrezzario>
        <EPUList>
          <EPU ID="A001.001">
            <Descrizione>Scavo di sbancamento</Descrizione>
            <UnitaMisura>m³</UnitaMisura>
            <PrezziList>
              <Prezzo Listino="BASE">12.50</Prezzo>
            </PrezziList>
          </EPU>
        </EPUList>
      </PwePrezzario>
    </PweDatiGenerali>

    <PweMisurazioni>
      <PweCapitoloList>
        <PweCapitolo ID="CAP_001">
          <RowList>
            <Row EPURef="A001.001" Quantita="1500.0" />
          </RowList>
        </PweCapitolo>
      </PweCapitoloList>
    </PweMisurazioni>
  </PweDocumento>
</SIXfile>
```

**Parsing Steps:**
1. Unzip `.six` (se ZIP)
2. Parse XML con `xml.etree.ElementTree`
3. Namespace stripping (`{http://...}` → ``)
4. Estrazione preventivi
5. Estrazione prodotti (EPU)
6. Estrazione misurazioni
7. Reference resolution (EPURef → prodotto)
8. Quantity aggregation

---

## AnalysisService

File: [services/analysis.py](../../backend/app/services/analysis.py) (~200 righe)

**Responsabilità**: Aggregazioni WBS e viste gerarchiche.

### Metodi Pubblici

#### 1. get_wbs_summary

```python
@staticmethod
def get_wbs_summary(
    session: Session,
    computo_id: int
) -> ComputoWbsSummary
```

Genera sommario WBS per un computo (tree + voci aggregate).

**Returns:**
```python
ComputoWbsSummary(
    importo_totale=15000000.00,
    tree=[
        WbsNodeSchema(
            level=1,
            code="P00",
            description="Edificio Principale",
            importo=15000000.00,
            children=[...]
        )
    ],
    voci=[
        AggregatedVoceSchema(
            codice="A001.001",
            descrizione="Scavo di sbancamento",
            quantita_totale=1500.0,
            importo_totale=18750.00,
            wbs_path=[...]
        )
    ]
)
```

**Processo:**
1. Carica voci computo
2. Filtra voci nascoste (via WbsVisibilityService)
3. Aggrega voci per WBS path + codice
4. Costruisce tree gerarchico (L1 → L2 → ... → L6/L7)
5. Calcola importi totali per nodo

**Esempio:**
```python
summary = AnalysisService.get_wbs_summary(session, computo_id=1)

# Naviga tree
for node_l1 in summary.tree:
    print(f"Livello 1: {node_l1.code} - €{node_l1.importo}")
    for node_l2 in node_l1.children:
        print(f"  Livello 2: {node_l2.code} - €{node_l2.importo}")

# Voci aggregate
for voce in summary.voci:
    print(f"{voce.codice}: €{voce.importo_totale} ({voce.quantita_totale} {voce.unita_misura})")
```

---

### WBS Normalization

**Codice normalizzato:**
```python
def normalize_wbs_code(code: str | None) -> str:
    if not code:
        return ""
    # A001 → A001.000
    # A001.001 → A001.001
    # A001_001 → A001.001
    code = code.replace("_", ".")
    if "." not in code:
        return f"{code}.000"
    return code
```

**Fallback per voci senza WBS7:**
```python
# Se wbs_7_code è None → usa codice articolo
aggregation_key = wbs_7_code or codice or "SCONOSCIUTO"
```

---

## InsightsService

File: [services/insights.py](../../backend/app/services/insights.py) (~600 righe)

**Responsabilità**: Analisi comparative, voci critiche, trend WBS6.

### Metodi Pubblici

#### 1. get_dashboard_stats

```python
@staticmethod
def get_dashboard_stats(session: Session) -> DashboardStatsSchema
```

Genera statistiche dashboard (mock parziale).

**Returns:**
```json
{
  "commesse_attive": 5,
  "computi_caricati": 18,
  "ritorni": 12,
  "report_generati": 0,
  "attivita_recente": [...]
}
```

---

#### 2. get_commessa_confronto

```python
@staticmethod
def get_commessa_confronto(
    session: Session,
    commessa_id: int,
    round_number: int | None = None,
    impresa: str | None = None
) -> ConfrontoOfferteSchema
```

Confronto tabulare progetto vs offerte (voce per voce).

**Returns:**
```python
ConfrontoOfferteSchema(
    voci=[
        ConfrontoVoceSchema(
            codice="A001.001",
            descrizione="Scavo di sbancamento",
            prezzo_unitario_progetto=12.50,
            importo_totale_progetto=18750.00,
            offerte={
                "Impresa ABC - Round 1": ConfrontoVoceOffertaSchema(
                    prezzo_unitario=10.00,
                    importo_totale=15000.00,
                    criticita="media"
                )
            }
        )
    ],
    imprese=[...],
    rounds=[...]
)
```

**Processo:**
1. Carica computo progetto + ritorni
2. Filtra ritorni (per round/impresa se specificato)
3. Merge voci progetto + offerte (chiave: wbs_6_code + descrizione normalizzata)
4. Calcola criticità per ogni offerta
5. Genera metadati imprese e round

**Esempio:**
```python
confronto = InsightsService.get_commessa_confronto(
    session,
    commessa_id=1,
    round_number=1
)

for voce in confronto.voci:
    print(f"{voce.codice}: Progetto €{voce.importo_totale_progetto}")
    for impresa, offerta in voce.offerte.items():
        delta = ((offerta.importo_totale - voce.importo_totale_progetto) / voce.importo_totale_progetto) * 100
        print(f"  {impresa}: €{offerta.importo_totale} ({delta:+.2f}%, {offerta.criticita})")
```

---

#### 3. get_commessa_analisi

```python
@staticmethod
def get_commessa_analisi(
    session: Session,
    commessa_id: int,
    round_number: int | None = None,
    impresa: str | None = None
) -> AnalisiCommessaSchema
```

Analisi completa commessa (importi, distribuzione, voci critiche, trend WBS6).

**Returns:**
```python
AnalisiCommessaSchema(
    confronto_importi=[...],           # Progetto vs ritorni
    distribuzione_variazioni=[...],    # Istogramma criticità
    voci_critiche=[...],               # Top 50 voci critiche
    analisi_per_wbs6=[...],            # Trend per categoria
    rounds=[...],                      # Metadati round
    imprese=[...],                     # Metadati imprese
    filtri=AnalisiFiltriSchema(...),   # Filtri applicati
    thresholds=AnalisiThresholdsSchema(...)  # Soglie criticità
)
```

**Componenti:**

##### A. Confronto Importi
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

##### B. Distribuzione Variazioni
```json
[
  {"nome": "Criticità Alta", "valore": 15, "colore": "#dc2626"},
  {"nome": "Criticità Media", "valore": 42, "colore": "#f59e0b"},
  {"nome": "Criticità Bassa", "valore": 120, "colore": "#10b981"}
]
```

##### C. Voci Critiche
```json
[
  {
    "codice": "A001.001",
    "descrizione": "Scavo di sbancamento",
    "progetto": 18750.00,
    "imprese": {
      "Impresa ABC": 12500.00,
      "Impresa XYZ": 15000.00
    },
    "delta": -30.0,
    "criticita": "alta",
    "delta_assoluto": -5625.00,
    "media_prezzo_unitario": 11.67,
    "deviazione_standard": 1250.00,
    "direzione": "ribasso"
  }
]
```

**Classificazione Criticità:**
```python
def classify_criticita(delta_percent: float, thresholds: Settings) -> str:
    abs_delta = abs(delta_percent)
    if abs_delta >= thresholds.criticita_alta_percent:  # Default: 50%
        return "alta"
    elif abs_delta >= thresholds.criticita_media_percent:  # Default: 25%
        return "media"
    return "bassa"

def classify_direzione(delta_percent: float) -> str:
    if delta_percent > 5:
        return "rialzo"
    elif delta_percent < -5:
        return "ribasso"
    return "neutrale"
```

##### D. Analisi per WBS6
```json
[
  {
    "wbs6_id": "1",
    "wbs6_label": "A001 - Scavi",
    "wbs6_code": "A001",
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
    "voci": [...]
  }
]
```

**Esempio:**
```python
analisi = InsightsService.get_commessa_analisi(
    session,
    commessa_id=1,
    round_number=1
)

# Voci critiche
print(f"Voci critiche: {len(analisi.voci_critiche)}")
for voce in analisi.voci_critiche[:10]:  # Top 10
    print(f"  {voce.codice}: {voce.delta:+.2f}% ({voce.criticita})")

# Distribuzione
for dist in analisi.distribuzione_variazioni:
    print(f"{dist.nome}: {dist.valore} voci")

# Trend WBS6
for trend in analisi.analisi_per_wbs6:
    print(f"{trend.wbs6_label}: Progetto €{trend.progetto}, Media ritorni €{trend.media_ritorni} ({trend.delta_percentuale:+.2f}%)")
```

---

#### 4. get_commessa_wbs6_dettaglio

```python
@staticmethod
def get_commessa_wbs6_dettaglio(
    session: Session,
    commessa_id: int,
    wbs6_id: int,
    round_number: int | None = None,
    impresa: str | None = None
) -> AnalisiWBS6TrendSchema
```

Drill-down su una categoria WBS6 (dettaglio voci).

**Returns**: Schema identico a elemento di `analisi_per_wbs6`, ma con tutte le voci (no limit).

---

### Jaccard Similarity (Token Matching)

**Algoritmo:**
```python
def jaccard_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union

# Esempio
tokens_a = {"scavo", "sbancamento", "terreni", "natura"}
tokens_b = {"scavo", "sbancamento", "qualsiasi", "terreno"}
similarity = jaccard_similarity(tokens_a, tokens_b)
# similarity = 2/6 = 0.333 (2 comuni: scavo, sbancamento)
```

**Uso in merge:**
```python
# Normalizza descrizione
desc_normalized = unidecode(descrizione.lower())
tokens = set(re.findall(r"\b\w{4,}\b", desc_normalized))

# Trova match
for voce_progetto in voci_progetto:
    similarity = jaccard_similarity(tokens, voce_progetto.tokens)
    if similarity > 0.6:  # Threshold
        return Match(voce_progetto, similarity)
```

---

## SemanticEmbeddingService

File: [services/nlp.py](../../backend/app/services/nlp.py) (~300 righe)

**Responsabilità**: Generazione embedding semantici per ricerca.

### Metodi Pubblici

#### 1. is_available

```python
def is_available(self) -> bool
```

Verifica se il servizio NLP è disponibile (modello caricato).

**Returns**: `True` se modello caricato, `False` se errore inizializzazione.

---

#### 2. embed_text

```python
def embed_text(self, text: str) -> list[float]
```

Genera embedding per un singolo testo.

**Returns**: Vector 384-dim L2-normalized.

**Esempio:**
```python
embedding = semantic_embedding_service.embed_text("Scavo di sbancamento in terreni")
print(f"Dimensione: {len(embedding)}")  # 384
print(f"Norma L2: {sum(x**2 for x in embedding)**0.5}")  # ~1.0
```

---

#### 3. embed_texts

```python
def embed_texts(self, texts: Sequence[str]) -> list[list[float]]
```

Genera embedding per batch di testi (più efficiente).

**Esempio:**
```python
texts = [
    "Scavo di sbancamento",
    "Fondazioni superficiali",
    "Strutture in c.a."
]
embeddings = semantic_embedding_service.embed_texts(texts)
# [[0.123, ...], [0.456, ...], [0.789, ...]]
```

---

#### 4. prepare_price_list_metadata

```python
def prepare_price_list_metadata(
    self,
    entry: Mapping[str, Any]
) -> dict[str, Any] | None
```

Prepara metadati embedding per voce elenco prezzi.

**Input:**
```python
entry = {
    "item_code": "A001.001",
    "item_description": "Scavo di sbancamento in terreni di qualsiasi natura",
    "wbs6_code": "A001",
    "wbs6_description": "Scavi",
    "wbs7_code": "A001.001",
    "wbs7_description": "Scavi di sbancamento",
    "price_lists": {"BASE": 12.50, "ALTO": 15.00}
}
```

**Output:**
```python
{
    "embedding": [0.123, 0.456, ..., 0.789],  # 384-dim
    "composed_text": "A001.001 Scavo di sbancamento in terreni di qualsiasi natura A001 Scavi A001.001 Scavi di sbancamento BASE ALTO"
}
```

**Composizione testo:**
```python
composed_text = " ".join([
    entry.get("item_code", ""),
    entry.get("item_description", ""),
    entry.get("wbs6_code", ""),
    entry.get("wbs6_description", ""),
    entry.get("wbs7_code", ""),
    entry.get("wbs7_description", ""),
    *entry.get("price_lists", {}).keys()
])
```

---

### Modello NLP

**Configurazione:**
```python
# core/config.py
nlp_model_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
nlp_execution_providers = ["CPUExecutionProvider"]
```

**Caratteristiche:**
- **Tipo**: SentenceTransformer (multilingual)
- **Dimensione embedding**: 384
- **Normalizzazione**: L2 (cosine similarity ready)
- **Max sequence length**: 128 tokens
- **Runtime**: ONNX (CPU-optimized)

**Lazy Initialization:**
```python
class SemanticEmbeddingService:
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._error: str | None = None

    def _ensure_model(self):
        if self._model is None and self._error is None:
            try:
                self._model = SentenceTransformer(
                    settings.nlp_model_id,
                    device="cpu"
                )
            except Exception as e:
                self._error = str(e)
                logger.error(f"Failed to load NLP model: {e}")
```

---

## PriceCatalogService

File: [services/price_catalog.py](../../backend/app/services/price_catalog.py) (~200 righe)

**Responsabilità**: Gestione elenco prezzi multi-commessa.

### Metodi Pubblici

#### 1. replace_catalog

```python
def replace_catalog(
    self,
    session: Session,
    commessa: Commessa,
    entries: Sequence[Mapping[str, Any]],
    source_file: str,
    preventivo_id: str | None,
    price_list_labels: dict[str, str] | None = None,
    preferred_lists: list[str] | None = None,
    base_list_keywords: list[str] | None = None
) -> None
```

Sostituisce l'elenco prezzi completo di una commessa (DELETE + INSERT bulk).

**Processo:**
1. **DELETE vecchio catalogo**
   ```python
   session.exec(delete(PriceListItem).where(
       PriceListItem.commessa_id == commessa.id
   ))
   ```

2. **Filtra listini preferiti**
   ```python
   preferred_lists = preferred_lists or []
   base_keywords = base_list_keywords or ["BASE", "LISTINO", "DEFAULT"]

   if not preferred_lists:
       # Auto-detect base list
       for list_id in entry["price_lists"].keys():
           if any(keyword in list_id.upper() for keyword in base_keywords):
               preferred_lists.append(list_id)
   ```

3. **Genera embedding**
   ```python
   embedding_data = self.embedding_service.prepare_price_list_metadata(entry)
   extra_metadata = {
       "embedding": embedding_data["embedding"],
       "composed_text": embedding_data["composed_text"]
   }
   ```

4. **Bulk insert**
   ```python
   items = []
   for entry in entries:
       item = PriceListItem(
           commessa_id=commessa.id,
           commessa_code=commessa.codice,
           product_id=entry["product_id"],
           global_code=f"{commessa.codice}#{entry['item_code']}",
           item_code=entry["item_code"],
           item_description=entry["item_description"],
           wbs6_code=entry.get("wbs6_code"),
           wbs7_code=entry.get("wbs7_code"),
           price_lists=filtered_price_lists,
           extra_metadata=extra_metadata,
           source_file=source_file,
           preventivo_id=preventivo_id
       )
       items.append(item)

   session.add_all(items)
   session.commit()
   ```

**Esempio:**
```python
price_catalog_service.replace_catalog(
    session,
    commessa=commessa,
    entries=[
        {
            "product_id": "PROD_001",
            "item_code": "A001.001",
            "item_description": "Scavo di sbancamento",
            "wbs6_code": "A001",
            "wbs6_description": "Scavi",
            "price_lists": {
                "BASE": 12.50,
                "ALTO": 15.00,
                "BASSO": 10.00
            }
        }
    ],
    source_file="preventivo.six",
    preventivo_id="PREV_001",
    preferred_lists=["BASE", "ALTO"]
)
```

---

## StorageService

File: [services/storage.py](../../backend/app/services/storage.py) (~248 righe)

**Responsabilità**: File management con validazione sicurezza.

### Metodi Pubblici

#### 1. commessa_dir

```python
def commessa_dir(self, commessa_id: int) -> Path
```

Recupera/crea directory storage per commessa.

**Returns**: `Path("storage/commessa_0001")`

---

#### 2. save_upload

```python
def save_upload(
    self,
    commessa_id: int,
    upload: UploadFile
) -> Path
```

Salva file uploadato con validazione sicurezza.

**Validazioni:**
1. **Estensione whitelist**
   ```python
   allowed_extensions = {".xlsx", ".xls", ".xlsm", ".six", ".xml"}
   if not any(filename.endswith(ext) for ext in allowed_extensions):
       raise ValueError("Estensione file non valida")
   ```

2. **Magic bytes**
   ```python
   EXCEL_MAGIC_BYTES = [
       b"\x50\x4B\x03\x04",  # ZIP (XLSX)
       b"\xD0\xCF\x11\xE0",  # OLE2 (XLS)
   ]
   if not any(file_bytes.startswith(magic) for magic in EXCEL_MAGIC_BYTES):
       raise ValueError("Formato file non valido")
   ```

3. **Limite dimensione**
   ```python
   max_size = settings.max_upload_size_mb * 1024 * 1024  # Default: 15MB
   if total_bytes > max_size:
       raise ValueError("File troppo grande")
   ```

4. **Path traversal prevention**
   ```python
   sanitized_filename = Path(filename).name  # Rimuovi path components
   ```

**Processo:**
```python
# 1. Crea directory
dir_path = self.commessa_dir(commessa_id)
dir_path.mkdir(parents=True, exist_ok=True)

# 2. Sanitizza nome
sanitized_filename = secure_filename(upload.filename)
timestamp = int(time.time())
safe_filename = f"{timestamp}_{sanitized_filename}"

# 3. Stream upload (chunk-based)
file_path = dir_path / safe_filename
with open(file_path, "wb") as f:
    while chunk := await upload.read(64 * 1024):  # 64KB chunks
        if total_bytes > max_size:
            f.close()
            file_path.unlink()
            raise ValueError("File troppo grande")
        f.write(chunk)
        total_bytes += len(chunk)

# 4. Valida magic bytes
validate_magic_bytes(file_path)

return file_path
```

---

#### 3. delete_file

```python
def delete_file(self, file_path: str | Path | None) -> bool
```

Elimina file in modo sicuro.

**Returns**: `True` se eliminato, `False` se non esisteva.

---

#### 4. delete_commessa_dir

```python
def delete_commessa_dir(self, commessa_id: int) -> None
```

Elimina directory commessa (se vuota).

---

### Magic Bytes Supported

```python
MAGIC_BYTES_MAP = {
    b"\x50\x4B\x03\x04": [".xlsx", ".xlsm", ".six"],  # ZIP-based
    b"\xD0\xCF\x11\xE0": [".xls"],                    # OLE2
    b"\x3C\x3F\x78\x6D": [".xml"],                    # XML (<?xml)
}
```

---

## WbsImportService

File: [services/wbs_import.py](../../backend/app/services/wbs_import.py) (~500 righe)

**Responsabilità**: Import WBS da Excel con upsert intelligente.

### Metodi Pubblici

#### 1. import_from_upload

```python
def import_from_upload(
    self,
    session: Session,
    commessa: Commessa,
    file_bytes: bytes,
    mode: Literal["create", "update"] = "update"
) -> WbsImportStatsSchema
```

Importa WBS da Excel (formato flessibile).

**Formato Excel Atteso:**

| WBS1_CODE | WBS1_DESC | WBS2_CODE | WBS2_DESC | ... | WBS6_CODE | WBS6_DESC | WBS7_CODE | WBS7_DESC |
|-----------|-----------|-----------|-----------|-----|-----------|-----------|-----------|-----------|
| P00 | Edificio | L00 | Piano Int. | ... | A001 | Scavi | A001.001 | Scavi sbancamento |
| P00 | Edificio | L00 | Piano Int. | ... | A001 | Scavi | A001.002 | Scavi fondazione |

**Header Aliases (case-insensitive):**
```python
ALIASES = {
    "wbs1_code": ["WBS1", "WBS_1_CODE", "LIVELLO1_CODICE"],
    "wbs1_description": ["WBS1_DESC", "WBS_1_DESCRIPTION", "LIVELLO1_DESC"],
    # ... fino a WBS7
}
```

**Processo:**
1. **Parse Excel**
   ```python
   wb = openpyxl.load_workbook(BytesIO(file_bytes))
   ws = wb.active
   headers = detect_headers(ws)
   ```

2. **Iterate rows**
   ```python
   for row in ws.iter_rows(min_row=2, values_only=True):
       # Estrai WBS1-5 (spaziali)
       for level in range(1, 6):
           code = row[headers[f"wbs{level}_code"]]
           description = row[headers[f"wbs{level}_description"]]
           if code:
               upsert_wbs_spaziale(session, commessa, level, code, description, parent_id)

       # Estrai WBS6
       wbs6_code = row[headers["wbs6_code"]]
       wbs6_description = row[headers["wbs6_description"]]
       if wbs6_code:
           upsert_wbs6(session, commessa, wbs6_code, wbs6_description, parent_wbs5_id)

       # Estrai WBS7
       wbs7_code = row[headers["wbs7_code"]]
       wbs7_description = row[headers["wbs7_description"]]
       if wbs7_code and wbs6_id:
           upsert_wbs7(session, commessa, wbs6_id, wbs7_code, wbs7_description)
   ```

3. **Upsert Logic**
   ```python
   def upsert_wbs6(session, commessa, code, description, parent_id):
       wbs6 = session.exec(
           select(Wbs6).where(
               Wbs6.commessa_id == commessa.id,
               Wbs6.code == code
           )
       ).first()

       if wbs6:
           # Update
           wbs6.description = description
           wbs6.wbs_spaziale_id = parent_id
           stats.wbs6_updated += 1
       else:
           # Insert
           wbs6 = Wbs6(
               commessa_id=commessa.id,
               code=code,
               description=description,
               label=f"{code} - {description}",
               wbs_spaziale_id=parent_id
           )
           session.add(wbs6)
           stats.wbs6_inserted += 1

       return wbs6
   ```

**Returns:**
```python
WbsImportStatsSchema(
    rows_total=150,
    spaziali_inserted=30,
    spaziali_updated=5,
    wbs6_inserted=80,
    wbs6_updated=10,
    wbs7_inserted=120,
    wbs7_updated=15
)
```

---

#### 2. fetch_commessa_wbs

```python
def fetch_commessa_wbs(
    self,
    session: Session,
    commessa_id: int
) -> tuple[list[WbsSpaziale], list[Wbs6], list[Wbs7]]
```

Recupera WBS completa per commessa.

**Returns**: `(spaziali, wbs6, wbs7)`

---

#### 3. update_spatial_node

```python
def update_spatial_node(
    self,
    session: Session,
    commessa_id: int,
    node_id: int,
    code: str | None = None,
    description: str | None = None,
    importo_totale: float | None = None,
    parent_id: int | None = None,
    level: int | None = None
) -> WbsSpaziale
```

Aggiorna nodo WBS spaziale (partial update).

**Nota**: Aggiorna `updated_at` per VoceComputo correlate (cache invalidation).

---

## WbsVisibilityService

File: [services/wbs_visibility.py](../../backend/app/services/wbs_visibility.py) (~150 righe)

**Responsabilità**: Gestione visibilità nodi WBS.

### Metodi Pubblici

#### 1. list_visibility

```python
def list_visibility(
    self,
    session: Session,
    commessa_id: int
) -> list[WbsVisibilityEntry]
```

Recupera preferenze visibilità per tutti i nodi WBS.

**Returns:**
```python
[
    WbsVisibilityEntry(
        level=6,
        node_id=1,
        code="A001",
        description="Scavi",
        hidden=True
    )
]
```

---

#### 2. update_visibility

```python
def update_visibility(
    self,
    session: Session,
    commessa_id: int,
    updates: Iterable[tuple[int, int, bool]]
) -> list[WbsVisibilityEntry]
```

Aggiorna visibilità batch.

**Input:**
```python
updates = [
    (6, 1, True),   # Nascondi WBS6 id=1
    (6, 2, False),  # Mostra WBS6 id=2
    (7, 5, True),   # Nascondi WBS7 id=5
]
```

**Logica:**
```python
for level, node_id, hidden in updates:
    visibility = session.exec(
        select(WbsVisibility).where(
            WbsVisibility.commessa_id == commessa_id,
            WbsVisibility.kind == map_level_to_kind(level),
            WbsVisibility.node_id == node_id
        )
    ).first()

    if hidden:
        if not visibility:
            # Crea record hidden
            visibility = WbsVisibility(
                commessa_id=commessa_id,
                kind=map_level_to_kind(level),
                node_id=node_id,
                hidden=True
            )
            session.add(visibility)
    else:
        if visibility:
            # Rimuovi record (default: visible)
            session.delete(visibility)
```

---

#### 3. hidden_codes_by_level

```python
def hidden_codes_by_level(
    self,
    session: Session,
    commessa_id: int
) -> dict[int, set[str]]
```

Genera lookup set di codici nascosti per livello.

**Returns:**
```python
{
    1: {"P01", "P03"},       # WBS spaziale L1
    2: {"L05"},              # WBS spaziale L2
    6: {"A001", "B234"},     # WBS6
    7: {"A001.001"}          # WBS7
}
```

**Uso in Analysis:**
```python
hidden_codes = visibility_service.hidden_codes_by_level(session, commessa_id)

# Filtra voci
voci_visibili = [
    v for v in voci
    if v.wbs_6_code not in hidden_codes.get(6, set())
    and v.wbs_7_code not in hidden_codes.get(7, set())
]
```

---

## Pattern e Best Practices

### 1. Singleton Services

**Definizione (module-level):**
```python
# services/__init__.py
import_service = ImportService()
six_import_service = SixImportService(import_service, price_catalog_service)
semantic_embedding_service = SemanticEmbeddingService()
price_catalog_service = PriceCatalogService(semantic_embedding_service)
storage_service = StorageService(settings.storage_root)
```

**Rationale:**
- Services stateless (no instance state)
- Evita re-inizializzazione costosa (es: NLP model loading)
- Dependency injection semplificata

---

### 2. Session Management

**Caller gestisce transazioni:**
```python
# BAD: Service non deve fare commit
def my_service_method(session):
    session.add(entity)
    session.commit()  # ❌ Non fare!

# GOOD: Caller gestisce commit
def my_service_method(session):
    session.add(entity)
    session.flush()  # OK: rende entity.id disponibile
    return entity

# Route handler
@router.post("/")
def create_something(session: Session = Depends(get_session)):
    result = my_service_method(session)
    session.commit()  # ✅ Commit gestito dalla route
    return result
```

**Eccezioni:** Servizi complessi con nested transactions (es: SixImportService usa savepoints).

---

### 3. Error Handling

**Service lancia eccezioni business:**
```python
# Service
class PreventivoSelectionError(Exception):
    pass

def import_six_file(...):
    if preventivo_id and preventivo not in preventivi:
        raise PreventivoSelectionError(f"Preventivo {preventivo_id} non trovato")

# Route
@router.post("/")
def import_six(session: Session, ...):
    try:
        result = six_import_service.import_six_file(...)
    except PreventivoSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
```

---

### 4. Bulk Operations

**Preferire bulk insert/delete:**
```python
# BAD: N queries
for item in items:
    session.add(item)
    session.commit()

# GOOD: 1 query
session.add_all(items)
session.commit()
```

**Bulk delete:**
```python
# GOOD
session.exec(delete(VoceComputo).where(VoceComputo.computo_id == computo_id))
session.commit()
```

---

### 5. Caching e Lazy Loading

**Esempio: WbsNormalizeContext**
```python
class WbsNormalizeContext:
    def __init__(self, session, commessa_id):
        self._wbs6_cache: dict[str, int] = {}
        self._wbs7_cache: dict[tuple[int, str], int] = {}

    def get_or_create_wbs6(self, code, description):
        if code in self._wbs6_cache:
            return self._wbs6_cache[code]

        wbs6 = session.exec(
            select(Wbs6).where(Wbs6.commessa_id == self.commessa_id, Wbs6.code == code)
        ).first()

        if not wbs6:
            wbs6 = Wbs6(...)
            session.add(wbs6)
            session.flush()

        self._wbs6_cache[code] = wbs6.id
        return wbs6.id
```

---

### 6. Logging

**Pattern comune:**
```python
import logging

logger = logging.getLogger(__name__)

def my_service_method(...):
    logger.info(f"Starting import for commessa {commessa_id}")
    try:
        result = process()
        logger.info(f"Import completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise
```

---

## Diagramma Dipendenze Servizi

```
┌─────────────────────┐
│  StorageService     │  (no dependencies)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CommesseService     │
│  └─ storage_service │
└─────────────────────┘

┌─────────────────────┐
│ SemanticEmbedding    │  (no dependencies)
│ Service             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PriceCatalog        │
│ Service             │
│  └─ semantic_embedding_svc   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SixImportService    │
│  ├─ import_service  │
│  └─ price_catalog   │
└─────────────────────┘

┌─────────────────────┐
│ ImportService       │
│  └─ commesse_svc    │
└─────────────────────┘

┌─────────────────────┐
│ WbsVisibility       │  (no dependencies)
│ Service             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ AnalysisService     │
│  └─ visibility_svc  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ InsightsService     │
│  └─ visibility_svc  │
└─────────────────────┘

┌─────────────────────┐
│ WbsImportService    │  (no dependencies)
└─────────────────────┘
```

---

## Prossimi Passi

- [Parser Excel](./06-PARSER-EXCEL.md) - Logica parsing computi Excel
- [STR Vision Parser](./07-SIX-PARSER.md) - Parser XML STR Vision
- [Testing](./08-TESTING.md) - Unit e integration tests
