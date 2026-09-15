from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.safety_hold_service import SafetyHoldService
from app.schemas.safety_hold import (
    SafetyHoldCreateRequest,
    SafetyHoldReviewRequest,
    SafetyHoldReassessRequest,
    SafetyHoldReleaseRequest,
    SafetyHoldVerifyReleaseRequest,
    SafetyHoldResponse,
    SafetyHoldListResponse
)

router = APIRouter(prefix="/safety-holds", tags=["Safety Holds"])


@router.post("/request", response_model=SafetyHoldResponse, status_code=status.HTTP_201_CREATED)
def request_safety_hold(
    req: SafetyHoldCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Submits an application-level Digital Safety Hold request.
    Freezes digital workflow operations for the targeted exposure upon approval.
    """
    try:
        hold = SafetyHoldService.request_safety_hold(db, req)
        return hold
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to request safety hold: {str(e)}"
        )


@router.get("", response_model=SafetyHoldListResponse)
def list_safety_holds(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. WORKFLOW_BLOCKED)"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery process unit"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Retrieves paginated safety holds with optional filtering."""
    items, total = SafetyHoldService.get_safety_holds(
        db, status=status_filter, refinery_unit=refinery_unit, page=page, page_size=page_size
    )
    return SafetyHoldListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/{hold_id}", response_model=SafetyHoldResponse)
def get_safety_hold(
    hold_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single safety hold by unique UUID."""
    hold = SafetyHoldService.get_safety_hold_by_id(db, hold_id)
    if not hold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety hold with ID '{hold_id}' not found."
        )
    return hold


@router.post("/{hold_id}/review", response_model=SafetyHoldResponse)
def review_safety_hold(
    hold_id: str,
    req: SafetyHoldReviewRequest,
    db: Session = Depends(get_db)
):
    """Reviews and approves/rejects safety hold, transitioning to WORKFLOW_BLOCKED if approved."""
    try:
        hold = SafetyHoldService.review_safety_hold(db, hold_id, req)
        return hold
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{hold_id}/reassess", response_model=SafetyHoldResponse)
def reassess_safety_hold(
    hold_id: str,
    req: SafetyHoldReassessRequest,
    db: Session = Depends(get_db)
):
    """Transitions safety hold into active reassessment state."""
    try:
        hold = SafetyHoldService.reassess_safety_hold(db, hold_id, req)
        return hold
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{hold_id}/request-release", response_model=SafetyHoldResponse)
def request_safety_hold_release(
    hold_id: str,
    req: SafetyHoldReleaseRequest,
    db: Session = Depends(get_db)
):
    """Submits request to release safety hold with remediation details."""
    try:
        hold = SafetyHoldService.request_release(db, hold_id, req)
        return hold
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{hold_id}/verify-release", response_model=SafetyHoldResponse)
def verify_and_release_safety_hold(
    hold_id: str,
    req: SafetyHoldVerifyReleaseRequest,
    db: Session = Depends(get_db)
):
    """Verifies remediation walkdown and releases the digital safety hold."""
    try:
        hold = SafetyHoldService.verify_and_release(db, hold_id, req)
        return hold
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
