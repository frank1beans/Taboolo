# TABOOLO

**Sistema di gestione prezzi edili e ritorni di gara**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Panoramica

TABOOLO è una piattaforma professionale per la gestione centralizzata di **computi metrici**, **cataloghi prezzi** e **ritorni di gara** nel settore delle costruzioni. Progettato per imprese edili italiane, integra funzionalità avanzate di analisi competitiva e ricerca semantica basata su AI.

### Funzionalità Principali

- **Gestione Commesse** - Creazione e monitoraggio progetti con stati e preferenze personalizzabili
- **Catalogo Prezzi Unificato** - Database centralizzato con ricerca semantica AI-powered
- **Import Multi-formato** - Supporto per Excel, STR Vision (.six/.xml) e formati proprietari
- **Ritorni di Gara** - Gestione multi-round delle offerte fornitori con allineamento automatico
- **Analisi Avanzate** - Heatmap competitività, trend prezzi, confronto offerte
- **WBS a 7 Livelli** - Struttura gerarchica completa con aggregazione costi
- **Estrazione Proprietà AI** - Identificazione automatica di materiali, spessori, normative

---

## Stack Tecnologico

### Frontend
| Tecnologia | Utilizzo |
|------------|----------|
| React 18 + TypeScript | UI Framework |
| TanStack Query | State Management |
| Tailwind CSS + shadcn/ui | Styling |
| ag-Grid | Tabelle dati avanzate |
| Recharts | Grafici e visualizzazioni |
| Vite | Build tool |

### Backend
| Tecnologia | Utilizzo |
|------------|----------|
| FastAPI | Web Framework |
| SQLModel + SQLAlchemy | ORM |
| Pydantic v2 | Validazione dati |
| sentence-transformers | Ricerca semantica |
| FAISS | Indicizzazione vettoriale |
| Alembic | Migrazioni database |

### Database
- **SQLite** (sviluppo)
- **PostgreSQL** (produzione)

---

## Installazione

### Prerequisiti

- Node.js 18+
- Python 3.10+
- npm o bun

### Frontend

```bash
# Installa dipendenze
npm install

# Avvia server di sviluppo (porta 8080)
npm run dev

# Build produzione
npm run build
```

### Backend

```bash
cd backend

# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente (Windows)
venv\Scripts\activate

# Attiva ambiente (Linux/Mac)
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Esegui migrazioni
alembic upgrade head

# Avvia server (porta 8000)
python run.py
```

---

## Configurazione

### Variabili d'ambiente Frontend (`.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=<url>
VITE_SUPABASE_PUBLISHABLE_KEY=<key>
```

### Variabili d'ambiente Backend (`backend/.env`)

```env
TABOO_DEBUG=False
TABOO_CORS_ORIGINS=http://localhost:8080,http://localhost:5173
TABOO_JWT_SECRET_KEY=<your-secret-key>
TABOO_MAX_UPLOAD_SIZE_MB=100
TABOO_DATABASE_URL=sqlite:///storage/database.sqlite
```

---

## Architettura

```
measure-maker-plus/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # Endpoint REST
│   │   ├── services/         # Business logic
│   │   ├── db/               # Modelli e sessioni
│   │   └── core/             # Config e security
│   └── tests/
├── src/
│   ├── pages/                # Pagine React
│   ├── components/           # Componenti riutilizzabili
│   ├── hooks/                # Custom hooks
│   └── lib/                  # Utilities
└── docs/                     # Documentazione tecnica
```

### Pattern Architetturali

- **3-layer architecture**: Routes → Services → Database
- **Dependency Injection**: Sessione DB passata come parametro
- **Transactional**: Il chiamante gestisce commit/rollback

---

## Funzionalità Dettagliate

### Gestione Commesse

Ogni commessa rappresenta un progetto edile con:
- Codice identificativo e nome
- Business unit di appartenenza
- Stati: `setup` → `in_progress` → `closed`
- Preferenze e impostazioni personalizzabili
- Export/import bundle (formato ZIP)

### Catalogo Prezzi

- Ricerca full-text e semantica (NLP)
- Filtraggio per WBS, fornitore, proprietà
- Confronto prezzi multi-fornitore
- Storico variazioni prezzo

### Import Dati

| Formato | Descrizione |
|---------|-------------|
| Excel Computo | Importazione preventivi con mapping colonne |
| Excel Ritorni | Offerte fornitori con allineamento automatico |
| STR Vision (.six) | Parser nativo per progetti STR |
| WBS Excel | Struttura gerarchica a 7 livelli |

### Analisi Avanzate

- **Confronto Offerte** - Tabella comparativa fornitori
- **Heatmap Competitività** - Visualizzazione forza prezzi per categoria
- **Trend Evoluzione** - Andamento prezzi nei round di gara
- **Delta Composition** - Waterfall chart delle variazioni

### Sicurezza

- Autenticazione JWT con refresh token
- Role-based access control (admin, project_manager, computista, viewer)
- Rate limiting sugli import
- Validazione magic byte per upload file
- Audit logging completo

---

## API Documentation

Con il server backend avviato, la documentazione interattiva è disponibile su:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoint Principali

```
GET    /api/v1/commesse                    # Lista commesse
POST   /api/v1/commesse                    # Crea commessa
GET    /api/v1/commesse/{id}               # Dettaglio commessa
POST   /api/v1/commesse/{id}/ritorni       # Import ritorni gara
GET    /api/v1/commesse/{id}/confronto     # Confronto offerte
GET    /api/v1/commesse/price-catalog      # Catalogo prezzi globale
```

---

## Sviluppo

### Struttura Test

```bash
# Backend tests
cd backend
pytest tests/

# Frontend (Vite dev server con HMR)
npm run dev
```

### Convenzioni Codice

- **Backend**: PEP 8, type hints obbligatori
- **Frontend**: ESLint + Prettier, TypeScript strict mode
- **Commits**: Conventional Commits

---

## Roadmap

- [ ] Dashboard personalizzabili
- [ ] Export PDF report
- [ ] Integrazione con sistemi ERP
- [ ] Mobile app (React Native)
- [ ] Multi-tenant SaaS

---

## Contributi

1. Fork del repository
2. Crea un branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit delle modifiche (`git commit -m 'Aggiunge nuova funzionalità'`)
4. Push sul branch (`git push origin feature/nuova-funzionalita`)
5. Apri una Pull Request

---

## Licenza

Proprietario - Tutti i diritti riservati.

---

## Contatti

**Repository**: [github.com/frank1beans/measure-maker-plus](https://github.com/frank1beans/measure-maker-plus)

---

<p align="center">
  <strong>TABOOLO</strong> - Gestione intelligente dei prezzi edili
</p>
