# 📊 Struttura Backend TABOOLO - Visualizzazione Completa

## 🌳 Albero Directory Completo

```
backend/
│
├── app/                                    # Applicazione principale
│   │
│   ├── main.py                            # 🚀 Entry point FastAPI
│   │
│   ├── api/                               # 🌐 Layer HTTP/API
│   │   ├── __init__.py                    # Re-export api_router
│   │   ├── router.py                      # ⭐ Router aggregator principale
│   │   ├── deps.py                        # Dependency injection (get_db, get_current_user)
│   │   ├── middleware.py                  # Audit & security middleware
│   │   │
│   │   ├── routes/                        # ⚠️ LEGACY: Vecchi endpoint (mantenuti per compatibilità)
│   │   │   ├── auth.py
│   │   │   ├── commesse.py
│   │   │   ├── computi.py
│   │   │   ├── dashboard.py
│   │   │   ├── settings.py
│   │   │   ├── import_configs.py
│   │   │   └── profile.py
│   │   │
│   │   └── v1/                            # ✨ NUOVO: API v1 (versioning)
│   │       ├── endpoints/                 # Endpoint organizzati per dominio
│   │       │   ├── auth.py               # Login, logout, token refresh
│   │       │   ├── commesse.py           # CRUD commesse
│   │       │   ├── computi.py            # CRUD computi
│   │       │   ├── dashboard.py          # Dashboard stats
│   │       │   ├── settings.py           # App settings
│   │       │   ├── import_configs.py     # Import configurations
│   │       │   └── profile.py            # User profile
│   │       │
│   │       └── schemas/                   # Request/Response DTOs
│   │           └── (da popolare)
│   │
│   ├── core/                              # ⚙️ Core Configuration
│   │   ├── config.py                     # Settings Pydantic (env vars)
│   │   ├── security.py                   # JWT, password hashing, auth
│   │   ├── logging.py                    # Logging configuration
│   │   ├── exceptions.py                 # Custom exceptions
│   │   └── constants.py                  # Global constants
│   │
│   ├── domain/                            # 🏢 DOMAIN LAYER (Business Logic)
│   │   │
│   │   ├── users/                         # 👤 User Domain
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # User, UserProfile, RefreshToken, AuditLog
│   │   │   ├── schemas.py                # (da creare) User DTOs
│   │   │   ├── repository.py             # (da creare) Data access patterns
│   │   │   └── service.py                # (da creare) Business logic
│   │   │
│   │   ├── commesse/                      # 📋 Commesse Domain
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # Commessa, CommessaPreferences
│   │   │   ├── schemas.py                # (da creare)
│   │   │   ├── service.py                # ← Copiato da services/commesse.py
│   │   │   └── bundle_service.py         # ← Copiato da services/commessa_bundle.py
│   │   │
│   │   ├── computi/                       # 📊 Computi Domain
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # Computo, VoceComputo, ImportConfig
│   │   │   ├── schemas.py                # (da creare)
│   │   │   ├── repository.py             # (da creare)
│   │   │   └── service.py                # (da creare)
│   │   │
│   │   ├── wbs/                           # 🗂️ WBS Domain
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # (riferimento a db/models_wbs.py)
│   │   │   ├── wbs_import.py             # ← Copiato da services/
│   │   │   ├── wbs_predictor.py          # ← Copiato da services/
│   │   │   └── wbs_visibility.py         # ← Copiato da services/
│   │   │
│   │   ├── catalog/                       # 🛒 Catalog Domain (Price Lists)
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # PriceListItem, PropertyLexicon, etc.
│   │   │   ├── schemas.py                # (da creare)
│   │   │   ├── search_service.py         # ← Copiato da services/catalog_search_service.py
│   │   │   └── price_service.py          # ← Copiato da services/price_catalog.py
│   │   │
│   │   └── settings/                      # ⚙️ Settings Domain
│   │       ├── __init__.py
│   │       ├── models.py                 # Settings globali applicazione
│   │       └── service.py                # (da creare)
│   │
│   ├── services/                          # 🔧 APPLICATION SERVICES (Orchestration)
│   │   │
│   │   ├── analysis/                      # 📈 Analysis Services
│   │   │   ├── __init__.py               # Export services
│   │   │   ├── analysis.py               # Main analysis service
│   │   │   ├── cache.py                  # Cache service
│   │   │   ├── comparison.py             # Comparison logic
│   │   │   ├── core.py                   # Core analysis
│   │   │   ├── dashboard.py              # Dashboard stats
│   │   │   ├── insights.py               # ← Copiato da services/insights.py
│   │   │   ├── trends.py                 # Trend analysis
│   │   │   └── wbs_analysis.py           # WBS-specific analysis
│   │   │
│   │   ├── import/                        # 📥 Import Services
│   │   │   ├── __init__.py
│   │   │   ├── excel_parser.py           # ← Copiato da excel/parser.py
│   │   │   └── importers/
│   │   │       ├── __init__.py
│   │   │       ├── common.py             # Shared import logic
│   │   │       ├── lc.py                 # LC format importer
│   │   │       ├── mc.py                 # MC format importer
│   │   │       ├── parser.py             # Excel parser
│   │   │       ├── six_importer.py       # ← Copiato da services/six_import_service.py
│   │   │       └── matching/
│   │   │           ├── __init__.py
│   │   │           ├── config.py         # Matching configuration
│   │   │           ├── normalization.py  # Text normalization
│   │   │           ├── legacy.py         # Legacy matching
│   │   │           └── report.py         # Matching reports
│   │   │
│   │   ├── nlp/                           # 🧠 NLP & ML Services
│   │   │   ├── __init__.py
│   │   │   ├── embedding_service.py      # ← Copiato da services/nlp.py
│   │   │   ├── property_extraction.py    # ← Copiato da services/
│   │   │   └── property_extractor.py     # ← Copiato da services/
│   │   │
│   │   ├── storage/                       # 💾 Storage Services
│   │   │   ├── __init__.py
│   │   │   ├── storage_service.py        # ← Copiato da services/storage.py
│   │   │   └── serialization.py          # ← Copiato da services/serialization_service.py
│   │   │
│   │   ├── audit/                         # 📝 Audit Services
│   │   │   ├── __init__.py
│   │   │   └── audit_service.py          # ← Copiato da services/audit.py
│   │   │
│   │   ├── ⚠️ LEGACY FILES (ancora presenti per compatibilità)
│   │   ├── analysis.py                   # → Da rimuovere dopo migrazione
│   │   ├── commesse.py                   # → Migrato a domain/commesse/service.py
│   │   ├── commessa_bundle.py            # → Migrato a domain/commesse/bundle_service.py
│   │   ├── catalog_search_service.py     # → Migrato a domain/catalog/
│   │   ├── price_catalog.py              # → Migrato a domain/catalog/
│   │   ├── nlp.py                        # → Migrato a services/nlp/
│   │   ├── property_*.py                 # → Migrato a services/nlp/
│   │   ├── storage.py                    # → Migrato a services/storage/
│   │   ├── audit.py                      # → Migrato a services/audit/
│   │   ├── wbs_*.py                      # → Migrato a domain/wbs/
│   │   └── six_import_service.py         # → Migrato a services/import/
│   │
│   ├── db/                                # 🗄️ Database Layer
│   │   ├── __init__.py
│   │   ├── session.py                    # DB engine & session factory
│   │   ├── base.py                       # Base classes (se necessario)
│   │   ├── init_db.py                    # DB initialization
│   │   ├── models.py                     # ⭐ COMPATIBILITY LAYER (re-export da domain)
│   │   ├── models_old.py                 # 📦 Backup del vecchio models.py
│   │   └── models_wbs.py                 # WBS models (complessi, tenuti qui)
│   │
│   ├── excel/                             # 📑 Excel utilities
│   │   ├── __init__.py
│   │   └── parser.py                     # Excel parser (originale, ancora usato)
│   │
│   └── utils/                             # 🛠️ Shared Utilities
│       ├── __init__.py
│       ├── datetime.py                   # (da creare)
│       ├── text.py                       # (da creare)
│       └── validators.py                 # (da creare)
│
├── robimb/                                # 🤖 ML Package (separato, ben organizzato)
│   ├── cli/
│   ├── extraction/
│   ├── inference/
│   ├── models/
│   ├── registry/
│   ├── reporting/
│   ├── training/
│   └── utils/
│
├── migrations/                            # 🔄 Alembic Migrations
│   └── versions/
│
├── tests/                                 # 🧪 Test Suite
│   ├── conftest.py
│   ├── unit/                             # Unit tests
│   │   ├── domain/                       # (da creare)
│   │   └── services/                     # (da creare)
│   └── integration/                      # Integration tests
│       └── test_api_*.py
│
├── scripts/                               # 📜 Utility Scripts
│   ├── import_test.py
│   ├── backfill_wbs6.py
│   └── build_faiss_index.py
│
├── .env                                   # Environment variables
├── .env.example                           # Example env file
├── requirements.txt                       # Python dependencies
├── pyproject.toml                         # Project config
│
└── 📚 DOCUMENTAZIONE
    ├── ARCHITECTURE.md                    # ⭐ Architettura completa
    ├── MIGRATION_GUIDE.md                 # ⭐ Guida alla migrazione
    ├── README_STRUCTURE.md                # ⭐ Stato attuale & tracking
    ├── REFACTORING_SUMMARY.md             # ⭐ Riepilogo refactoring
    └── STRUCTURE_VISUAL.md                # ⭐ Questo file!
```

## 🎨 Legenda Simboli

| Simbolo | Significato |
|---------|-------------|
| ⭐ | File/directory chiave |
| ✨ | Nuovo nella ristrutturazione |
| ⚠️ | Legacy/Deprecato (da migrare) |
| 📦 | Backup |
| ← | Copiato da altra posizione |
| → | Da migrare a nuova posizione |

## 🔄 Flusso Request Tipico

```
1. HTTP Request
   ↓
2. main.py (FastAPI app)
   ↓
3. api/middleware.py (audit, security)
   ↓
4. api/router.py (route to endpoint)
   ↓
5. api/v1/endpoints/*.py (HTTP handler)
   ↓
6. domain/*/service.py (business logic)
   ↓
7. domain/*/repository.py (data access)
   ↓
8. domain/*/models.py (ORM)
   ↓
9. db/session.py (database)
   ↓
10. Response (via schemas)
```

## 📊 Domini e Responsabilità

### 🏢 Domain Layer (Business Logic)

| Dominio | Responsabilità | Models Principali |
|---------|----------------|-------------------|
| **users** | Autenticazione, profili, audit | User, UserProfile, RefreshToken, AuditLog |
| **commesse** | Gestione progetti | Commessa, CommessaPreferences |
| **computi** | Computi metrici, voci | Computo, VoceComputo, ImportConfig |
| **wbs** | Work Breakdown Structure | WBS nodes (in models_wbs.py) |
| **catalog** | Listini prezzi, prodotti | PriceListItem, PropertyLexicon |
| **settings** | Configurazioni app | Settings |

### 🔧 Service Layer (Orchestration)

| Service | Responsabilità | Usa Domini |
|---------|----------------|------------|
| **analysis** | Analytics, insights, comparazioni | commesse, computi, wbs |
| **import** | Import Excel, matching | commesse, computi, catalog |
| **nlp** | Embeddings, property extraction | catalog |
| **storage** | File storage, serialization | commesse, computi |
| **audit** | Logging azioni utente | users |

## 🎯 Pattern di Import

### ✅ Nuovo Pattern (Raccomandato)

```python
# Import da domain packages
from app.domain.commesse.models import Commessa
from app.domain.users.models import User, UserRole
from app.domain.computi.models import Computo, ComputoTipo

# Import da services
from app.services.nlp.embedding_service import semantic_embedding_service
from app.services.analysis import CoreAnalysisService
```

### ⚠️ Vecchio Pattern (Ancora Supportato)

```python
# Import da compatibility layer (funziona ancora)
from app.db.models import Commessa, User, Computo

# Import da vecchie posizioni (funziona ancora)
from app.services.nlp import semantic_embedding_service
from app.services.commesse import CommesseService
```

## 📈 Stato Migrazione per File

### ✅ Completamente Migrati
- [x] `app/domain/users/models.py`
- [x] `app/domain/commesse/models.py`
- [x] `app/domain/computi/models.py`
- [x] `app/domain/catalog/models.py`
- [x] `app/domain/settings/models.py`
- [x] `app/api/router.py`
- [x] `app/api/v1/endpoints/` (copiati)

### 🔄 Parzialmente Migrati (copiati ma vecchi ancora usati)
- [ ] `app/services/` → `app/domain/*/service.py`
- [ ] `app/services/nlp.py` → `app/services/nlp/`
- [ ] `app/services/import*` → `app/services/import/`

### ⏳ Da Migrare
- [ ] Aggiornare imports negli endpoint
- [ ] Creare repository pattern
- [ ] Creare schemas separati
- [ ] Rimuovere vecchi file

## 🎓 Per Nuovi Sviluppatori

### Dove Trovare Cosa?

**Voglio creare un nuovo endpoint?**
→ `app/api/v1/endpoints/`

**Voglio aggiungere business logic?**
→ `app/domain/[dominio]/service.py`

**Voglio aggiungere un modello DB?**
→ `app/domain/[dominio]/models.py`

**Voglio orchestrare tra più domini?**
→ `app/services/[nome_service]/`

**Voglio configurare l'app?**
→ `app/core/config.py`

**Voglio aggiungere utility condivise?**
→ `app/utils/`

### Esempi Completi da Studiare

- **Dominio ben organizzato**: `app/domain/users/`
- **Services complessi**: `app/services/analysis/`
- **Import complessi**: `app/services/import/importers/`
- **Endpoint completo**: `app/api/v1/endpoints/commesse.py`

## 🚀 Quick Actions

### Aggiungere Nuovo Dominio
```bash
mkdir -p app/domain/nuovo_dominio
touch app/domain/nuovo_dominio/{__init__.py,models.py,schemas.py,service.py}
```

### Aggiungere Nuovo Endpoint
```bash
touch app/api/v1/endpoints/nuovo_endpoint.py
# Poi registrare in app/api/router.py
```

### Aggiungere Nuovo Service
```bash
mkdir -p app/services/nuovo_service
touch app/services/nuovo_service/{__init__.py,service.py}
```

---

**Documentazione Completa**: Vedi [ARCHITECTURE.md](./ARCHITECTURE.md) per dettagli architetturali
**Guida Migrazione**: Vedi [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) per esempi pratici
