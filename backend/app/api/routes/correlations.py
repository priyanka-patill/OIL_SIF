from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.correlation_service import CorrelationService
from app.schemas.correlations import (
    ReportCorrelationResponse,
    UnitCorrelationsResponse,
    HighRiskCorrelationsResponse,
    RecurringCorrelationsResponse,
    MultiFactorConvergenceResponse,
    CorrelationSummaryResponse
)

router = APIRouter(prefix="/correlations", tags=["Multi-Factor Safety Correlations"])


@router.get(
    "/report/{report_id}",
    response_model=ReportCorrelationResponse,
    summary="Get multi-factor correlations and evidence statement for a specific report"
)
def get_report_correlations(
    report_id: str,
    db: Session = Depends(get_db)
):
    result = CorrelationService.correlate_single_report(db=db, report_id=report_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID '{report_id}' not found."
        )
    return result


@router.get(
    "/unit/{unit_id}",
    response_model=UnitCorrelationsResponse,
    summary="Get multi-factor correlations and equipment clusters for a refinery unit"
)
def get_unit_correlations(
    unit_id: str,
    db: Session = Depends(get_db)
):
    return CorrelationService.get_unit_correlations(db=db, unit_id=unit_id)


@router.get(
    "/high-risk",
    response_model=HighRiskCorrelationsResponse,
    summary="Get high-risk and critical multi-barrier collapse correlations"
)
def get_high_risk_correlations(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    return CorrelationService.get_high_risk_correlations(db=db, limit=limit)


@router.get(
    "/recurring",
    response_model=RecurringCorrelationsResponse,
    summary="Get recurring issue correlations and recurring equipment clusters"
)
def get_recurring_correlations(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    return CorrelationService.get_recurring_correlations(db=db, limit=limit)


@router.get(
    "/multi-factor",
    response_model=MultiFactorConvergenceResponse,
    summary="Get 2-factor, 3-factor, and 4-factor multi-barrier convergence clusters"
)
def get_multi_factor_convergences(
    db: Session = Depends(get_db)
):
    return CorrelationService.get_multi_factor_convergences(db=db)


@router.get(
    "/summary",
    response_model=CorrelationSummaryResponse,
    summary="Get overall correlation metrics, factor co-occurrence matrix, and dataset provenance"
)
def get_correlation_summary(
    db: Session = Depends(get_db)
):
    return CorrelationService.get_correlation_summary(db=db)


@router.post(
    "/compute",
    summary="Trigger idempotent batch correlation computation across reports"
)
def compute_correlations(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    count = CorrelationService.batch_compute_correlations(db=db, dataset_id=dataset_id)
    return {
        "status": "success",
        "message": f"Successfully computed and stored {count} safety correlations.",
        "correlations_created": count
    }
