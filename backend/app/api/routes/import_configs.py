from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DBSession, require_role, UserRole
from app.db.models import ImportConfig, ImportConfigRead, ImportConfigBase

router = APIRouter(
    dependencies=[require_role([UserRole.project_manager, UserRole.admin])]
)


@router.get("/", response_model=List[ImportConfigRead])
def list_import_configs(
    session: DBSession,
    commessa_id: Optional[int] = Query(default=None, description="Filtra per commessa (null = globali)"),
) -> List[ImportConfigRead]:
    """Elenca tutte le configurazioni import salvate."""
    query = select(ImportConfig)

    if commessa_id is not None:
        # Configurazioni specifiche per commessa + globali
        query = query.where(
            (ImportConfig.commessa_id == commessa_id) | (ImportConfig.commessa_id.is_(None))
        )

    configs = session.exec(query).scalars().all()
    return [ImportConfigRead.model_validate(c) for c in configs]


@router.post("/", response_model=ImportConfigRead, status_code=status.HTTP_201_CREATED)
def create_import_config(
    payload: ImportConfigBase,
    session: DBSession,
    commessa_id: Optional[int] = Query(default=None, description="Commessa associata (null = globale)"),
) -> ImportConfigRead:
    """Crea una nuova configurazione import."""
    config = ImportConfig(
        **payload.model_dump(),
        commessa_id=commessa_id,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return ImportConfigRead.model_validate(config)


@router.get("/{config_id}", response_model=ImportConfigRead)
def get_import_config(config_id: int, session: DBSession) -> ImportConfigRead:
    """Recupera una configurazione import specifica."""
    config = session.get(ImportConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurazione non trovata"
        )
    return ImportConfigRead.model_validate(config)


@router.put("/{config_id}", response_model=ImportConfigRead)
def update_import_config(
    config_id: int,
    payload: ImportConfigBase,
    session: DBSession,
) -> ImportConfigRead:
    """Aggiorna una configurazione import esistente."""
    config = session.get(ImportConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurazione non trovata"
        )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    session.add(config)
    session.commit()
    session.refresh(config)
    return ImportConfigRead.model_validate(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_import_config(config_id: int, session: DBSession):
    """Elimina una configurazione import."""
    config = session.get(ImportConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurazione non trovata"
        )

    session.delete(config)
    session.commit()
