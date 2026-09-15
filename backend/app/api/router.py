from fastapi import APIRouter
from app.api.routes import (
    health,
    datasets,
    reports,
    data_quality,
    metadata,
    sif,
    chat,
    actions,
    notifications,
    export_reports,
    audit_logs,
    factors,
    correlations,
    barriers,
    bdi,
    sif_escalation,
    orchestrator,
    safety_holds,
    sla,
    audit_trail,
    human_feedback,
    admin_config,
    demo
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(datasets.router)
api_router.include_router(reports.router)
api_router.include_router(data_quality.router)
api_router.include_router(metadata.router)
api_router.include_router(sif.router)
api_router.include_router(chat.router)
api_router.include_router(actions.router)
api_router.include_router(notifications.router)
api_router.include_router(export_reports.router)
api_router.include_router(audit_logs.router)
api_router.include_router(factors.router)
api_router.include_router(correlations.router)
api_router.include_router(barriers.router)
api_router.include_router(bdi.router)
api_router.include_router(sif_escalation.router)
api_router.include_router(orchestrator.router)
api_router.include_router(safety_holds.router)
api_router.include_router(sla.router)
api_router.include_router(audit_trail.router)
api_router.include_router(human_feedback.router)
api_router.include_router(admin_config.router)
api_router.include_router(demo.router)




