from fastapi import APIRouter, HTTPException

from app.api.deps import DBSession, require_role, UserRole
from app.schemas import ComputoWbsSummary
from app.services import AnalysisService

router = APIRouter(
    dependencies=[
        require_role(
            [UserRole.viewer, UserRole.computista, UserRole.project_manager, UserRole.admin]
        )
    ]
)


@router.get("/{computo_id}/wbs", response_model=ComputoWbsSummary)
def get_computo_wbs(computo_id: int, session: DBSession) -> ComputoWbsSummary:
    try:
        return AnalysisService.get_wbs_summary(session, computo_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
