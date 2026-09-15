from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.report import (
    SafetyReportResponse,
    SafetyReportDetailResponse,
    ReportCountResponse,
    SafetyReportCreate,
    SafetyReportUpdate,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Safety Reports"])


@router.post("", response_model=SafetyReportDetailResponse, status_code=status.HTTP_201_CREATED)
def create_safety_report(
    report_data: SafetyReportCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new safety report directly from supervisor input.
    Validates natural-language observation, assigns a unique Report ID (e.g. OIL-2026-000124),
    saves original observation, sets analysis status, and triggers background AI analysis.
    """
    try:
        return ReportService.create_report(db=db, report_data=report_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report creation failed: {str(e)}")


@router.get("", response_model=PaginatedResponse[SafetyReportResponse])
def get_reports(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery unit"),
    equipment: Optional[str] = Query(None, description="Filter by equipment ID"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    department: Optional[str] = Query(None, description="Filter by department"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (Low, Medium, High)"),
    action_status: Optional[str] = Query(None, description="Filter by action status (Open, In Progress, Closed, Overdue)"),
    immediate_cause: Optional[str] = Query(None, description="Filter by immediate cause"),
    potential_consequence: Optional[str] = Query(None, description="Filter by potential consequence"),
    high_potential: Optional[bool] = Query(None, description="Filter by high potential flag"),
    date_from: Optional[datetime] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date filter (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Keyword search across description, causes, and actions"),
    sort_by: str = Query("report_date", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Query normalized safety reports with multi-attribute filtering, keyword search, 
    sorting, and pagination.
    """
    items, total = ReportService.get_reports(
        db=db,
        dataset_id=dataset_id,
        refinery_unit=refinery_unit,
        equipment=equipment,
        work_type=work_type,
        department=department,
        risk_level=risk_level,
        action_status=action_status,
        immediate_cause=immediate_cause,
        potential_consequence=potential_consequence,
        high_potential=high_potential,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/count", response_model=ReportCountResponse)
def get_report_counts(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieve report counts and breakdowns across Risk Levels, Departments, 
    Refinery Units, Action Statuses, and Work Types.
    """
    return ReportService.get_report_counts(db=db, dataset_id=dataset_id)


@router.get("/{report_id}", response_model=SafetyReportDetailResponse)
def get_report_detail(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve single safety report with canonical normalized fields AND the 
    100% untouched raw source data.
    """
    report = ReportService.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety report not found")
    return report


@router.put("/{report_id}", response_model=SafetyReportDetailResponse)
def update_safety_report(
    report_id: str,
    update_data: SafetyReportUpdate,
    db: Session = Depends(get_db)
):
    """
    Update safety report details (e.g. human supervisor correction or action details).
    """
    updated = ReportService.update_report(db=db, report_id=report_id, update_data=update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Safety report {report_id} not found")
    return updated

