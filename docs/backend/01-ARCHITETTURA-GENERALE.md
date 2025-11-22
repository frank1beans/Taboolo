# Architettura Generale del Backend

## Indice
- [Panoramica](#panoramica)
- [Stack Tecnologico](#stack-tecnologico)
- [Struttura delle Cartelle](#struttura-delle-cartelle)
- [Pattern Architetturali](#pattern-architetturali)
- [Punto di Ingresso](#punto-di-ingresso)
- [Flusso di Dati](#flusso-di-dati)

## Panoramica

**Taboo Measure Maker Plus** è un'applicazione backend costruita con **FastAPI** per la gestione di computi metrici estimativi e ritorni di gara nel settore edile/costruzioni.

### Caratteristiche Principali

- **Gestione Commesse**: CRUD completo per commesse e computi
- **Import Multi-formato**:
  - Excel (.xlsx, .xls, .xlsm)
  - STR Vision (.six, .xml)
- **WBS Gerarchica**: Supporto per 7 livelli di Work Breakdown Structure
- **Analisi Avanzate**: Confronto offerte, analisi criticità, statistiche
- **NLP/Embedding**: Ricerca semantica nell'elenco prezzi
- **Multi-round Bidding**: Gestione round multipli di gara

## Stack Tecnologico

### Framework e Librerie Core

| Componente | Tecnologia | Versione | Scopo |
|------------|-----------|----------|-------|
| Web Framework | FastAPI | 0.115+ | API REST |
| ORM | SQLModel | 0.0.22+ | Database ORM (SQLAlchemy + Pydantic) |
| Database | SQLite | 3.x | Storage dati |
| Validazione | Pydantic | v2 | Schemi e validazione |
| Parser Excel | openpyxl | 3.x | Lettura file Excel |
| NLP | sentence-transformers | 3.3+ | Embedding semantici |
| Runtime NLP | ONNX Runtime | 1.20+ | Inference CPU-based |
| Migrazioni | Alembic | 1.14+ | Schema migrations |

### Architettura a 3 Livelli

```
┌─────────────────────────────────────┐
│     API Layer (FastAPI Routes)     │  ← HTTP Endpoints
├─────────────────────────────────────┤
│   Service Layer (Business Logic)   │  ← Logica applicativa
├─────────────────────────────────────┤
│  Data Layer (SQLModel/SQLAlchemy)  │  ← Database access
└─────────────────────────────────────┘
```

## Struttura delle Cartelle

```
backend/
├── app/                              # Codice applicativo
│   ├── main.py                      # Entry point FastAPI
│   ├── core/                        # Configurazione globale
│   │   ├── config.py               # Settings (Pydantic BaseSettings)
│   │   └── __init__.py
│   │
│   ├── api/                         # Layer HTTP/REST
│   │   ├── __init__.py             # Router aggregator
│   │   ├── deps.py                 # Dependency Injection
│   │   └── routes/                 # Endpoint handlers
│   │       ├── commesse.py         # CRUD commesse (800+ righe)
│   │       ├── computi.py          # WBS summary
│   │       ├── dashboard.py        # Stats dashboard
│   │       ├── settings.py         # Impostazioni globali
│   │       └── import_configs.py   # Config personalizzate
│   │
│   ├── db/                          # Database layer
│   │   ├── session.py              # Engine + SessionMaker
│   │   ├── init_db.py              # Creazione tabelle
│   │   ├── models.py               # Modelli core (246 righe)
│   │   └── models_wbs.py           # Modelli WBS (200+ righe)
│   │
│   ├── services/                    # Business logic
│   │   ├── commesse.py             # CRUD service
│   │   ├── importer.py             # Import Excel (800+ righe)
│   │   ├── six_import_service.py   # Import STR Vision (800+ righe)
│   │   ├── analysis.py             # Aggregazioni WBS (200+ righe)
│   │   ├── insights.py             # Dashboard/analisi (600+ righe)
│   │   ├── nlp.py                  # Embedding service (300+ righe)
│   │   ├── price_catalog.py        # Elenco prezzi (200+ righe)
│   │   ├── storage.py              # File management (248 righe)
│   │   ├── wbs_import.py           # Import WBS Excel (500+ righe)
│   │   └── wbs_visibility.py       # Visibilità WBS (150+ righe)
│   │
│   ├── excel/                       # Parser Excel
│   │   ├── parser.py               # parse_computo_excel() (500+ righe)
│   │   └── __init__.py
│   │
│   └── schemas.py                   # Schemi Pydantic API (450 righe)
│
├── migrations/                      # Alembic migrations
│   ├── versions/                   # Script migrazione
│   └── env.py                      # Configurazione Alembic
│
├── tests/                           # Test suite
│   ├── test_six_import_service.py
│   └── ...
│
├── storage/                         # File storage (runtime)
│   ├── database.sqlite             # Database SQLite
│   ├── commessa_0001/              # File per commessa
│   └── models/                     # Modelli NLP
│
├── requirements.txt                 # Dipendenze Python
├── start_backend.py                # Script avvio
└── run.py                          # Script alternativo
```

## Pattern Architetturali

### 1. Factory Pattern (main.py)

```python
def create_app() -> FastAPI:
    """Factory che crea e configura l'applicazione"""
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # Setup middleware
    app.add_middleware(CORSMiddleware, ...)

    # Startup events
    @app.on_event("startup")
    def _startup():
        init_db()  # Crea tabelle

    # Include routers
    app.include_router(api_router)

    return app

app = create_app()
```

### 2. Service Layer Pattern

Tutta la business logic è isolata in servizi:

```python
# services/commesse.py
class CommesseService:
    @staticmethod
    def create_commessa(session, payload: CommessaCreate) -> Commessa:
        commessa = Commessa(**payload.model_dump())
        session.add(commessa)
        session.commit()
        session.refresh(commessa)
        return commessa
```

### 3. Dependency Injection (FastAPI)

```python
# api/deps.py
def get_session():
    with Session(engine) as session:
        yield session

# Uso nelle route
@router.get("/commesse")
def list_commesse(session: Session = Depends(get_session)):
    return CommesseService.list_commesse(session)
```

### 4. Singleton Services

```python
# services/__init__.py
storage_service = StorageService(settings.storage_root)
semantic_embedding_service = SemanticEmbeddingService()
price_catalog_service = PriceCatalogService(embedding_service=semantic_embedding_service)
```

### 5. Repository Pattern (implicito con SQLModel)

```python
# Query builder con SQLModel
stmt = select(Commessa).where(Commessa.id == commessa_id)
commessa = session.exec(stmt).first()
```

## Punto di Ingresso

### main.py

File: [backend/app/main.py](../../backend/app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router
from app.db.init_db import init_db

def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS rigoroso (no wildcard)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Startup: crea tabelle database
    @application.on_event("startup")
    def _startup():
        init_db()

    # Include router API
    application.include_router(api_router)  # prefix: /api/v1

    return application

app = create_app()
```

### Avvio Server

```bash
# Development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Flusso di Dati

### 1. Request Flow

```
HTTP Request
  ↓
FastAPI Router
  ↓
Route Handler (api/routes/*.py)
  ↓
Dependency Injection (get_session)
  ↓
Service Layer (services/*.py)
  ↓
Database (SQLModel/SQLAlchemy)
  ↓
Response (Pydantic Schema)
```

### 2. Upload Computo Progetto

```
POST /api/v1/commesse/{id}/computo/upload
  ↓
storage_service.save_upload()
  ├─ Valida file (magic bytes)
  ├─ Sanitizza nome
  └─ Salva in storage/commessa_XXXX/
  ↓
parse_computo_excel(file_path)
  ├─ Riconosce intestazioni
  ├─ Estrae WBS levels (1-7)
  └─ Estrae voci (codice, desc, qty, price)
  ↓
import_service.import_computo_progetto()
  ├─ Crea Computo(tipo="progetto")
  ├─ Inserisce VoceComputo (bulk)
  └─ Calcola aggregati
  ↓
Response: ComputoSchema
```

### 3. Import STR Vision

```
POST /api/v1/commesse/{id}/six/import
  ↓
SixParser.parse(file_path)
  ├─ Unzip .six (se ZIP)
  ├─ Parse XML
  ├─ Estrae WBS spaziale (L1-5)
  ├─ Estrae WBS6 (categorie)
  ├─ Estrae WBS7 (raggruppatori)
  └─ Estrae prodotti + prezzi
  ↓
six_import_service.import_six_file()
  ├─ Upsert WbsSpaziale, Wbs6, Wbs7
  ├─ price_catalog_service.replace_catalog()
  │  ├─ DELETE vecchi items
  │  ├─ INSERT nuovi PriceListItem
  │  └─ Genera embedding (NLP)
  └─ import_service.import_computo_progetto()
     └─ Crea Computo con voci STR Vision
  ↓
Response: SixImportReportSchema
```

### 4. Analisi Commessa

```
GET /api/v1/commesse/{id}/analisi
  ↓
insights_service.get_analisi_commessa()
  ├─ Carica Settings (thresholds)
  ├─ Recupera computo progetto
  ├─ Recupera ritorni (filtrati)
  │
  ├─ Confronto importi
  │  └─ Delta progetto vs offerte
  │
  ├─ Distribuzione variazioni
  │  └─ Istogramma criticità
  │
  ├─ Voci critiche
  │  ├─ Per ogni voce:
  │  │  ├─ Media offerte
  │  │  ├─ Deviazione standard
  │  │  └─ Classifica criticità
  │  └─ Sort per criticità
  │
  └─ Analisi per WBS6
     ├─ Aggregazioni per categoria
     ├─ Statistiche per impresa
     └─ Trend prezzi
  ↓
Response: AnalisiCommessaSchema
```

## Configurazione

### Environment Variables

```bash
# Debug mode
TABOO_DEBUG=true

# CORS
TABOO_CORS_ORIGINS="http://localhost:5173,http://localhost:3000"

# Upload
TABOO_MAX_UPLOAD_SIZE_MB=30

# NLP
TABOO_NLP_EXECUTION_PROVIDERS="CPUExecutionProvider"
TABOO_NLP_MODEL_ID="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

### Settings (core/config.py)

```python
class Settings(BaseSettings):
    app_name: str = "Taboo Measure Maker Backend"
    debug: bool = False

    # Storage
    storage_root: Path = Path("./storage")
    database_path: str = "database.sqlite"

    # Upload limits
    max_upload_size_mb: int = 15
    allowed_file_extensions: set[str] = {".xlsx", ".xls", ".xlsm", ".six", ".xml"}

    # CORS
    cors_origins: list[str] = [...]

    # NLP
    nlp_model_id: str = "sentence-transformers/..."
    nlp_execution_providers: list[str] = ["CPUExecutionProvider"]

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.storage_root / self.database_path}"
```

## Sicurezza

### 1. File Upload

- Validazione magic bytes (no estensione solo)
- Whitelist estensioni (`.xlsx`, `.xls`, `.xlsm`, `.six`, `.xml`)
- Sanitizzazione nome file (rimuovi path traversal)
- Limite dimensione file (15MB default)
- Streaming upload (chunk-based, no memory overflow)

```python
# storage_service.py
EXCEL_MAGIC_BYTES = [
    b"\x50\x4B\x03\x04",  # ZIP (XLSX)
    b"\xD0\xCF\x11\xE0",  # OLE2 (XLS)
]

def _validate_file_security(self, filename, file_bytes):
    # Check extension
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTS):
        raise ValueError("Invalid file extension")

    # Check magic bytes
    if not any(file_bytes.startswith(magic) for magic in MAGIC_BYTES):
        raise ValueError("Invalid file format")
```

### 2. CORS

```python
# CORS rigoroso - NO wildcard
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
allow_credentials=True
```

### 3. Input Sanitization

- Pydantic validation su tutti input
- SQLModel previene SQL injection
- Path sanitization per file storage

## Database

### SQLite Configuration

```python
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug
    connect_args={"check_same_thread": False},  # SQLite threading
)
```

### Migrazioni (Alembic)

```bash
# Crea migrazione
alembic revision --autogenerate -m "Descrizione"

# Applica migrazioni
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance

### 1. Bulk Insert

```python
# Batch insert voci computo (evita N+1 queries)
session.add_all(voci_list)
session.commit()
```

### 2. Lazy Loading

```python
# Carica solo quando necessario
commessa = session.get(Commessa, id)  # No join
computi = commessa.computi  # Lazy load se relationship
```

### 3. Indexing

```python
# Index su colonne chiave
class VoceComputo(SQLModel, table=True):
    computo_id: int = Field(index=True)
    commessa_code: str = Field(index=True)
    global_code: str = Field(index=True)
```

### 4. NLP Caching

```python
# Modello ONNX caricato una sola volta (singleton)
semantic_embedding_service = SemanticEmbeddingService()  # Lazy init
```

## Logging

```python
import logging

logger = logging.getLogger(__name__)

# Uso
logger.info("Importing computo for commessa %d", commessa_id)
logger.error("Failed to parse Excel: %s", str(e))
```

## Prossimi Passi

- [Database Models](./02-DATABASE-MODELS.md) - Modelli e relazioni
- [API Routes](./03-API-ROUTES.md) - Endpoint HTTP
- [Services](./04-SERVICES.md) - Business logic
- [Schemas](./05-SCHEMAS.md) - Schemi Pydantic
