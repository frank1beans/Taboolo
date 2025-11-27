# Backend Architecture

## 🏗️ Struttura del Progetto

Il backend di TABOOLO segue una architettura modulare Domain-Driven Design (DDD), organizzata in layer separati per massimizzare manutenibilità, testabilità e scalabilità.

## 📁 Organizzazione Directory

```
backend/
├── app/                            # Applicazione principale
│   ├── main.py                     # Entry point FastAPI
│   │
│   ├── api/                        # Layer HTTP/API
│   │   ├── router.py               # Router aggregator principale
│   │   ├── deps.py                 # Dependency injection
│   │   ├── middleware.py           # Middleware HTTP
│   │   └── v1/                     # API versioning (v1)
│   │       ├── endpoints/          # Endpoint HTTP organizzati per dominio
│   │       └── schemas/            # Request/Response DTOs
│   │
│   ├── core/                       # Configurazione core
│   │   ├── config.py               # Settings (Pydantic)
│   │   ├── security.py             # Auth, JWT, password hashing
│   │   ├── logging.py              # Logging configuration
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── constants.py            # Costanti globali
│   │
│   ├── domain/                     # Domain Layer (Business Logic)
│   │   ├── users/                  # User domain
│   │   │   ├── models.py           # SQLModel tables
│   │   │   ├── schemas.py          # Pydantic schemas
│   │   │   ├── repository.py       # Data access
│   │   │   └── service.py          # Business logic
│   │   │
│   │   ├── commesse/               # Commesse domain
│   │   ├── computi/                # Computi domain
│   │   ├── wbs/                    # WBS domain
│   │   ├── catalog/                # Catalog/Price lists
│   │   └── settings/               # Global settings
│   │
│   ├── services/                   # Application Services (Orchestration)
│   │   ├── analysis/               # Analytics & insights
│   │   ├── import/                 # File import services
│   │   ├── nlp/                    # NLP & embeddings
│   │   ├── storage/                # File storage
│   │   └── audit/                  # Auditing
│   │
│   ├── db/                         # Database layer
│   │   ├── session.py              # DB engine & session
│   │   ├── base.py                 # Base classes
│   │   ├── init_db.py              # DB initialization
│   │   ├── models.py               # Compatibility layer (re-exports)
│   │   └── models_wbs.py           # WBS models
│   │
│   └── utils/                      # Shared utilities
│
├── robimb/                         # ML package (separate)
├── migrations/                     # Alembic migrations
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
│
└── scripts/                        # Utility scripts
```

## 🎯 Principi Architetturali

### 1. **Separation of Concerns**
Ogni layer ha responsabilità ben definite:
- **API Layer**: gestisce HTTP, validazione input, serializzazione
- **Domain Layer**: contiene business logic e regole di dominio
- **Service Layer**: orchestra operazioni complesse tra domini
- **DB Layer**: gestisce persistenza dati

### 2. **Domain-Driven Design**
Codice organizzato per domini business (`commesse`, `computi`, `users`, etc.) invece che per tipo tecnico. Ogni dominio contiene:
- **models.py**: Entità del database (SQLModel)
- **schemas.py**: DTOs e validazione (Pydantic)
- **repository.py**: Pattern di accesso ai dati
- **service.py**: Business logic specifica del dominio

### 3. **Dependency Injection**
Utilizzo di FastAPI `Depends()` per:
- Gestione sessioni database
- Autenticazione/autorizzazione
- Configurazione condivisa

### 4. **Backward Compatibility**
Il file `app/db/models.py` funziona come **compatibility layer** che re-esporta tutti i modelli dai rispettivi domini, permettendo al codice esistente di continuare a funzionare senza modifiche agli import.

## 🔄 Flusso Tipico di una Request

```
1. HTTP Request
   ↓
2. API Middleware (audit, security)
   ↓
3. API Endpoint (app/api/v1/endpoints/)
   ↓
4. Domain Service (app/domain/*/service.py)
   ↓
5. Repository (app/domain/*/repository.py)
   ↓
6. Database (SQLModel)
   ↓
7. Response (via schemas)
```

## 📦 Domini Principali

### **Users** (`app/domain/users/`)
Gestione utenti, autenticazione, profili, audit log

### **Commesse** (`app/domain/commesse/`)
Progetti, preferenze commessa, stati

### **Computi** (`app/domain/computi/`)
Computi metrici, voci, configurazioni import

### **WBS** (`app/domain/wbs/`)
Work Breakdown Structure, predizioni, visibilità

### **Catalog** (`app/domain/catalog/`)
Listini prezzi, proprietà prodotti, offerte imprese

### **Settings** (`app/domain/settings/`)
Configurazioni globali applicazione

## 🛠️ Services (Orchestrazione)

### **Analysis** (`app/services/analysis/`)
Analytics, comparazioni, trends, dashboard stats

### **Import** (`app/services/import/`)
Import Excel, parsing, matching, SIX format

### **NLP** (`app/services/nlp/`)
Semantic embeddings, property extraction, ML models

### **Storage** (`app/services/storage/`)
File storage, serialization

### **Audit** (`app/services/audit/`)
Audit logging, tracking azioni utente

## 🧪 Testing

```
tests/
├── unit/                   # Test isolati per singole funzioni
│   ├── domain/             # Test business logic
│   └── services/           # Test services
└── integration/            # Test end-to-end
    └── test_api_*.py       # Test API completi
```

## 🚀 Vantaggi della Nuova Struttura

### Per Sviluppatori
- ✅ **Onboarding rapido**: Struttura intuitiva e auto-documentante
- ✅ **Manutenibilità**: Modifiche localizzate ai singoli domini
- ✅ **Testing**: Moduli isolati facili da testare
- ✅ **Git**: Meno conflitti grazie alla separazione

### Per il Progetto
- ✅ **Scalabilità**: Facile aggiungere nuovi domini
- ✅ **Flessibilità**: Domain logic separato da infrastruttura
- ✅ **Qualità**: Separation of concerns = meno bug
- ✅ **Documentazione**: Codice organizzato = più leggibile

## 🔧 Best Practices

### Import Convention
```python
# ✅ PREFERITO: Import da domain packages
from app.domain.commesse.models import Commessa
from app.domain.users.models import User

# ⚠️ DEPRECATO (ma ancora supportato): Import da compatibility layer
from app.db.models import Commessa, User
```

### Aggiungere un Nuovo Dominio
1. Creare directory `app/domain/nuovo_dominio/`
2. Aggiungere `models.py`, `schemas.py`, `service.py`
3. Creare endpoint in `app/api/v1/endpoints/nuovo_dominio.py`
4. Aggiungere route in `app/api/router.py`

### Service vs Domain Logic
- **Domain Service**: Operazioni su singolo dominio (es: calcolo totale computo)
- **Application Service**: Orchestrazione tra domini (es: import che tocca computi + wbs)

## 📚 References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
