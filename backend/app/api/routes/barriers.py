from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.barrier_service import BarrierService
from app.schemas.barriers import (
    ReportBarrierResponse,
    UnitBarrierResponse,
    CriticalBarriersResponse,
    BarrierSummaryResponse,
    BarrierConvergenceResponse
)

router = APIRouter(prefix="/barriers", tags=["Swiss Cheese Safety Barrier Model"])


@router.get(
    "/report/{report_id}",
    response_model=ReportBarrierResponse,
    summary="Get Reason's Swiss Cheese barrier assessment & multi-barrier convergence for a report"
)
def get_report_barriers(
    report_id: str,
    db: Session = Depends(get_db)
):
    result = BarrierService.get_report_barriers(db=db, report_id=report_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID '{report_id}' not found."
        )
    return result


@router.get(
    "/unit/{unit_id}",
    response_model=UnitBarrierResponse,
    summary="Get unit-wide barrier defense health and equipment convergences"
)
def get_unit_barriers(
    unit_id: str,
    db: Session = Depends(get_db)
):
    return BarrierService.get_unit_barriers(db=db, unit_id=unit_id)


@router.get(
    "/critical",
    response_model=CriticalBarriersResponse,
    summary="Get critical multi-barrier convergences where 3+ defense layers are compromised"
)
def get_critical_barriers(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of critical convergences to return"),
    db: Session = Depends(get_db)
):
    return BarrierService.get_critical_barriers(db=db, limit=limit)


@router.get(
    "/summary",
    response_model=BarrierSummaryResponse,
    summary="Get platform-wide barrier defense summary, degradation rates, and top weakened barriers"
)
def get_barrier_summary(
    db: Session = Depends(get_db)
):
    return BarrierService.get_barrier_summary(db=db)


@router.get(
    "/convergence",
    response_model=BarrierConvergenceResponse,
    summary="Get all multi-barrier convergence sequences and Swiss Cheese alignment diagrams"
)
def get_barrier_convergences(
    db: Session = Depends(get_db)
):
    return BarrierService.get_barrier_convergences(db=db)


@router.post(
    "/assess",
    summary="Trigger idempotent batch barrier assessment across reports"
)
def assess_barriers(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    count = BarrierService.batch_assess_barriers(db=db, dataset_id=dataset_id)
    return {
        "status": "success",
        "message": f"Successfully computed and stored {count} barrier assessments.",
        "assessments_created": count
    }
