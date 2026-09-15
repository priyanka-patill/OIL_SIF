from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.sif_escalation_service import SIFEscalationService
from app.schemas.sif_escalation import (
    ReportSIFEscalationResponse,
    CriticalEscalationsResponse,
    HighEscalationsResponse,
    SIFEscalationSummaryResponse,
    UnitSIFEscalationResponse
)

router = APIRouter(prefix="/sif/escalation", tags=["SIF Precursor Escalation Engine"])


@router.get(
    "/report/{report_id}",
    response_model=ReportSIFEscalationResponse,
    summary="Get multi-dimensional SIF Precursor escalation evaluation & 7-stage scenario for a report"
)
def get_report_escalation(
    report_id: str,
    db: Session = Depends(get_db)
):
    result = SIFEscalationService.get_report_escalation(db=db, report_id=report_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID '{report_id}' not found."
        )
    return result


@router.get(
    "/critical",
    response_model=CriticalEscalationsResponse,
    summary="Get all safety exposures evaluated at CRITICAL SIF escalation severity"
)
def get_critical_escalations(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of critical items to return"),
    db: Session = Depends(get_db)
):
    return SIFEscalationService.get_critical_escalations(db=db, limit=limit)


@router.get(
    "/high",
    response_model=HighEscalationsResponse,
    summary="Get all safety exposures evaluated at HIGH or CRITICAL SIF escalation severity"
)
def get_high_escalations(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of high/critical items to return"),
    db: Session = Depends(get_db)
):
    return SIFEscalationService.get_high_escalations(db=db, limit=limit)


@router.get(
    "/summary",
    response_model=SIFEscalationSummaryResponse,
    summary="Get platform-wide SIF Precursor escalation summary and precursor rate"
)
def get_escalation_summary(
    db: Session = Depends(get_db)
):
    return SIFEscalationService.get_escalation_summary(db=db)


@router.get(
    "/unit/{unit_id}",
    response_model=UnitSIFEscalationResponse,
    summary="Get unit-level SIF Precursor escalation severity, dominant hazards, and preventive imperative"
)
def get_unit_escalation(
    unit_id: str,
    db: Session = Depends(get_db)
):
    return SIFEscalationService.get_unit_escalation(db=db, unit_id=unit_id)


@router.post(
    "/assess",
    summary="Trigger batch SIF Precursor escalation calculation and persistence"
)
def assess_escalations(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    count = SIFEscalationService.batch_assess_escalations(db=db, dataset_id=dataset_id)
    return {
        "status": "success",
        "message": f"Successfully computed and stored {count} SIF escalation assessments.",
        "assessments_created": count
    }
