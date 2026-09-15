import os
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.sla_policy import SLAPolicy
from app.models.escalation_log import EscalationLog
from app.models.email_log import EmailLog
from app.services.orchestration_service import OrchestrationService
from app.services.safety_hold_service import SafetyHoldService
from app.services.sla_service import SLAService
from app.services.ai.sla_engine import SLAEngine
from app.services.sla_background_worker import sla_worker
from app.schemas.safety_hold import (
    SafetyHoldCreateRequest,
    SafetyHoldReviewRequest,
    SafetyHoldReassessRequest,
    SafetyHoldReleaseRequest,
    SafetyHoldVerifyReleaseRequest
)
from app.schemas.sla import (
    SLAPolicyUpdateRequest,
    SLAAcknowledgeRequest
)
from app.schemas.orchestrator import SafetyActionTransitionRequest


@pytest.fixture(scope="function")
def phase6_test_data(db_session: Session):
    """
    Sets up controlled reports, datasets, and ensures default SLA policies are initialized.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="Phase 6 SLA & Holds Test Dataset",
        original_filename="phase6_test.xlsx",
        sheet_name="SLA_Test",
        file_type="xlsx",
        row_count=2,
        status="ready"
    )
    db_session.add(dataset)

    # 1. Critical SIF Report with Permit & JSA IDs in raw_data
    rep_crit = SafetyReport(
        id="rep-sla-crit-01",
        dataset_id=dataset_id,
        original_id="SLA-001",
        raw_data={
            "desc": "High pressure hydrogen line flange seal failed near reactor; toxic flammable vapor; hot work underway",
            "permit_id": "PTW-2026-8891",
            "jsa_id": "JSA-HYD-042"
        },
        refinery_unit="HGU-1",
        equipment="Flange-FL-402",
        department="Operations",
        work_type="Hot Work",
        description="High pressure hydrogen line flange seal failed near reactor; toxic flammable vapor; hot work underway",
        hazard="Pressurized flammable hydrogen cloud",
        potential_consequence="Explosion and facility damage",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=True,
        previous_similar_reports=3,
        risk_level="Critical",
        action_status="Open",
        report_date=datetime(2026, 2, 8, 10, 0, 0)
    )

    # 2. High SIF Report
    rep_high = SafetyReport(
        id="rep-sla-high-02",
        dataset_id=dataset_id,
        original_id="SLA-002",
        raw_data={"desc": "Crude transfer pump mechanical seal leaking; maintenance delayed"},
        refinery_unit="CDU-1",
        equipment="Pump-P-201",
        department="Maintenance",
        work_type="Routine Maintenance",
        description="Crude transfer pump mechanical seal leaking; maintenance delayed",
        hazard="Hydrocarbon leakage",
        potential_consequence="Flash Fire",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=1,
        risk_level="High",
        action_status="Open",
        report_date=datetime(2026, 2, 7, 11, 0, 0)
    )

    db_session.add_all([rep_crit, rep_high])
    db_session.commit()

    # Ensure dynamic SLA policies are seeded
    SLAService.get_or_create_policies(db_session)

    return {
        "dataset_id": dataset_id,
        "rep_crit": rep_crit,
        "rep_high": rep_high
    }


class TestPhase6SLAAndSafetyHolds:

    def test_01_new_critical_action_sla_policy(self, db_session: Session, phase6_test_data):
        """Test 1: Critical action generation dynamically inherits 60-minute SLA policy from database."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        assert action is not None
        assert action.severity == "CRITICAL"
        assert action.sla_minutes == 60  # Default 60-min demonstration policy
        assert action.sla_deadline is not None
        assert action.sla_state == "NORMAL"
        assert action.escalation_level == 0
        assert action.assigned_role == "Unit In-Charge"

    def test_02_countdown_calculation_and_formatting(self, db_session: Session, phase6_test_data):
        """Test 2: Verifies active SLA countdown calculation and remaining time formatting."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # Simulated at t = +20 minutes (40 minutes remaining)
        simulated_now = action.created_at + timedelta(minutes=20)
        cd = SLAService.get_action_countdown(db_session, action.id, now=simulated_now)

        assert cd["time_remaining_seconds"] == 40 * 60
        assert "00:40:00 remaining" in cd["formatted_countdown"]
        assert round(cd["percentage_elapsed"], 1) == 33.3
        assert cd["sla_state"] == "NORMAL"
        assert cd["is_breached"] is False

    def test_03_acknowledgement_before_sla(self, db_session: Session, phase6_test_data):
        """Test 3: Acknowledgement before SLA deadline transitions state to ACKNOWLEDGED and halts breach timer."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        ack_time = action.created_at + timedelta(minutes=15)
        req = SLAAcknowledgeRequest(
            actor_name="Unit Supervisor Verma",
            actor_role="Unit In-Charge",
            comments="Acknowledged and dispatched team to secure perimeter."
        )
        updated_act = SLAService.acknowledge_action(db_session, action.id, req, now=ack_time)

        assert updated_act.acknowledged_at == ack_time
        assert updated_act.sla_state == "ACKNOWLEDGED"

        # Check countdown state at t = +70 minutes (past original deadline)
        future_time = action.created_at + timedelta(minutes=70)
        cd = SLAService.get_action_countdown(db_session, action.id, now=future_time)
        assert cd["sla_state"] == "ACKNOWLEDGED"
        assert cd["is_acknowledged"] is True

    def test_04_sla_breach_detection(self, db_session: Session, phase6_test_data):
        """Test 4: Unacknowledged action exceeding 60 minutes is detected as BREACHED."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # Simulated at t = +65 minutes (5 minutes past deadline)
        breached_time = action.created_at + timedelta(minutes=65)
        cd = SLAService.get_action_countdown(db_session, action.id, now=breached_time)

        assert cd["is_breached"] is True
        assert cd["time_remaining_seconds"] == -300
        assert "BREACHED by 00:05:00" in cd["formatted_countdown"]
        assert cd["sla_state"] == "BREACHED"

    def test_05_reminder_and_warning_intervals(self, db_session: Session, phase6_test_data):
        """Test 5: Countdown state transitions to APPROACHING_DEADLINE at >= 50% elapsed time (>= 30 mins)."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # At t = +35 minutes (more than 50% elapsed)
        warning_time = action.created_at + timedelta(minutes=35)
        cd = SLAService.get_action_countdown(db_session, action.id, now=warning_time)

        assert cd["percentage_elapsed"] >= 50.0
        assert cd["sla_state"] == "APPROACHING_DEADLINE"

    def test_06_escalation_level_1_hse_head(self, db_session: Session, phase6_test_data):
        """Test 6: SLA breach automatically triggers Level 1 escalation to HSE Head."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        breached_time = action.created_at + timedelta(minutes=65)
        res = SLAService.evaluate_and_escalate_actions(db_session, now=breached_time)

        assert res["escalated_count"] >= 1

        db_session.refresh(action)
        assert action.escalation_level == 1
        assert action.assigned_role == "HSE Head"
        assert action.status == "ESCALATED"
        assert action.sla_state == "ESCALATED"

        # Verify EscalationLog and EmailLog created
        esc_log = db_session.scalar(
            select(EscalationLog).where(EscalationLog.action_id == action.id)
        )
        assert esc_log is not None
        assert esc_log.escalation_level == 1
        assert esc_log.recipient_role == "HSE Head"

        email = db_session.scalar(
            select(EmailLog).where(EmailLog.report_id == rep.id)
        )
        assert email is not None
        assert "ESCALATION LEVEL 1" in email.subject

    def test_07_multiple_escalation_levels(self, db_session: Session, phase6_test_data):
        """Test 7: Multi-tier escalation progresses Level 1 -> Level 2 (Plant Management) -> Level 3 (Executive Management)."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # Step 1: Breach -> Level 1 (t = +65m)
        t1 = action.created_at + timedelta(minutes=65)
        SLAService.evaluate_and_escalate_actions(db_session, now=t1)
        db_session.refresh(action)
        assert action.escalation_level == 1
        assert action.assigned_role == "HSE Head"

        # Step 2: Unresolved for additional 30m -> Level 2 (t = +95m)
        t2 = action.created_at + timedelta(minutes=95)
        SLAService.evaluate_and_escalate_actions(db_session, now=t2)
        db_session.refresh(action)
        assert action.escalation_level == 2
        assert action.assigned_role == "Plant Management"

        # Step 3: Unresolved for another 30m -> Level 3 (t = +125m)
        t3 = action.created_at + timedelta(minutes=125)
        SLAService.evaluate_and_escalate_actions(db_session, now=t3)
        db_session.refresh(action)
        assert action.escalation_level == 3
        assert action.assigned_role == "Executive Management"

        # Verify 3 distinct escalation logs
        logs = list(db_session.scalars(
            select(EscalationLog).where(EscalationLog.action_id == action.id).order_by(EscalationLog.escalation_level)
        ).all())
        assert len(logs) == 3
        assert [l.escalation_level for l in logs] == [1, 2, 3]

    def test_08_duplicate_prevention_and_idempotency(self, db_session: Session, phase6_test_data):
        """Test 8: Running escalation evaluations repeatedly at the same timestamp does NOT generate duplicate notifications."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        t_breach = action.created_at + timedelta(minutes=65)

        # First run triggers Level 1
        res1 = SLAService.evaluate_and_escalate_actions(db_session, now=t_breach)
        assert res1["escalated_count"] == 1

        # Second and third run at same time window must be idempotent
        res2 = SLAService.evaluate_and_escalate_actions(db_session, now=t_breach)
        res3 = SLAService.evaluate_and_escalate_actions(db_session, now=t_breach + timedelta(seconds=10))

        assert res2["escalated_count"] == 0
        assert res3["escalated_count"] == 0

        logs_cnt = db_session.scalar(
            select(EscalationLog).where(EscalationLog.action_id == action.id)
        )
        assert logs_cnt is not None

    def test_09_action_closure_lifecycle(self, db_session: Session, phase6_test_data):
        """Test 9: Transitioning action to CLOSED records closed_at timestamp and updates sla_state."""
        rep = phase6_test_data["rep_high"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # Transition PENDING_APPROVAL -> DISPATCHED -> IN_PROGRESS -> CLOSED
        action.status = "DISPATCHED"
        db_session.commit()

        req_close = SafetyActionTransitionRequest(
            new_status="CLOSED",
            actor_name="Duty Officer Rajesh",
            actor_role="Safety Officer",
            comments="Work successfully contained and validated."
        )
        closed_act = OrchestrationService.transition_action_status(db_session, action.id, req_close)

        assert closed_act.status == "CLOSED"
        assert closed_act.closed_at is not None
        assert closed_act.sla_state == "CLOSED"

    def test_10_action_verification_signoff(self, db_session: Session, phase6_test_data):
        """Test 10: Transitioning action to VERIFIED records verified_by and remediation_completed_at."""
        rep = phase6_test_data["rep_high"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        action.status = "CONTAINED"
        db_session.commit()

        req_verif = SafetyActionTransitionRequest(
            new_status="VERIFIED",
            actor_name="HSE Auditor Dr. Das",
            actor_role="HSE Auditor",
            comments="Field barrier inspection confirmed positive isolation."
        )
        verif_act = OrchestrationService.transition_action_status(db_session, action.id, req_verif)

        assert verif_act.status == "VERIFIED"
        assert verif_act.verified_by == "HSE Auditor Dr. Das"
        assert verif_act.verified_at is not None
        assert verif_act.remediation_completed_at is not None

    def test_11_safety_hold_request_and_review(self, db_session: Session, phase6_test_data):
        """Test 11: Digital Safety Hold request uses permit/JSA references from dataset and review freezes digital workflow."""
        rep = phase6_test_data["rep_crit"]

        req_hold = SafetyHoldCreateRequest(
            report_id=rep.id,
            reason="Uncontrolled hydrogen flange leak in vicinity of active hot work",
            trigger="CRITICAL SIF Precursor",
            bdi=95.0,
            sif_status="YES",
            requested_by="Unit In-Charge Banerjee"
        )
        hold = SafetyHoldService.request_safety_hold(db_session, req_hold)

        assert hold is not None
        assert hold.status == "SAFETY_HOLD_REQUESTED"
        # Verify Permit ID & JSA ID extracted from source report raw_data
        assert hold.permit_id == "PTW-2026-8891"
        assert hold.jsa_id == "JSA-HYD-042"
        assert hold.refinery_unit == "HGU-1"

        # Review & Approve Safety Hold -> WORKFLOW_BLOCKED
        req_rev = SafetyHoldReviewRequest(
            decision="APPROVE",
            reviewer_name="Senior Safety Officer Gupta",
            reviewer_role="Safety Officer",
            comments="Confirmed severe barrier void. Digital permit freeze authorized."
        )
        approved_hold = SafetyHoldService.review_safety_hold(db_session, hold.id, req_rev)

        assert approved_hold.status == "WORKFLOW_BLOCKED"
        assert approved_hold.approved_by == "Senior Safety Officer Gupta"
        assert approved_hold.approved_at is not None

    def test_12_safety_hold_reassessment_and_release(self, db_session: Session, phase6_test_data):
        """Test 12: Complete safety hold release cycle: WORKFLOW_BLOCKED -> REASSESSMENT -> RELEASE_REQUESTED -> RELEASED."""
        rep = phase6_test_data["rep_crit"]
        req_hold = SafetyHoldCreateRequest(
            report_id=rep.id,
            reason="Flange leak near hot work",
            trigger="CRITICAL SIF Precursor",
            requested_by="Unit In-Charge"
        )
        hold = SafetyHoldService.request_safety_hold(db_session, req_hold)

        # 1. Approve
        SafetyHoldService.review_safety_hold(
            db_session, hold.id, SafetyHoldReviewRequest(decision="APPROVE", reviewer_name="Safety Lead")
        )

        # 2. Reassess
        SafetyHoldService.reassess_safety_hold(
            db_session, hold.id, SafetyHoldReassessRequest(actor_name="HSE Inspector", reassessment_notes="Flange gasket replaced and torque checked.")
        )
        db_session.refresh(hold)
        assert hold.status == "REASSESSMENT"

        # 3. Request Release
        SafetyHoldService.request_release(
            db_session, hold.id, SafetyHoldReleaseRequest(requester_name="Unit Supervisor", justification="Pressure test passed at 1.5x design.")
        )
        db_session.refresh(hold)
        assert hold.status == "RELEASE_REQUESTED"

        # 4. Verify and Release
        SafetyHoldService.verify_and_release(
            db_session, hold.id, SafetyHoldVerifyReleaseRequest(verifier_name="HSE Head Roy", walkdown_notes="Physical walkdown completed.", permit_reauthorized=True)
        )
        db_session.refresh(hold)
        assert hold.status == "RELEASED"
        assert hold.released_at is not None
        assert hold.verified_by == "HSE Head Roy"

    def test_13_server_restart_recovery(self, db_session: Session, phase6_test_data):
        """Test 13: SLA deadlines and escalation levels persist across restarts and seamlessly resume countdown."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)
        saved_id = action.id
        saved_deadline = action.sla_deadline

        # Simulate fresh session (as during server restart)
        db_session.expire_all()

        reloaded_act = db_session.scalar(select(SafetyAction).where(SafetyAction.id == saved_id))
        assert reloaded_act is not None
        assert reloaded_act.sla_deadline == saved_deadline
        assert reloaded_act.sla_minutes == 60

        # Countdown calculation continues accurately from persisted timestamps
        simulated_now = reloaded_act.created_at + timedelta(minutes=45)
        cd = SLAService.get_action_countdown(db_session, reloaded_act.id, now=simulated_now)
        assert cd["time_remaining_seconds"] == 15 * 60
        assert "00:15:00 remaining" in cd["formatted_countdown"]

    def test_14_background_worker_cycle_and_api_routes(self, client: TestClient, db_session: Session, phase6_test_data):
        """Test 14: Validates background worker tick execution and all Phase 6 REST API routes."""
        rep = phase6_test_data["rep_crit"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # 1. GET /api/sla/policies
        res_pol = client.get("/api/sla/policies")
        assert res_pol.status_code == 200
        pols = res_pol.json()
        assert len(pols) >= 5
        crit_pol = next(p for p in pols if p["severity"] == "CRITICAL")
        assert crit_pol["sla_minutes"] == 60

        # 2. PUT /api/sla/policies/CRITICAL
        res_upd = client.put(
            "/api/sla/policies/CRITICAL",
            json={"sla_minutes": 55, "reminder_minutes": 10}
        )
        assert res_upd.status_code == 200
        assert res_upd.json()["sla_minutes"] == 55

        # 3. GET /api/sla/countdown/{action_id}
        res_cd = client.get(f"/api/sla/countdown/{action.id}")
        assert res_cd.status_code == 200
        data_cd = res_cd.json()
        assert data_cd["action_id"] == action.id
        assert "remaining" in data_cd["formatted_countdown"]

        # 4. POST /api/sla/acknowledge/{action_id}
        res_ack = client.post(
            f"/api/sla/acknowledge/{action.id}",
            json={"actor_name": "Field Officer Dave", "comments": "Team dispatched."}
        )
        assert res_ack.status_code == 200
        assert res_ack.json()["acknowledged_at"] is not None

        # 5. GET /api/sla/dashboard
        res_dash = client.get("/api/sla/dashboard")
        assert res_dash.status_code == 200
        dash_data = res_dash.json()
        assert "critical_open" in dash_data
        assert "active_actions" in dash_data

        # 6. POST /api/sla/evaluate-now
        res_eval = client.post("/api/sla/evaluate-now")
        assert res_eval.status_code == 200
        assert "evaluated_count" in res_eval.json()

        # 7. POST /api/safety-holds/request
        res_hold = client.post(
            "/api/safety-holds/request",
            json={
                "report_id": rep.id,
                "action_id": action.id,
                "reason": "Test hold request via API",
                "trigger": "CRITICAL SIF Precursor",
                "requested_by": "Test Operator"
            }
        )
        assert res_hold.status_code == 201
        hold_id = res_hold.json()["id"]

        # 8. GET /api/safety-holds
        res_holds_list = client.get("/api/safety-holds")
        assert res_holds_list.status_code == 200
        assert res_holds_list.json()["total"] >= 1

        # 9. GET /api/safety-holds/{hold_id}
        res_hold_get = client.get(f"/api/safety-holds/{hold_id}")
        assert res_hold_get.status_code == 200
        assert res_hold_get.json()["id"] == hold_id

        # 10. POST /api/safety-holds/{hold_id}/review -> WORKFLOW_BLOCKED
        res_rev = client.post(
            f"/api/safety-holds/{hold_id}/review",
            json={"decision": "APPROVE", "reviewer_name": "Reviewer Dave"}
        )
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "WORKFLOW_BLOCKED"

        # 11. POST /api/safety-holds/{hold_id}/reassess
        res_reassess = client.post(
            f"/api/safety-holds/{hold_id}/reassess",
            json={"actor_name": "Inspector Kim", "reassessment_notes": "Repair completed."}
        )
        assert res_reassess.status_code == 200
        assert res_reassess.json()["status"] == "REASSESSMENT"

        # 12. POST /api/safety-holds/{hold_id}/request-release
        res_req_rel = client.post(
            f"/api/safety-holds/{hold_id}/request-release",
            json={"requester_name": "Supervisor Dave", "justification": "Checked."}
        )
        assert res_req_rel.status_code == 200
        assert res_req_rel.json()["status"] == "RELEASE_REQUESTED"

        # 13. POST /api/safety-holds/{hold_id}/verify-release -> RELEASED
        res_ver_rel = client.post(
            f"/api/safety-holds/{hold_id}/verify-release",
            json={"verifier_name": "Auditor Singh", "walkdown_notes": "Passed walkdown.", "permit_reauthorized": True}
        )
        assert res_ver_rel.status_code == 200
        assert res_ver_rel.json()["status"] == "RELEASED"
