import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine, init_db
from app.database.base import Base
from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.barrier_degradation_assessment import BarrierDegradationAssessment
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.models.sif_escalation_assessment import SIFEscalationAssessment
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.safety_correlation import SafetyCorrelation
from app.services.ai.chat_service import ChatService


@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_phase7_chat_queries(db_session: Session):
    # Setup test dataset and report
    ds = Dataset(
        dataset_name="Phase 7 Intelligence Test Dataset",
        description="Dataset for testing Phase 7 chat and UI integration",
        original_filename="phase7_test.csv",
        file_type="csv"
    )
    db_session.add(ds)
    db_session.flush()

    rep = SafetyReport(
        dataset_id=ds.id,
        original_id="P7-REP-001",
        raw_data={"Observation": "High pressure valve leakage with degraded seal and missing PPE"},
        description="High pressure valve leakage with degraded seal and missing personal protective equipment",
        risk_level="High",
        potential_consequence="Fatal hydrocarbon fire or severe thermal burns",
        immediate_cause="Maintenance backlog and worn seal",
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        department="Operations",
        work_type="Hot Work",
        repeated_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        ppe_issue=True
    )
    db_session.add(rep)
    db_session.flush()

    # Add BarrierDegradationAssessment
    bdi = BarrierDegradationAssessment(
        report_id=rep.id,
        dataset_id=ds.id,
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        bdi_score=78.5,
        classification="SIGNIFICANT",
        component_scores={"failed_barriers": 40.0, "repeated_issues": 20.0, "supervisor_factor": 18.5},
        contributing_factors=["PPE Non-Compliance", "Maintenance Backlog"],
        barrier_states_summary={"PPE": "FAILED", "Maintenance": "DEGRADED"},
        evidence={"dominant_degraded_barriers": ["PPE / Personal Protective Equipment", "Maintenance / Equipment Integrity"], "dominant_safety_factors": ["PPE Non-Compliance", "Maintenance Backlog"]}
    )
    db_session.add(bdi)

    # Add SafetyBarrierAssessment
    bar1 = SafetyBarrierAssessment(
        report_id=rep.id,
        dataset_id=ds.id,
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        barrier_name="PPE / Personal Protective Equipment",
        barrier_category="Physical / Personnel Barrier",
        status="FAILED",
        confidence=0.95,
        evidence={"reasoning": "Personnel entered active zone without flame-resistant suit."}
    )
    bar2 = SafetyBarrierAssessment(
        report_id=rep.id,
        dataset_id=ds.id,
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        barrier_name="Maintenance / Equipment Integrity",
        barrier_category="Physical / Engineering Barrier",
        status="DEGRADED",
        confidence=0.90,
        evidence={"reasoning": "Valve seal inspection deferred over 90 days."}
    )
    db_session.add_all([bar1, bar2])

    # Add SIFEscalationAssessment
    sif_esc = SIFEscalationAssessment(
        report_id=rep.id,
        dataset_id=ds.id,
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        severity="CRITICAL",
        sif_precursor_status=True,
        bdi_score=78.5,
        bdi_classification="SIGNIFICANT",
        reasoning={"why_escalated": "Unmitigated high pressure hydrocarbon exposure converging with failed PPE barrier."},
        immediate_actions=["Depressurize CDU-1 valve V-101-A and enforce area exclusion zone."],
        preventive_actions=["Replace valve packing seals and audit pre-job safety checklists."],
        contributing_factors=["High Pressure Hydrocarbon", "Failed PPE", "Maintenance Delay"],
        escalation_scenario=[
            {"stage_number": 1, "stage_name": "Latent Condition", "description": "Seal wear", "is_active": True},
            {"stage_number": 2, "stage_name": "Trigger", "description": "Pressure surge", "is_active": True},
            {"stage_number": 7, "stage_name": "SIF Outcome", "description": "Hydrocarbon flash fire", "is_active": True}
        ]
    )
    db_session.add(sif_esc)

    # Add SafetyAction
    act = SafetyAction(
        report_id=rep.id,
        dataset_id=ds.id,
        action_type="CONTAINMENT",
        severity="CRITICAL",
        title="Immediate CDU-1 Valve Isolation & Seal Replacement",
        description="Isolate valve V-101-A immediately and replace degraded seal packing.",
        assigned_role="Unit In-Charge",
        status="DISPATCHED",
        sla_state="NORMAL",
        escalation_level=0
    )
    db_session.add(act)

    # Add SafetyHold
    hold = SafetyHold(
        report_id=rep.id,
        action_id=act.id,
        refinery_unit="Crude Distillation Unit (CDU-1)",
        equipment="V-101-A",
        trigger="CRITICAL SIF Precursor",
        reason="Active hydrocarbon leak with degraded seal",
        status="HOLD_APPROVED",
        requested_by="AI Safety Orchestrator"
    )
    db_session.add(hold)
    db_session.commit()

    # 1. Test Report-Specific QA
    res1 = ChatService.process_chat_message(db_session, "Why was this report escalated?", report_id=rep.id)
    assert "SIF Precursor Escalation Analysis" in res1["reply"]
    assert "CRITICAL" in res1["reply"]

    res2 = ChatService.process_chat_message(db_session, "Why is BDI high?", report_id=rep.id)
    assert "Barrier Degradation Index (BDI) Breakdown" in res2["reply"]
    assert "78.5" in res2["reply"]

    res3 = ChatService.process_chat_message(db_session, "Which barriers are degraded?", report_id=rep.id)
    assert "Swiss Cheese Barrier Defense Evaluation" in res3["reply"]
    assert "PPE" in res3["reply"]

    res4 = ChatService.process_chat_message(db_session, "What is the 7-stage precursor pathway?", report_id=rep.id)
    assert "7-Stage Precursor Escalation Pathway" in res4["reply"]

    res5 = ChatService.process_chat_message(db_session, "What is the SLA and Safety Hold status?", report_id=rep.id)
    assert "SLA & Safety Hold Governance" in res5["reply"]
    assert "HOLD_APPROVED" in res5["reply"]

    # 2. Test Global Queries
    res_glob1 = ChatService.process_chat_message(db_session, "Show critical SIF precursors.", dataset_id=ds.id)
    assert "Critical SIF Precursor Intelligence" in res_glob1["reply"]

    res_glob2 = ChatService.process_chat_message(db_session, "Which refinery units have the highest BDI?", dataset_id=ds.id)
    assert "Refinery Units Ranked by Barrier Degradation Index" in res_glob2["reply"]

    res_glob3 = ChatService.process_chat_message(db_session, "Which safety barriers are degraded or failed?", dataset_id=ds.id)
    assert "Swiss Cheese Safety Barrier Degradation Intelligence" in res_glob3["reply"]

    res_glob4 = ChatService.process_chat_message(db_session, "Which factors are converging?", dataset_id=ds.id)
    assert "Multi-Factor Convergence Breakdown" in res_glob4["reply"]

    res_glob5 = ChatService.process_chat_message(db_session, "Show active safety holds.", dataset_id=ds.id)
    assert "Action Governance & Digital Safety Hold Telemetry" in res_glob5["reply"]
