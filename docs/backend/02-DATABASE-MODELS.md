# Database Models - Documentazione Completa

## Indice
- [Panoramica](#panoramica)
- [Modelli Core](#modelli-core)
- [Modelli WBS](#modelli-wbs)
- [Enumerazioni](#enumerazioni)
- [Relazioni e Diagrammi ERD](#relazioni-e-diagrammi-erd)
- [Indici e Constraints](#indici-e-constraints)
- [Esempi d'Uso](#esempi-duso)

## Panoramica

Il database utilizza **SQLModel** (combinazione di SQLAlchemy + Pydantic) per definire i modelli. Ci sono due file principali:

- **[models.py](../../backend/app/db/models.py)** (~246 righe): Modelli core (Commessa, Computo, VoceComputo, PriceListItem, Settings, ImportConfig)
- **[models_wbs.py](../../backend/app/db/models_wbs.py)** (~246 righe): Modelli WBS normalizzati (WbsSpaziale, Wbs6, Wbs7, Voce, VoceProgetto, VoceOfferta)

### Architettura del Database

```
┌─────────────────────────────────────────────┐
│           CORE MODELS (models.py)           │
│  - Commessa (container principale)         │
│  - Computo (progetto/ritorno)              │
│  - VoceComputo (voci denormalizzate)       │
│  - PriceListItem (elenco prezzi)           │
│  - Settings (configurazione globale)       │
│  - ImportConfig (template import)          │
│  - CommessaPreferences (preferenze)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        WBS MODELS (models_wbs.py)           │
│  - WbsSpaziale (livelli 1-5 gerarchici)    │
│  - Wbs6 (categorie merceologiche A###)     │
│  - Wbs7 (raggruppatori EPU A###.###)       │
│  - WbsVisibility (preferenze visibilità)   │
│  - Impresa (anagrafica normalizzata)       │
│  - Voce (voci normalizzate)                │
│  - VoceProgetto (prezzi progetto)          │
│  - VoceOfferta (prezzi offerte)            │
└─────────────────────────────────────────────┘
```

## Modelli Core

### 1. Commessa

**File:** [models.py:35-38](../../backend/app/db/models.py#L35-L38)

**Descrizione:** Entità principale che rappresenta una commessa/gara d'appalto.

```python
class Commessa(CommessaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CommessaBase(SQLModel):
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato = Field(default=CommessaStato.setup)
```

#### Campi

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `id` | int | No | Chiave primaria auto-incrementale |
| `nome` | str | No | Nome descrittivo della commessa |
| `codice` | str | No | Codice univoco identificativo |
| `descrizione` | str | Si | Descrizione estesa della commessa |
| `note` | str | Si | Note libere |
| `business_unit` | str | Si | Business unit / divisione aziendale |
| `revisione` | str | Si | Versione/revisione commessa |
| `stato` | CommessaStato | No | Stato operativo (setup/in_corso/chiusa) |
| `created_at` | datetime | No | Data creazione record |
| `updated_at` | datetime | No | Data ultimo aggiornamento |

#### Relazioni

- **1-to-Many** → `Computo` (computi progetto e ritorni)
- **1-to-Many** → `VoceComputo` (tutte le voci dei computi)
- **1-to-Many** → `WbsSpaziale` (nodi WBS spaziali)
- **1-to-Many** → `Wbs6` (categorie merceologiche)
- **1-to-Many** → `PriceListItem` (elenco prezzi)
- **1-to-One** → `CommessaPreferences` (preferenze)
- **1-to-Many** → `ImportConfig` (configurazioni import)

#### Esempio

```python
commessa = Commessa(
    nome="Nuovo Ospedale Milano",
    codice="OSP-MI-2025",
    descrizione="Costruzione nuovo polo ospedaliero",
    business_unit="Healthcare",
    revisione="Rev. 02",
    stato=CommessaStato.in_corso
)
session.add(commessa)
session.commit()
```

---

### 2. Computo

**File:** [models.py:60-65](../../backend/app/db/models.py#L60-L65)

**Descrizione:** Rappresenta un computo metrico (progetto) o un ritorno di gara (offerta).

```python
class Computo(ComputoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ComputoBase(SQLModel):
    nome: str
    tipo: ComputoTipo  # "progetto" | "ritorno"
    impresa: Optional[str] = None
    file_nome: Optional[str] = None
    file_percorso: Optional[str] = None
    round_number: Optional[int] = None
    importo_totale: Optional[float] = None
    delta_vs_progetto: Optional[float] = None
    percentuale_delta: Optional[float] = None
    note: Optional[str] = None
```

#### Campi

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `id` | int | No | Chiave primaria |
| `commessa_id` | int | No | FK → Commessa |
| `commessa_code` | str | Si (indexed) | Codice commessa denormalizzato |
| `nome` | str | No | Nome del computo (es: "Commessa XYZ - Progetto") |
| `tipo` | ComputoTipo | No | `progetto` o `ritorno` |
| `impresa` | str | Si | Nome impresa (solo per ritorni) |
| `file_nome` | str | Si | Nome file originale caricato |
| `file_percorso` | str | Si | Path file salvato in storage |
| `round_number` | int | Si | Numero round gara (solo ritorni) |
| `importo_totale` | float | Si | Somma importi di tutte le voci |
| `delta_vs_progetto` | float | Si | Delta assoluto rispetto progetto |
| `percentuale_delta` | float | Si | Delta percentuale rispetto progetto |
| `note` | str | Si | Note libere |

#### Relazioni

- **Many-to-One** → `Commessa`
- **1-to-Many** → `VoceComputo` (voci del computo)

#### Esempio: Computo Progetto

```python
computo_progetto = Computo(
    commessa_id=1,
    commessa_code="OSP-MI-2025",
    nome="Ospedale Milano - Computo Progetto",
    tipo=ComputoTipo.progetto,
    file_nome="computo_progetto_rev02.xlsx",
    file_percorso="storage/commessa_0001/computo_progetto_rev02.xlsx",
    importo_totale=15_000_000.00,
)
```

#### Esempio: Computo Ritorno

```python
computo_ritorno = Computo(
    commessa_id=1,
    commessa_code="OSP-MI-2025",
    nome="Ospedale Milano - Offerta Impresa ABC",
    tipo=ComputoTipo.ritorno,
    impresa="Impresa ABC S.p.A.",
    round_number=1,
    file_nome="offerta_impresa_abc_round1.xlsx",
    file_percorso="storage/commessa_0001/offerta_impresa_abc.xlsx",
    importo_totale=14_250_000.00,
    delta_vs_progetto=-750_000.00,
    percentuale_delta=-5.0,
)
```

---

### 3. VoceComputo

**File:** [models.py:101-109](../../backend/app/db/models.py#L101-L109)

**Descrizione:** Voce di computo con 7 livelli WBS denormalizzati (approccio legacy/flat).

```python
class VoceComputo(VoceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(default=None, foreign_key="commessa.id")
    commessa_code: Optional[str] = Field(default=None, index=True)
    computo_id: int = Field(foreign_key="computo.id")
    global_code: Optional[str] = Field(default=None, index=True)
    extra_metadata: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )

class VoceBase(SQLModel):
    progressivo: Optional[int] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    ordine: int = Field(default=0)

    # WBS levels (7 livelli)
    wbs_1_code: Optional[str] = None
    wbs_1_description: Optional[str] = None
    wbs_2_code: Optional[str] = None
    wbs_2_description: Optional[str] = None
    wbs_3_code: Optional[str] = None
    wbs_3_description: Optional[str] = None
    wbs_4_code: Optional[str] = None
    wbs_4_description: Optional[str] = None
    wbs_5_code: Optional[str] = None
    wbs_5_description: Optional[str] = None
    wbs_6_code: Optional[str] = None
    wbs_6_description: Optional[str] = None
    wbs_7_code: Optional[str] = None
    wbs_7_description: Optional[str] = None
```

#### Campi Principali

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `id` | int | No | Chiave primaria |
| `computo_id` | int | No | FK → Computo |
| `commessa_id` | int | Si | FK → Commessa (denorm.) |
| `commessa_code` | str | Si (indexed) | Codice commessa (denorm.) |
| `global_code` | str | Si (indexed) | Codice globale multi-commessa |
| `progressivo` | int | Si | Numero progressivo voce originale |
| `codice` | str | Si | Codice articolo/voce |
| `descrizione` | str | Si | Descrizione estesa della voce |
| `unita_misura` | str | Si | Unità di misura (es: "m²", "ml", "cad") |
| `quantita` | float | Si | Quantità |
| `prezzo_unitario` | float | Si | Prezzo unitario (€) |
| `importo` | float | Si | Importo totale = quantità × prezzo_unitario |
| `note` | str | Si | Note libere |
| `ordine` | int | No | Ordinamento voce nel computo |
| `extra_metadata` | dict | Si (JSON) | Metadati extra (es: embedding, tags) |

#### Campi WBS (7 Livelli)

| Livello | Campi | Descrizione |
|---------|-------|-------------|
| WBS 1 | `wbs_1_code`, `wbs_1_description` | Lotto / Edificio |
| WBS 2 | `wbs_2_code`, `wbs_2_description` | Livelli / Piani |
| WBS 3 | `wbs_3_code`, `wbs_3_description` | Ambiti Omogenei |
| WBS 4 | `wbs_4_code`, `wbs_4_description` | Appalto / Fase |
| WBS 5 | `wbs_5_code`, `wbs_5_description` | Elementi Funzionali |
| WBS 6 | `wbs_6_code`, `wbs_6_description` | Categorie Merceologiche (A###) |
| WBS 7 | `wbs_7_code`, `wbs_7_description` | Raggruppatori EPU (A###.###) |

#### Esempio

```python
voce = VoceComputo(
    computo_id=1,
    commessa_id=1,
    commessa_code="OSP-MI-2025",
    progressivo=1,
    codice="A001.001",
    descrizione="Scavo di sbancamento in terreni di qualsiasi natura",
    unita_misura="m³",
    quantita=1500.0,
    prezzo_unitario=12.50,
    importo=18_750.00,
    ordine=1,

    # WBS Spaziale
    wbs_1_code="P00",
    wbs_1_description="Lotto 1 - Edificio Principale",
    wbs_2_code="L00",
    wbs_2_description="Piano Interrato",
    wbs_3_code="AO01",
    wbs_3_description="Opere di fondazione",
    wbs_4_code="F01",
    wbs_4_description="Fase 1 - Opere preliminari",
    wbs_5_code="EL001",
    wbs_5_description="Scavi e sbancamenti",

    # WBS Analitica
    wbs_6_code="A001",
    wbs_6_description="Scavi",
    wbs_7_code="A001.001",
    wbs_7_description="Scavi di sbancamento",

    global_code="OSP-MI-2025#A001.001",
)
```

---

### 4. PriceListItem

**File:** [models.py:117-157](../../backend/app/db/models.py#L117-L157)

**Descrizione:** Voce dell'elenco prezzi importata da STR Vision, arricchita con metadati e embedding.

```python
class PriceListItem(SQLModel, table=True):
    __tablename__ = "price_list_item"
    __table_args__ = (
        UniqueConstraint("commessa_id", "product_id",
                        name="uq_price_list_item_commessa_product"),
        UniqueConstraint("global_code",
                        name="uq_price_list_item_global_code"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    commessa_code: str = Field(index=True)
    product_id: str = Field(description="ID originale prodotto STR Vision")
    global_code: str = Field(description="Codice commessa+prodotto", index=True)
    item_code: str = Field(description="Codice visualizzato", index=True)
    item_description: Optional[str] = None
    unit_id: Optional[str] = None
    unit_label: Optional[str] = None
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    wbs7_code: Optional[str] = None
    wbs7_description: Optional[str] = None
    price_lists: Optional[dict[str, float]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    extra_metadata: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    source_file: Optional[str] = None
    preventivo_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Campi

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `id` | int | No | Chiave primaria |
| `commessa_id` | int | No | FK → Commessa |
| `commessa_code` | str | No (indexed) | Codice commessa |
| `product_id` | str | No | ID originale prodotto da STR Vision |
| `global_code` | str | No (indexed, unique) | Codice univoco globale |
| `item_code` | str | No (indexed) | Codice visualizzato nel prezzario |
| `item_description` | str | Si | Descrizione prodotto |
| `unit_id` | str | Si | ID unità di misura |
| `unit_label` | str | Si | Etichetta unità (es: "m²", "cad") |
| `wbs6_code` | str | Si | Codice WBS6 associato |
| `wbs6_description` | str | Si | Descrizione WBS6 |
| `wbs7_code` | str | Si | Codice WBS7 associato |
| `wbs7_description` | str | Si | Descrizione WBS7 |
| `price_lists` | dict[str,float] | Si (JSON) | Prezzi per listino {"BASE": 12.50, "ALTO": 15.00} |
| `extra_metadata` | dict | Si (JSON) | Metadati extra (embedding, tags, ecc.) |
| `source_file` | str | Si | File STR Vision di origine |
| `preventivo_id` | str | Si | ID preventivo STR Vision |

#### Esempio

```python
item = PriceListItem(
    commessa_id=1,
    commessa_code="OSP-MI-2025",
    product_id="PROD_12345",
    global_code="OSP-MI-2025#A001.001",
    item_code="A001.001",
    item_description="Scavo di sbancamento in terreni di qualsiasi natura",
    unit_id="m3",
    unit_label="m³",
    wbs6_code="A001",
    wbs6_description="Scavi",
    wbs7_code="A001.001",
    wbs7_description="Scavi di sbancamento",
    price_lists={
        "BASE": 12.50,
        "ALTO": 15.00,
        "BASSO": 10.00,
    },
    extra_metadata={
        "embedding": [0.123, 0.456, ...],  # 384-dim vector
        "tags": ["scavo", "movimento terra"],
    },
    source_file="preventivo_rev02.six",
    preventivo_id="PREV_001",
)
```

---

### 5. Settings

**File:** [models.py:169-172](../../backend/app/db/models.py#L169-L172)

**Descrizione:** Impostazioni globali singleton per soglie di criticità e analisi.

```python
class Settings(SettingsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SettingsBase(SQLModel):
    delta_minimo_critico: float = -30000.0
    delta_massimo_critico: float = 1000.0
    percentuale_cme_alto: float = 25.0
    percentuale_cme_basso: float = 50.0
    criticita_media_percent: float = 25.0
    criticita_alta_percent: float = 50.0
```

#### Campi

| Campo | Tipo | Default | Descrizione |
|-------|------|---------|-------------|
| `delta_minimo_critico` | float | -30000.0 | Soglia minima delta critico (€) |
| `delta_massimo_critico` | float | 1000.0 | Soglia massima delta critico (€) |
| `percentuale_cme_alto` | float | 25.0 | % CME alto |
| `percentuale_cme_basso` | float | 50.0 | % CME basso |
| `criticita_media_percent` | float | 25.0 | Soglia criticità media (%) |
| `criticita_alta_percent` | float | 50.0 | Soglia criticità alta (%) |

#### Uso

```python
# Recupera settings (singleton)
settings = session.exec(select(Settings)).first()
if not settings:
    settings = Settings()  # Usa default
    session.add(settings)
    session.commit()

# Classifica criticità
def classify_criticita(delta_percent: float) -> str:
    if abs(delta_percent) >= settings.criticita_alta_percent:
        return "alta"
    elif abs(delta_percent) >= settings.criticita_media_percent:
        return "media"
    return "bassa"
```

---

### 6. ImportConfig

**File:** [models.py:193-200](../../backend/app/db/models.py#L193-L200)

**Descrizione:** Configurazione salvata per import personalizzati (formati Excel custom).

```python
class ImportConfig(ImportConfigBase, table=True):
    __tablename__ = "import_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: Optional[int] = Field(
        default=None,
        foreign_key="commessa.id",
        description="Commessa associata (null = globale)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ImportConfigBase(SQLModel):
    nome: str = Field(description="Nome descrittivo")
    impresa: Optional[str] = None
    sheet_name: Optional[str] = None
    code_columns: Optional[str] = None  # es: "A,B"
    description_columns: Optional[str] = None
    price_column: Optional[str] = None
    quantity_column: Optional[str] = None
    note: Optional[str] = None
```

#### Campi

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `id` | int | No | Chiave primaria |
| `commessa_id` | int | Si | FK → Commessa (null = config globale) |
| `nome` | str | No | Nome descrittivo (es: "Formato Impresa XYZ") |
| `impresa` | str | Si | Impresa associata |
| `sheet_name` | str | Si | Nome foglio Excel |
| `code_columns` | str | Si | Colonne codice (es: "A,B") |
| `description_columns` | str | Si | Colonne descrizione |
| `price_column` | str | Si | Colonna prezzo unitario |
| `quantity_column` | str | Si | Colonna quantità |
| `note` | str | Si | Note sulla configurazione |

#### Esempio

```python
config = ImportConfig(
    commessa_id=None,  # Globale
    nome="Formato Impresa ABC",
    impresa="Impresa ABC S.p.A.",
    sheet_name="Offerta Economica",
    code_columns="A,B",  # Concatena colonne A e B
    description_columns="C,D",
    price_column="E",
    quantity_column="F",
    note="Formato standard utilizzato da Impresa ABC",
)
```

---

### 7. CommessaPreferences

**File:** [models.py:231-238](../../backend/app/db/models.py#L231-L238)

**Descrizione:** Preferenze e impostazioni specifiche per commessa.

```python
class CommessaPreferences(CommessaPreferencesBase, table=True):
    __tablename__ = "commessa_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(
        foreign_key="commessa.id",
        unique=True,
        description="Commessa di riferimento"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CommessaPreferencesBase(SQLModel):
    selected_preventivo_id: Optional[str] = None
    selected_price_list_id: Optional[str] = None
    default_wbs_view: Optional[str] = None  # "spaziale" | "wbs6" | "wbs7"
    custom_settings: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
```

#### Esempio

```python
prefs = CommessaPreferences(
    commessa_id=1,
    selected_preventivo_id="PREV_001",
    selected_price_list_id="BASE",
    default_wbs_view="wbs6",
    custom_settings={
        "theme": "dark",
        "show_advanced_filters": True,
    }
)
```

---

## Modelli WBS

### 8. WbsSpaziale

**File:** [models_wbs.py:22-46](../../backend/app/db/models_wbs.py#L22-L46)

**Descrizione:** Nodo spaziale della WBS (livelli 1-5) normalizzato per commessa.

```python
class WbsSpaziale(SQLModel, table=True):
    __tablename__ = "wbs_spaziale"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id", "level", "code",
            name="uq_wbs_spaziale_commessa_level_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="wbs_spaziale.id")
    level: int = Field(description="Livello WBS (1-5)")
    code: str = Field(description="Codice del nodo (es. P00)")
    description: Optional[str] = None
    importo_totale: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Gerarchia WBS Spaziale (Livelli 1-5)

| Livello | Descrizione | Esempio Codice | Esempio Descrizione |
|---------|-------------|----------------|---------------------|
| 1 | Lotto / Edificio | P00 | Edificio Principale |
| 2 | Livelli / Piani | L00, L01 | Piano Interrato, Piano Terra |
| 3 | Ambiti Omogenei | AO01, AO02 | Opere di fondazione, Strutture |
| 4 | Appalto / Fase | F01, F02 | Fase 1 - Preliminari, Fase 2 - Strutture |
| 5 | Elementi Funzionali | EL001, EL002 | Scavi, Fondazioni superficiali |

#### Esempio Gerarchia

```python
# Livello 1: Lotto
edificio = WbsSpaziale(
    commessa_id=1,
    parent_id=None,
    level=1,
    code="P00",
    description="Edificio Principale",
)

# Livello 2: Piano
piano_interrato = WbsSpaziale(
    commessa_id=1,
    parent_id=edificio.id,
    level=2,
    code="L00",
    description="Piano Interrato",
)

# Livello 3: Ambito
fondazioni = WbsSpaziale(
    commessa_id=1,
    parent_id=piano_interrato.id,
    level=3,
    code="AO01",
    description="Opere di fondazione",
)

# Livello 4: Fase
fase_preliminare = WbsSpaziale(
    commessa_id=1,
    parent_id=fondazioni.id,
    level=4,
    code="F01",
    description="Fase 1 - Opere preliminari",
)

# Livello 5: Elemento Funzionale
scavi = WbsSpaziale(
    commessa_id=1,
    parent_id=fase_preliminare.id,
    level=5,
    code="EL001",
    description="Scavi e sbancamenti",
)
```

---

### 9. Wbs6

**File:** [models_wbs.py:49-72](../../backend/app/db/models_wbs.py#L49-L72)

**Descrizione:** Nodo analitico WBS6 (codice A### obbligatorio). **Pivot principale** per aggregazioni.

```python
class Wbs6(SQLModel, table=True):
    __tablename__ = "wbs6"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id", "code",
            name="uq_wbs6_commessa_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    wbs_spaziale_id: Optional[int] = Field(
        default=None,
        foreign_key="wbs_spaziale.id",
        description="Nodo spaziale foglia associato (livello 5)",
    )
    code: str = Field(description="Codice WBS6 (formato A###)")
    description: str = Field(description="Descrizione categoria")
    label: str = Field(description="Etichetta normalizzata (CODE - DESCRIPTION)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Caratteristiche

- **Formato codice**: 1 lettera + 3 cifre (es: `A001`, `B234`, `Z999`)
- **Pivot analitico**: Tutte le voci di progetto e offerte si agganciano a WBS6
- **Label normalizzato**: Formato `{CODE} - {DESCRIPTION}` (es: "A001 - Scavi")

#### Esempio

```python
wbs6_scavi = Wbs6(
    commessa_id=1,
    wbs_spaziale_id=scavi.id,  # Collegamento a livello 5 spaziale
    code="A001",
    description="Scavi",
    label="A001 - Scavi",
)

wbs6_strutture = Wbs6(
    commessa_id=1,
    wbs_spaziale_id=strutture.id,
    code="B001",
    description="Strutture in c.a.",
    label="B001 - Strutture in c.a.",
)
```

---

### 10. Wbs7

**File:** [models_wbs.py:75-102](../../backend/app/db/models_wbs.py#L75-L102)

**Descrizione:** Nodo opzionale WBS7 (sotto-articolazione della WBS6).

```python
class Wbs7(SQLModel, table=True):
    __tablename__ = "wbs7"
    __table_args__ = (
        UniqueConstraint(
            "wbs6_id", "code",
            name="uq_wbs7_wbs6_code",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    wbs6_id: int = Field(foreign_key="wbs6.id")
    code: Optional[str] = Field(
        default=None,
        description="Codice WBS7 (A###.### o A###_###)",
    )
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Formato Codice

- **Standard**: `A###.###` (es: `A001.001`, `B234.050`)
- **Alternativo**: `A###_###` (es: `A001_001`)

#### Esempio

```python
wbs7_scavi_sbancamento = Wbs7(
    commessa_id=1,
    wbs6_id=wbs6_scavi.id,
    code="A001.001",
    description="Scavi di sbancamento",
)

wbs7_scavi_fondazione = Wbs7(
    commessa_id=1,
    wbs6_id=wbs6_scavi.id,
    code="A001.002",
    description="Scavi per fondazioni",
)
```

---

### 11. WbsVisibility

**File:** [models_wbs.py:111-133](../../backend/app/db/models_wbs.py#L111-L133)

**Descrizione:** Preferenze di visibilità per nodi WBS (hide/show).

```python
class WbsVisibilityKind(str, Enum):
    spaziale = "spaziale"
    wbs6 = "wbs6"
    wbs7 = "wbs7"

class WbsVisibility(SQLModel, table=True):
    __tablename__ = "wbs_visibility"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id", "kind", "node_id",
            name="uq_wbs_visibility_commessa_node",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    kind: WbsVisibilityKind
    node_id: int = Field(description="ID del nodo nascosto")
    hidden: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Esempio

```python
# Nascondi nodo WBS6 "A001 - Scavi"
visibility = WbsVisibility(
    commessa_id=1,
    kind=WbsVisibilityKind.wbs6,
    node_id=wbs6_scavi.id,
    hidden=True,
)

# Nascondi nodo spaziale "P00 - Edificio Principale"
visibility_spaziale = WbsVisibility(
    commessa_id=1,
    kind=WbsVisibilityKind.spaziale,
    node_id=edificio.id,
    hidden=True,
)
```

---

### 12. Voce, VoceProgetto, VoceOfferta

**File:** [models_wbs.py:155-245](../../backend/app/db/models_wbs.py#L155-L245)

**Descrizione:** Modelli normalizzati per voci (evoluzione di VoceComputo).

#### 12.1 Voce (Anagrafica Normalizzata)

```python
class Voce(SQLModel, table=True):
    __tablename__ = "voce"
    __table_args__ = (
        UniqueConstraint(
            "commessa_id", "wbs6_id", "codice", "ordine",
            name="uq_voce_commessa_wbs6_codice_ordine",
        ),
        UniqueConstraint(
            "legacy_vocecomputo_id",
            name="uq_voce_legacy",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    commessa_id: int = Field(foreign_key="commessa.id")
    wbs6_id: int = Field(foreign_key="wbs6.id")
    wbs7_id: Optional[int] = Field(default=None, foreign_key="wbs7.id")
    legacy_vocecomputo_id: Optional[int] = Field(
        default=None,
        foreign_key="vocecomputo.id",
    )
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    note: Optional[str] = None
    ordine: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 12.2 VoceProgetto (Prezzi Progetto)

```python
class VoceProgetto(SQLModel, table=True):
    __tablename__ = "voce_progetto"
    __table_args__ = (
        UniqueConstraint("voce_id", name="uq_voce_progetto_voce"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    voce_id: int = Field(foreign_key="voce.id")
    computo_id: int = Field(foreign_key="computo.id")
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 12.3 VoceOfferta (Prezzi Offerte)

```python
class VoceOfferta(SQLModel, table=True):
    __tablename__ = "voce_offerta"
    __table_args__ = (
        UniqueConstraint(
            "voce_id", "computo_id", "impresa_id",
            name="uq_voce_offerta_voce_computo_impresa",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    voce_id: int = Field(foreign_key="voce.id")
    computo_id: int = Field(foreign_key="computo.id")
    impresa_id: int = Field(foreign_key="impresa.id")
    round_number: Optional[int] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 12.4 Impresa (Anagrafica)

```python
class Impresa(SQLModel, table=True):
    __tablename__ = "impresa"
    __table_args__ = (
        UniqueConstraint(
            "normalized_label",
            name="uq_impresa_normalized_label",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(description="Nome visualizzato")
    normalized_label: str = Field(description="Nome normalizzato")
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Enumerazioni

### ComputoTipo

```python
class ComputoTipo(str, Enum):
    progetto = "progetto"  # Computo metrico estimativo
    ritorno = "ritorno"    # Offerta/ritorno di gara
```

### CommessaStato

```python
class CommessaStato(str, Enum):
    setup = "setup"          # In configurazione
    in_corso = "in_corso"    # Attiva
    chiusa = "chiusa"        # Completata
```

### WbsVisibilityKind

```python
class WbsVisibilityKind(str, Enum):
    spaziale = "spaziale"  # Nodi WbsSpaziale (L1-5)
    wbs6 = "wbs6"          # Nodi Wbs6
    wbs7 = "wbs7"          # Nodi Wbs7
```

---

## Relazioni e Diagrammi ERD

### Schema Completo

```
┌──────────────┐
│  Commessa    │
│  - id (PK)   │
│  - codice    │
│  - nome      │
│  - stato     │
└──────┬───────┘
       │
       ├───────────────────────────────────────────────────────┐
       │                                                       │
       │ 1:N                                                   │ 1:N
┌──────▼────────┐                                      ┌──────▼────────┐
│  Computo      │                                      │ WbsSpaziale   │
│  - id (PK)    │                                      │  - id (PK)    │
│  - tipo       │ progetto | ritorno                   │  - level 1-5  │
│  - impresa    │                                      │  - code       │
│  - round_num  │                                      │  - parent_id  │
└──────┬────────┘                                      └──────┬────────┘
       │                                                      │
       │ 1:N                                                  │ self-ref
┌──────▼────────┐                                      ┌──────▼────────┐
│ VoceComputo   │                                      │     Wbs6      │
│  - id (PK)    │                                      │  - id (PK)    │
│  - codice     │                                      │  - code A###  │
│  - desc       │                                      │  - label      │
│  - qty        │                                      └──────┬────────┘
│  - price      │                                             │
│  - wbs_1...7  │                                             │ 1:N
└───────────────┘                                      ┌──────▼────────┐
                                                       │     Wbs7      │
┌──────────────┐                                       │  - id (PK)    │
│ PriceListItem│                                       │  - code A###. │
│  - id (PK)   │                                       │  - wbs6_id    │
│  - item_code │                                       └───────────────┘
│  - price_list│ (JSON)
│  - wbs6_code │
│  - embedding │ (JSON)
└──────────────┘

┌──────────────┐
│   Settings   │  (singleton)
│  - id (PK)   │
│  - thresholds│
└──────────────┘

┌──────────────┐
│ ImportConfig │
│  - id (PK)   │
│  - nome      │
│  - columns   │
└──────────────┘
```

### Relazioni Principali

```
Commessa
  ├─ 1:N → Computo
  │   └─ 1:N → VoceComputo
  ├─ 1:N → WbsSpaziale (L1-5)
  │   └─ self-reference (parent_id)
  ├─ 1:N → Wbs6
  │   └─ 1:N → Wbs7
  ├─ 1:N → PriceListItem
  ├─ 1:1 → CommessaPreferences
  └─ 1:N → ImportConfig

Wbs6 (pivot analitico)
  ├─ N:1 → WbsSpaziale (opzionale, livello 5)
  └─ 1:N → Wbs7

WbsVisibility
  ├─ N:1 → Commessa
  └─ reference → WbsSpaziale | Wbs6 | Wbs7 (via kind + node_id)
```

---

## Indici e Constraints

### Unique Constraints

| Tabella | Constraint | Campi |
|---------|-----------|-------|
| `wbs_spaziale` | `uq_wbs_spaziale_commessa_level_code` | (commessa_id, level, code) |
| `wbs6` | `uq_wbs6_commessa_code` | (commessa_id, code) |
| `wbs7` | `uq_wbs7_wbs6_code` | (wbs6_id, code) |
| `price_list_item` | `uq_price_list_item_commessa_product` | (commessa_id, product_id) |
| `price_list_item` | `uq_price_list_item_global_code` | (global_code) |
| `wbs_visibility` | `uq_wbs_visibility_commessa_node` | (commessa_id, kind, node_id) |
| `commessa_preferences` | unique constraint | (commessa_id) |
| `impresa` | `uq_impresa_normalized_label` | (normalized_label) |
| `voce` | `uq_voce_commessa_wbs6_codice_ordine` | (commessa_id, wbs6_id, codice, ordine) |
| `voce_progetto` | `uq_voce_progetto_voce` | (voce_id) |
| `voce_offerta` | `uq_voce_offerta_voce_computo_impresa` | (voce_id, computo_id, impresa_id) |

### Indici

| Tabella | Campo | Tipo |
|---------|-------|------|
| `computo` | `commessa_code` | index |
| `voce_computo` | `commessa_code` | index |
| `voce_computo` | `global_code` | index |
| `price_list_item` | `commessa_code` | index |
| `price_list_item` | `item_code` | index |
| `price_list_item` | `global_code` | unique index |

---

## Esempi d'Uso

### Query: Lista Commesse Attive

```python
from sqlmodel import select

stmt = select(Commessa).where(
    Commessa.stato == CommessaStato.in_corso
).order_by(Commessa.created_at.desc())

commesse = session.exec(stmt).all()
```

### Query: Computi di una Commessa

```python
stmt = select(Computo).where(
    Computo.commessa_id == commessa_id
)
computi = session.exec(stmt).all()

# Separare progetto e ritorni
progetto = [c for c in computi if c.tipo == ComputoTipo.progetto]
ritorni = [c for c in computi if c.tipo == ComputoTipo.ritorno]
```

### Query: Voci WBS6 per Commessa

```python
stmt = select(Wbs6).where(
    Wbs6.commessa_id == commessa_id
).order_by(Wbs6.code)

wbs6_nodes = session.exec(stmt).all()
```

### Query: Calcolo Importo Totale Computo

```python
from sqlalchemy import func

stmt = select(func.sum(VoceComputo.importo)).where(
    VoceComputo.computo_id == computo_id
)
importo_totale = session.exec(stmt).one()
```

### Query: Ricerca Elenco Prezzi

```python
stmt = select(PriceListItem).where(
    PriceListItem.commessa_id == commessa_id,
    PriceListItem.item_code.contains("A001")
).limit(20)

items = session.exec(stmt).all()
```

---

## Prossimi Passi

- [Schemas](./05-SCHEMAS.md) - Schemi Pydantic per API
- [API Routes](./03-API-ROUTES.md) - Endpoint HTTP
- [Services](./04-SERVICES.md) - Business logic
