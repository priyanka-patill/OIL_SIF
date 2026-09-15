from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.action_history import ActionHistory
from app.schemas.common import PaginatedResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.action import ActionHistoryResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs & Governance"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def get_audit_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type (e.g. EMAIL_SENT, ACTION_UPDATED)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. REPORT_ACTION, NOTIFICATION)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve platform audit log stream for safety modifications, data uploads, and notification events.
    """
    query = select(AuditLog)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    offset = (page - 1) * page_size
    items = list(db.scalars(query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(page_size)).all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/actions", response_model=PaginatedResponse[ActionHistoryResponse])
def get_all_action_histories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve system-wide action changes and assignment histories.
    """
    query = select(ActionHistory)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    offset = (page - 1) * page_size
    items = list(db.scalars(query.order_by(desc(ActionHistory.timestamp)).offset(offset).limit(page_size)).all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=[ActionHistoryResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
