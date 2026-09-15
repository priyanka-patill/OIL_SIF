from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.demo import (
    DemoStatusResponse,
    DemoToggleRequest,
    DemoLoadScenarioRequest,
    DemoTimeTravelRequest,
    DemoSimulateStepRequest,
    DemoScenarioExecutionResponse
)
from app.services.demo_simulation_service import DemoSimulationService

router = APIRouter(prefix="/demo", tags=["Demo & Simulation Engine"])


@router.get("/status", response_model=DemoStatusResponse)
def get_demo_status(
    db: Session = Depends(get_db)
):
    """
    Get current simulation mode state, virtual time offset, and loaded scenario.
    """
    return DemoSimulationService.get_status(db)


@router.post("/toggle", response_model=DemoStatusResponse)
def toggle_demo_mode(
    payload: DemoToggleRequest,
    db: Session = Depends(get_db)
):
    """
    Enable or disable Demonstration / Simulation Mode.
    When enabled, external notifications are suppressed.
    """
    return DemoSimulationService.set_demo_mode(db, payload.enabled)


@router.post("/load-scenario", response_model=DemoScenarioExecutionResponse)
def load_and_execute_scenario(
    payload: DemoLoadScenarioRequest,
    db: Session = Depends(get_db)
):
    """
    Instantly loads and executes one of the 5 realistic demo scenarios:
    NORMAL, MINOR_PRECURSOR, MULTI_FACTOR_CONVERGENCE, HIGH_SIF_PRECURSOR, CRITICAL_SIF_PRECURSOR.
    Runs detection -> correlation -> barrier degradation -> BDI -> SIF escalation -> action -> hold -> SLA.
    """
    return DemoSimulationService.execute_scenario(
        db=db,
        scenario_type=payload.scenario_type,
        custom_unit=payload.refinery_unit
    )


@router.post("/time-travel")
def time_travel_simulation(
    payload: DemoTimeTravelRequest,
    db: Session = Depends(get_db)
):
    """
    Fast-forward virtual time (e.g. +15m, +30m, +60m) to simulate SLA reminders,
    approaching warnings, SLA breaches, and supervisor escalations without real waiting.
    """
    return DemoSimulationService.time_travel(
        db=db,
        advance_minutes=payload.advance_minutes,
        action_id=payload.action_id
    )


@router.post("/simulate-step")
def simulate_action_step(
    payload: DemoSimulateStepRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate individual action lifecycle steps:
    ACKNOWLEDGE, CONTAIN, VERIFY, CLOSE, ESCALATE, TRIGGER_BREACH.
    """
    try:
        return DemoSimulationService.simulate_step(
            db=db,
            step=payload.step,
            action_id=payload.action_id,
            actor_name=payload.actor_name,
            actor_role=payload.actor_role,
            notes=payload.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset")
def reset_simulation(
    db: Session = Depends(get_db)
):
    """
    Resets virtual clock and demo simulation state.
    """
    return DemoSimulationService.reset_demo_state(db)
