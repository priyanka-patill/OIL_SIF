from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.bdi_service import BDIService
from app.schemas.bdi import (
    ReportBDIResponse,
    UnitBDIResponse,
    HighBDIResponse,
    BDISummaryResponse,
    BDITrendsResponse,
    BDIConfigResponse
)

router = APIRouter(prefix="/bdi", tags=["Barrier Degradation Index (BDI)"])


@router.get(
    "/report/{report_id}",
    response_model=ReportBDIResponse,
    summary="Get explainable Barrier Degradation Index (BDI) for a specific safety report"
)
def get_report_bdi(
    report_id: str,
    db: Session = Depends(get_db)
):
    result = BDIService.get_report_bdi(db=db, report_id=report_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID '{report_id}' not found."
        )
    return result


@router.get(
    "/unit/{unit_id}",
    response_model=UnitBDIResponse,
    summary="Get unit-level Barrier Degradation Index with weighted barrier density"
)
def get_unit_bdi(
    unit_id: str,
    db: Session = Depends(get_db)
):
    return BDIService.get_unit_bdi(db=db, unit_id=unit_id)


@router.get(
    "/high",
    response_model=HighBDIResponse,
    summary="Get safety exposures with high or severe barrier degradation (BDI >= threshold)"
)
def get_high_bdi(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return"),
    threshold: float = Query(60.0, ge=0.0, le=100.0, description="Minimum BDI score threshold"),
    db: Session = Depends(get_db)
):
    return BDIService.get_high_bdi(db=db, limit=limit, threshold=threshold)


@router.get(
    "/summary",
    response_model=BDISummaryResponse,
    summary="Get platform-wide BDI score distribution, average BDI, and degraded units"
)
def get_bdi_summary(
    db: Session = Depends(get_db)
):
    return BDIService.get_bdi_summary(db=db)


@router.get(
    "/trends",
    response_model=BDITrendsResponse,
    summary="Get temporal BDI trends across periods and refinery units"
)
def get_bdi_trends(
    db: Session = Depends(get_db)
):
    return BDIService.get_bdi_trends(db=db)


@router.get(
    "/config",
    response_model=BDIConfigResponse,
    summary="Get active BDI weights, classification thresholds, and explanatory documentation"
)
def get_bdi_config():
    return BDIService.get_bdi_config()


@router.post(
    "/assess",
    summary="Trigger batch BDI calculation and persistence into database"
)
def assess_bdi(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    count = BDIService.batch_assess_bdi(db=db, dataset_id=dataset_id)
    return {
        "status": "success",
        "message": f"Successfully computed and stored {count} BDI assessments.",
        "assessments_created": count
    }
