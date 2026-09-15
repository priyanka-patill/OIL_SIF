from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.orchestrator import (
    SafetyActionResponse,
    SafetyActionApprovalRequest,
    SafetyActionTransitionRequest,
    EmailDraftResponse,
    WebhookDispatchRequest,
    WebhookLogResponse,
    OrchestratorSummaryResponse,
    AutoOrchestrateResponse
)
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/orchestrator", tags=["AI Safety Action Orchestrator"])


@router.post(
    "/generate/{report_id}",
    response_model=SafetyActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a context-aware safety response action package for a safety report"
)
def generate_action_for_report(
    report_id: str,
    force_regenerate: bool = Query(False, description="Force create new draft even if one exists"),
    db: Session = Depends(get_db)
):
    action = OrchestrationService.generate_action_for_report(
        db=db, report_id=report_id, force_regenerate=force_regenerate
    )
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID '{report_id}' not found."
        )
    return action


@router.get(
    "/actions",
    response_model=PaginatedResponse[SafetyActionResponse],
    summary="Retrieve paginated safety actions with status, role, and severity filtering"
)
def get_actions(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING_APPROVAL, DISPATCHED, etc."),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, etc."),
    assigned_role: Optional[str] = Query(None, description="Filter by role: Unit In-Charge, Safety Officer, etc."),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    items, total = OrchestrationService.get_actions(
        db=db,
        dataset_id=dataset_id,
        status=status,
        severity=severity,
        assigned_role=assigned_role,
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


@router.get(
    "/actions/{action_id}",
    response_model=SafetyActionResponse,
    summary="Get full action package details, SLA deadlines, and audit history"
)
def get_action_by_id(
    action_id: str,
    db: Session = Depends(get_db)
):
    action = OrchestrationService.get_action_by_id(db=db, action_id=action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety action with ID '{action_id}' not found."
        )
    return action


@router.post(
    "/actions/{action_id}/approve",
    response_model=SafetyActionResponse,
    summary="Human-in-the-loop review: Approve & Send, Edit & Approve, Reject, or Cancel"
)
def approve_action(
    action_id: str,
    req: SafetyActionApprovalRequest,
    db: Session = Depends(get_db)
):
    action = OrchestrationService.approve_action(db=db, action_id=action_id, req=req)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety action with ID '{action_id}' not found."
        )
    return action


@router.post(
    "/actions/{action_id}/reject",
    response_model=SafetyActionResponse,
    summary="Reject an action package draft with recorded feedback justification"
)
def reject_action(
    action_id: str,
    req: SafetyActionApprovalRequest,
    db: Session = Depends(get_db)
):
    action = OrchestrationService.reject_action(db=db, action_id=action_id, req=req)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety action with ID '{action_id}' not found."
        )
    return action


@router.post(
    "/actions/{action_id}/transition",
    response_model=SafetyActionResponse,
    summary="Transition action through legal lifecycle states (ACKNOWLEDGED, IN_PROGRESS, CONTAINED, VERIFIED, CLOSED, ESCALATED)"
)
def transition_action_status(
    action_id: str,
    req: SafetyActionTransitionRequest,
    db: Session = Depends(get_db)
):
    try:
        return OrchestrationService.transition_action_status(db=db, action_id=action_id, req=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/actions/{action_id}/email-draft",
    response_model=EmailDraftResponse,
    summary="Get context-aware email draft distinctly separating source facts from AI recommendations"
)
def get_email_draft(
    action_id: str,
    db: Session = Depends(get_db)
):
    draft = OrchestrationService.get_email_draft(db=db, action_id=action_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety action with ID '{action_id}' not found."
        )
    return draft


@router.post(
    "/actions/{action_id}/webhook",
    response_model=WebhookLogResponse,
    summary="Trigger outbound webhook dispatch and log immutable delivery entry"
)
def dispatch_webhook(
    action_id: str,
    req: WebhookDispatchRequest,
    db: Session = Depends(get_db)
):
    try:
        return OrchestrationService.dispatch_webhook(
            db=db,
            action_id=action_id,
            endpoint=req.endpoint,
            event_type=req.event_type or "ACTION_DISPATCHED"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/summary",
    response_model=OrchestratorSummaryResponse,
    summary="Get platform-wide orchestrator metrics, active holds, and SLA breach counts"
)
def get_orchestrator_summary(
    db: Session = Depends(get_db)
):
    return OrchestrationService.get_orchestrator_summary(db=db)


@router.post(
    "/auto-orchestrate",
    response_model=AutoOrchestrateResponse,
    summary="Scan dataset and automatically draft action packages for all High/Critical SIF precursors"
)
def auto_orchestrate(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    return OrchestrationService.auto_orchestrate_high_critical(db=db, dataset_id=dataset_id)
