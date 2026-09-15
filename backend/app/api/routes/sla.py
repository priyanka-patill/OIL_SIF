from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.sla_service import SLAService
from app.services.sla_background_worker import sla_worker
from app.schemas.sla import (
    SLAPolicyResponse,
    SLAPolicyUpdateRequest,
    SLACountdownResponse,
    SLADashboardResponse,
    SLAAcknowledgeRequest
)
from app.schemas.orchestrator import SafetyActionResponse

router = APIRouter(prefix="/sla", tags=["SLA Monitoring & Escalation"])


@router.get("/policies", response_model=List[SLAPolicyResponse])
def get_sla_policies(db: Session = Depends(get_db)):
    """Retrieves all active dynamic SLA policies."""
    return SLAService.get_or_create_policies(db)


@router.put("/policies/{severity}", response_model=SLAPolicyResponse)
def update_sla_policy(
    severity: str,
    req: SLAPolicyUpdateRequest,
    db: Session = Depends(get_db)
):
    """Updates an SLA policy for a specific severity tier."""
    try:
        return SLAService.update_policy(db, severity, req)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/dashboard", response_model=SLADashboardResponse)
def get_sla_dashboard(db: Session = Depends(get_db)):
    """Retrieves aggregated SLA dashboard metrics and live countdown metadata."""
    return SLAService.get_sla_dashboard(db)


@router.get("/countdown/{action_id}", response_model=SLACountdownResponse)
def get_action_countdown(
    action_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves live countdown, remaining seconds, and SLA state for a single action."""
    try:
        data = SLAService.get_action_countdown(db, action_id)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/acknowledge/{action_id}", response_model=SafetyActionResponse)
def acknowledge_action(
    action_id: str,
    req: SLAAcknowledgeRequest,
    db: Session = Depends(get_db)
):
    """Records human acknowledgement for an action, halting SLA breach countdown."""
    try:
        act = SLAService.acknowledge_action(db, action_id, req)
        return act
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/evaluate-now", response_model=Dict[str, Any])
def evaluate_actions_now(db: Session = Depends(get_db)):
    """Triggers an immediate SLA audit and idempotent escalation evaluation cycle."""
    res = sla_worker.run_cycle(db=db)
    return res
