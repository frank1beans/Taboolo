from fastapi import APIRouter

from app.api.deps import DBSession, require_role, UserRole
from app.schemas import DashboardStatsSchema
from app.services.analysis.dashboard import DashboardService

router = APIRouter(
    dependencies=[
        require_role(
            [UserRole.viewer, UserRole.computista, UserRole.project_manager, UserRole.admin]
        )
    ]
)


@router.get("/stats", response_model=DashboardStatsSchema)
def get_dashboard_stats(session: DBSession) -> DashboardStatsSchema:
    return DashboardService.get_dashboard_stats(session)
