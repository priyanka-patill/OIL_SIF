from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.sif import (
    ReportAnalysisResponse,
    SIFSummaryResponse,
    RecurringIssuesResponse,
    BatchAnalysisResponse,
    AIFeedbackCreate,
    AIFeedbackResponse
)
from app.services.sif_service import SIFService

router = APIRouter(tags=["AI/NLP Engine & SIF Preventive Intelligence"])


@router.post("/reports/{report_id}/analyze", response_model=ReportAnalysisResponse)
def analyze_report_endpoint(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Run AI/NLP analysis on a single safety report: extracts PPE entities, 
    assesses SIF precursor potential, synthesizes immediate/preventive actions, 
    and models the 6-stage risk-escalation scenario. Supports retrying failed analysis.
    """
    from app.models.safety_report import SafetyReport
    report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

    report.analysis_status = "IN_PROGRESS"
    db.commit()

    try:
        analysis = SIFService.analyze_report(db=db, report_id=report_id)
        if not analysis:
            report.analysis_status = "FAILED"
            db.commit()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI analysis returned empty result")
        report.analysis_status = "COMPLETED"
        db.commit()
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        report.analysis_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI analysis failed: {str(e)}")


@router.post("/reports/analyze-all", response_model=BatchAnalysisResponse)
def batch_analyze_reports(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Run batch AI analysis across all ingested safety reports in a dataset.
    """
    return SIFService.batch_analyze_dataset(db=db, dataset_id=dataset_id)


@router.get("/reports/{report_id}/analysis", response_model=ReportAnalysisResponse)
def get_report_analysis(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve SIF precursor classification, AI predicted risk, explainable reasoning, 
    action recommendations, and the 6-stage risk-escalation scenario for a report.
    """
    analysis = SIFService.get_analysis_by_report_id(db=db, report_id=report_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis not found for report {report_id}")
    return analysis


@router.get("/sif/summary", response_model=SIFSummaryResponse)
def get_sif_summary(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieve executive SIF intelligence summary: overall precursor detection rate, 
    AI vs recorded risk comparison, SIF category distribution, and top hotspot units.
    """
    return SIFService.get_sif_summary(db=db, dataset_id=dataset_id)


@router.get("/sif/high-risk", response_model=PaginatedResponse[ReportAnalysisResponse])
def get_high_risk_sif_reports(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Query reports flagged as SIF Precursors (YES) or evaluated at High/Critical AI Risk.
    """
    items, total = SIFService.get_high_risk_reports(
        db=db, dataset_id=dataset_id, page=page, page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/sif/high-potential")
def get_high_potential_sif(
    db: Session = Depends(get_db)
):
    """
    Retrieve dedicated High Potential Near Miss intelligence and multi-barrier failure patterns.
    """
    from app.services.factor_service import FactorService
    return FactorService.get_high_potential_intelligence(db=db)


@router.get("/sif/recurring", response_model=RecurringIssuesResponse)
def get_recurring_issues(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Discover recurring safety hotspots across Equipment, Process Units, 
    Departments, and Work Types.
    """
    return SIFService.get_recurring_issues(db=db, dataset_id=dataset_id)


@router.post("/ai-feedback", response_model=AIFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_ai_feedback(
    feedback: AIFeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit human safety officer review or override. Preserves original AI assessment 
    while storing expert human feedback.
    """
    try:
        return SIFService.submit_feedback(db=db, feedback_data=feedback)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ai-feedback/{report_id}", response_model=List[AIFeedbackResponse])
def get_ai_feedback_for_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all human safety officer reviews submitted for a specific report.
    """
    return SIFService.get_feedback_by_report_id(db=db, report_id=report_id)


@router.get("/sif/density")
def get_sif_density(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieve SIF Precursor Density analytics and rankings across all available dimensions.
    """
    from app.services.sif_density_service import SIFDensityService
    return SIFDensityService.calculate_sif_density(db=db, dataset_id=dataset_id)


@router.get("/sif/multi-factor")
def get_multi_factor_analytics(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieve Multi-Factor Swiss Cheese compound risk breakdown and factor combinations.
    """
    from app.services.factor_service import FactorService
    return FactorService.get_factor_combinations(db=db, dataset_id=dataset_id)

