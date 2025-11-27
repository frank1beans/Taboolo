# Migration Guide - Nuova Struttura Backend

## 📋 Sommario

Questa guida descrive come migrare codice esistente alla nuova struttura modulare del backend.

## 🔄 Mapping dei File

### API Endpoints

| Vecchia Posizione | Nuova Posizione |
|-------------------|-----------------|
| `app/api/routes/auth.py` | `app/api/v1/endpoints/auth.py` |
| `app/api/routes/commesse.py` | `app/api/v1/endpoints/commesse.py` |
| `app/api/routes/computi.py` | `app/api/v1/endpoints/computi.py` |
| `app/api/routes/dashboard.py` | `app/api/v1/endpoints/dashboard.py` |
| `app/api/routes/settings.py` | `app/api/v1/endpoints/settings.py` |
| `app/api/routes/import_configs.py` | `app/api/v1/endpoints/import_configs.py` |
| `app/api/routes/profile.py` | `app/api/v1/endpoints/profile.py` |

### Models (Database)

| Vecchia Posizione | Nuova Posizione |
|-------------------|-----------------|
| `app/db/models.py` (Users) | `app/domain/users/models.py` |
| `app/db/models.py` (Commesse) | `app/domain/commesse/models.py` |
| `app/db/models.py` (Computi) | `app/domain/computi/models.py` |
| `app/db/models.py` (Catalog) | `app/domain/catalog/models.py` |
| `app/db/models.py` (Settings) | `app/domain/settings/models.py` |
| `app/db/models_wbs.py` | `app/db/models_wbs.py` (invariato) |

### Services

| Vecchia Posizione | Nuova Posizione |
|-------------------|-----------------|
| `app/services/analysis.py` | `app/services/analysis/` (già diviso) |
| `app/services/commesse.py` | `app/domain/commesse/service.py` |
| `app/services/commessa_bundle.py` | `app/domain/commesse/bundle_service.py` |
| `app/services/catalog_search_service.py` | `app/domain/catalog/search_service.py` |
| `app/services/price_catalog.py` | `app/domain/catalog/price_service.py` |
| `app/services/wbs_*.py` | `app/domain/wbs/` |
| `app/services/importer*.py` | `app/services/import/` |
| `app/services/importers/` | `app/services/import/importers/` |
| `app/services/nlp.py` | `app/services/nlp/embedding_service.py` |
| `app/services/property_*.py` | `app/services/nlp/` |
| `app/services/storage.py` | `app/services/storage/storage_service.py` |
| `app/services/serialization_service.py` | `app/services/storage/serialization.py` |
| `app/services/audit.py` | `app/services/audit/audit_service.py` |
| `app/services/six_import_service.py` | `app/services/import/importers/six_importer.py` |

## 🔧 Come Aggiornare gli Import

### Opzione 1: Backward Compatible (Raccomandato per ora)

Il file `app/db/models.py` funziona come **compatibility layer** e re-esporta tutti i modelli. Il codice esistente continuerà a funzionare senza modifiche:

```python
# ✅ Continua a funzionare
from app.db.models import Commessa, User, Computo

# ✅ Anche questo funziona
from app.api import api_router
```

### Opzione 2: Nuovi Import (Per Nuovo Codice)

Per nuovo codice, usa direttamente i domain packages:

```python
# ❌ Vecchio modo
from app.db.models import Commessa, User, ComputoTipo

# ✅ Nuovo modo
from app.domain.commesse.models import Commessa
from app.domain.users.models import User
from app.domain.computi.models import ComputoTipo
```

## 📝 Esempi di Migrazione

### Esempio 1: Endpoint API

**Prima:**
```python
# app/api/routes/custom.py
from fastapi import APIRouter, Depends
from app.db.models import Commessa
from app.services.commesse import get_commessa_stats

router = APIRouter()

@router.get("/stats/{id}")
def get_stats(id: int):
    return get_commessa_stats(id)
```

**Dopo:**
```python
# app/api/v1/endpoints/custom.py
from fastapi import APIRouter, Depends
from app.domain.commesse.models import Commessa
from app.domain.commesse.service import get_commessa_stats

router = APIRouter()

@router.get("/stats/{id}")
def get_stats(id: int):
    return get_commessa_stats(id)
```

### Esempio 2: Service Function

**Prima:**
```python
# app/services/my_service.py
from app.db.models import Computo, VoceComputo
from app.services.nlp import semantic_embedding_service

def analyze_computo(computo_id: int):
    # logic here
    pass
```

**Dopo:**
```python
# app/services/analysis/my_service.py
from app.domain.computi.models import Computo, VoceComputo
from app.services.nlp.embedding_service import semantic_embedding_service

def analyze_computo(computo_id: int):
    # logic here
    pass
```

### Esempio 3: Repository Pattern (Nuovo)

**Creare un repository per accesso dati:**
```python
# app/domain/commesse/repository.py
from typing import Optional
from sqlmodel import Session, select
from app.domain.commesse.models import Commessa

class CommessaRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: int) -> Optional[Commessa]:
        return self.session.get(Commessa, id)

    def get_by_codice(self, codice: str) -> Optional[Commessa]:
        statement = select(Commessa).where(Commessa.codice == codice)
        return self.session.exec(statement).first()

    def save(self, commessa: Commessa) -> Commessa:
        self.session.add(commessa)
        self.session.commit()
        self.session.refresh(commessa)
        return commessa
```

**Utilizzare il repository in un service:**
```python
# app/domain/commesse/service.py
from sqlmodel import Session
from app.domain.commesse.repository import CommessaRepository
from app.domain.commesse.models import Commessa

def create_commessa(session: Session, nome: str, codice: str) -> Commessa:
    repo = CommessaRepository(session)
    commessa = Commessa(nome=nome, codice=codice)
    return repo.save(commessa)
```

## 🎯 Checklist Migrazione

Quando migri un modulo:

- [ ] Sposta il file nella directory appropriata (`domain/` o `services/`)
- [ ] Aggiorna gli import nel file spostato
- [ ] Aggiungi `__init__.py` con re-export se necessario
- [ ] Aggiorna i test relativi
- [ ] Verifica che i test passino
- [ ] Aggiorna la documentazione se necessaria

## ⚠️ Note Importanti

### Compatibility Layer
- `app/db/models.py` è ora un compatibility layer che re-esporta tutti i modelli
- Mantieni questo file finché tutto il codice non è migrato
- Una volta migrato tutto, puoi rimuoverlo gradualmente

### API Versioning
- Gli endpoint sono ora sotto `app/api/v1/`
- Prepara per future versioni API (v2, v3...)
- Il prefix `/api/v1` è configurato in `app/core/config.py`

### Testing
- Mantieni la stessa struttura dei test (`tests/unit/`, `tests/integration/`)
- Aggiorna gli import nei test per riflettere la nuova struttura

## 🆘 Troubleshooting

### Problema: "ModuleNotFoundError"
**Causa:** Import non aggiornati
**Soluzione:** Usa la tabella di mapping sopra per trovare il nuovo percorso

### Problema: "Circular import"
**Causa:** Dipendenze circolari tra domini
**Soluzione:** Usa dependency injection o sposta la logica condivisa in `app/utils/`

### Problema: Test falliscono dopo migrazione
**Causa:** Import nei test non aggiornati
**Soluzione:** Aggiorna gli import dei test seguendo la stessa logica

## 📚 Risorse Aggiuntive

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Documentazione completa dell'architettura
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Repository Pattern](https://deviq.com/design-patterns/repository-pattern)
