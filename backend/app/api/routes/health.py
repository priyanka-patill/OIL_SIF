from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from app.database.session import get_db
from app.schemas.common import HealthResponse
from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.config.settings import settings

router = APIRouter(tags=["System Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """System health check verifying database connection and operational readiness."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    total_datasets = db.scalar(select(func.count(Dataset.id)).where(Dataset.is_active == True)) or 0
    total_reports = db.scalar(select(func.count(SafetyReport.id))) or 0

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        database=db_status,
        total_datasets=total_datasets,
        total_reports=total_reports
    )
