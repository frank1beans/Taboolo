# 🚀 Quick Reference - Backend TABOOLO

## 📁 Dove Mettere il Codice?

| Cosa Stai Facendo | Dove Va |
|-------------------|---------|
| Nuovo modello database | `app/domain/[dominio]/models.py` |
| Business logic | `app/domain/[dominio]/service.py` |
| Nuovo endpoint HTTP | `app/api/v1/endpoints/[nome].py` |
| Orchestrazione cross-domain | `app/services/[nome]/` |
| Config app | `app/core/config.py` |
| Utility condivisa | `app/utils/[nome].py` |
| Test domain | `tests/unit/domain/test_[dominio].py` |
| Test API | `tests/integration/test_api_[nome].py` |

## 🎯 Pattern Comuni

### Creare Nuovo Endpoint

```python
# app/api/v1/endpoints/nuovo.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db, get_current_user
from app.domain.users.models import User
from app.domain.commesse.models import Commessa

router = APIRouter()

@router.get("/nuovo/{id}")
def get_nuovo(id: int, db: Session = Depends(get_db)):
    # Your logic here
    pass
```

Poi registrare in `app/api/router.py`:
```python
from app.api.v1.endpoints import nuovo
api_router.include_router(nuovo.router, prefix="/nuovo", tags=["nuovo"])
```

### Creare Domain Service

```python
# app/domain/[dominio]/service.py
from sqlmodel import Session, select
from app.domain.[dominio].models import Model

def get_by_id(session: Session, id: int) -> Model:
    return session.get(Model, id)

def create(session: Session, **data) -> Model:
    obj = Model(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
```

### Repository Pattern

```python
# app/domain/[dominio]/repository.py
from typing import Optional, List
from sqlmodel import Session, select
from app.domain.[dominio].models import Model

class ModelRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, id: int) -> Optional[Model]:
        return self.session.get(Model, id)
    
    def get_all(self) -> List[Model]:
        return self.session.exec(select(Model)).all()
    
    def create(self, obj: Model) -> Model:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
```

## 📋 Checklist Nuova Feature

- [ ] Identificato dominio giusto
- [ ] Modello aggiunto in `domain/[dominio]/models.py`
- [ ] Service creato in `domain/[dominio]/service.py`
- [ ] Endpoint creato in `api/v1/endpoints/[nome].py`
- [ ] Router registrato in `api/router.py`
- [ ] Test scritti in `tests/`
- [ ] Test passano ✅

## 🔍 Import Cheat Sheet

### Models
```python
# ✅ Nuovo
from app.domain.commesse.models import Commessa
from app.domain.users.models import User, UserRole
from app.domain.computi.models import Computo

# ⚠️ Vecchio (ancora ok)
from app.db.models import Commessa, User, Computo
```

### Services
```python
# ✅ Nuovo
from app.services.nlp.embedding_service import semantic_embedding_service
from app.services.analysis import CoreAnalysisService

# ⚠️ Vecchio (ancora ok)
from app.services.nlp import semantic_embedding_service
```

## 🧪 Test Comuni

```python
# tests/unit/domain/test_commesse.py
import pytest
from sqlmodel import Session, create_engine
from app.domain.commesse.models import Commessa

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        yield session

def test_create_commessa(session: Session):
    commessa = Commessa(nome="Test", codice="T001")
    session.add(commessa)
    session.commit()
    
    assert commessa.id is not None
    assert commessa.nome == "Test"
```

## 🚨 Common Errors

### Import Error
```
ImportError: cannot import name 'X' from 'app.services'
```
**Fix**: Usa nuovo import path da `app.domain` o `app.services/[submodule]`

### Circular Import
```
ImportError: circular import
```
**Fix**: Sposta logica condivisa in `app.utils/` o usa dependency injection

### Model Not Found
```
sqlmodel.exc.NoResultFound
```
**Fix**: Usa `.get()` per primary key o `.first()` per queries

## 📚 Documentazione Completa

- **Overview**: [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)
- **Architettura**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Migrazione**: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- **Struttura**: [STRUCTURE_VISUAL.md](./STRUCTURE_VISUAL.md)

## 💡 Pro Tips

1. **Inizia dal domain**: Prima model, poi service, poi endpoint
2. **Test subito**: Scrivi test mentre sviluppi, non dopo
3. **Segui i pattern**: Guarda codice esistente per esempi
4. **Dominio chiaro**: Se non sai dove mettere codice, probabilmente serve nuovo dominio
5. **Repository per data access**: Separa business logic da database queries

---

**Ultima Modifica**: $(date +%Y-%m-%d)
