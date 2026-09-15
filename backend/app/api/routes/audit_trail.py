from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.database.session import get_db
from app.models.system_audit_log import SystemAuditLog
from app.schemas.audit_trail import (
    SystemAuditLogResponse,
    AuditTimelineResponse,
    AuditStatsResponse
)
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-trail", tags=["System Audit Trail & Governance"])


@router.get("", response_model=PaginatedResponse[SystemAuditLogResponse])
def get_audit_trail_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. SIF_ESCALATION, SLA_BREACH)"),
    report_id: Optional[str] = Query(None, description="Filter by report ID"),
    is_simulated: Optional[bool] = Query(None, description="Filter by simulated vs real events"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated immutable platform audit log stream.
    """
    query = select(SystemAuditLog)
    if event_type:
        query = query.where(SystemAuditLog.event_type == event_type.upper())
    if report_id:
        query = query.where(SystemAuditLog.report_id == str(report_id))
    if is_simulated is not None:
        query = query.where(SystemAuditLog.is_simulated == is_simulated)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    offset = (page - 1) * page_size
    items = list(db.scalars(query.order_by(desc(SystemAuditLog.timestamp)).offset(offset).limit(page_size)).all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=[SystemAuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/report/{report_id}", response_model=AuditTimelineResponse)
def get_report_timeline(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full chronological audit timeline for a specific safety report exposure.
    """
    return AuditService.get_timeline_for_report(db, report_id)


@router.get("/action/{action_id}", response_model=AuditTimelineResponse)
def get_action_timeline(
    action_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full chronological audit timeline for a specific action lifecycle.
    """
    return AuditService.get_timeline_for_action(db, action_id)


@router.get("/stats", response_model=AuditStatsResponse)
def get_audit_statistics(
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregate statistics across all platform audit events.
    """
    return AuditService.get_audit_stats(db)
