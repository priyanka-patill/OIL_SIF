from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.action import (
    ActionUpdateRequest,
    ActionItemResponse,
    ActionStatsResponse,
    ActionHistoryResponse
)
from app.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["Action Center & Assignments"])


@router.get("", response_model=PaginatedResponse[ActionItemResponse])
def get_actions(
    dataset_id: Optional[str] = Query(None, description="Optional dataset filter"),
    status: Optional[str] = Query(None, description="Filter: Open, In Progress, Closed, Overdue"),
    department: Optional[str] = Query(None, description="Filter by department"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    search: Optional[str] = Query(None, description="Keyword search across problem, action, assignee"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve action items categorized across Open, In Progress, Closed, and Overdue statuses.
    """
    items, total = ActionService.get_actions(
        db=db,
        dataset_id=dataset_id,
        status=status,
        department=department,
        risk_level=risk_level,
        assigned_to=assigned_to,
        search=search,
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


@router.get("/stats", response_model=ActionStatsResponse)
def get_action_stats(
    dataset_id: Optional[str] = Query(None, description="Optional dataset filter"),
    db: Session = Depends(get_db)
):
    """
    Get KPI counts for Action Center (Open, In Progress, Closed, Overdue, Unassigned).
    """
    return ActionService.get_action_stats(db=db, dataset_id=dataset_id)


@router.patch("/{report_id}", response_model=ActionItemResponse)
def update_action(
    report_id: str,
    req: ActionUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Assign action, update status, add due date, add comments, mark completed, or verify closure.
    Automatically generates immutable action audit history.
    """
    try:
        return ActionService.update_action(db=db, report_id=report_id, req=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{report_id}/history", response_model=List[ActionHistoryResponse])
def get_action_history(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full audit trail of action modifications for a specific safety report.
    """
    return ActionService.get_action_history(db=db, report_id=report_id)
