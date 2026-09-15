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
from app.models.webhook_log import WebhookLog
from app.models.email_log import EmailLog
from app.models.action_history import ActionHistory
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.ai.sif_escalation_engine import SIFEscalationEngine
from app.services.ai.orchestration_engine import OrchestrationEngine
from app.services.orchestration_service import OrchestrationService
from app.schemas.orchestrator import (
    SafetyActionApprovalRequest,
    SafetyActionTransitionRequest
)


@pytest.fixture(scope="function")
def orchestrator_test_data(db_session: Session):
    """
    Creates controlled test reports for Agentic Safety Action Orchestrator testing.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="Orchestrator Test Dataset",
        original_filename="orchestrator_test.xlsx",
        sheet_name="Orchestrator_Test",
        file_type="xlsx",
        dataset_type="multi_factor",
        factor_count=4,
        factor_names=["PPE_NonCompliance", "Supervisor_Negligence", "Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored"],
        row_count=10,
        column_count=15,
        status="ready",
        is_active=True
    )
    db_session.add(dataset)
    db_session.flush()

    # 1. Critical SIF Report (Blowout, bypass permit, repeat failure -> CRITICAL -> 2h SLA, SAFETY_HOLD_REQUEST, Unit In-Charge)
    rep_critical = SafetyReport(
        id="rep-orch-crit-01",
        dataset_id=dataset_id,
        original_id="ORCH-001",
        raw_data={"desc": "Booster pump seal catastrophic blowout; worker without PPE; supervisor absent; hot work permit bypassed; repeat failure ignored; action overdue"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Operations",
        work_type="Hot Work",
        description="Booster pump seal catastrophic blowout; worker without PPE; supervisor absent; hot work permit bypassed; repeat failure ignored; action overdue",
        hazard="Uncontrolled pressurized hot hydrocarbon release",
        potential_consequence="Explosion and multiple casualties",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=True,
        previous_similar_reports=4,
        risk_level="Critical",
        action_status="Overdue",
        report_date=datetime(2026, 2, 8, 16, 0, 0)
    )

    # 2. High SIF Report (Hydrocarbon weeping + maintenance delay -> HIGH -> 4h SLA, Department Head)
    rep_high = SafetyReport(
        id="rep-orch-high-02",
        dataset_id=dataset_id,
        original_id="ORCH-002",
        raw_data={"desc": "Heavy hydrocarbon pump seal weeping near hot furnace; maintenance delayed; corrective action in progress"},
        refinery_unit="CDU-1",
        equipment="Pump-P-102",
        department="Maintenance",
        work_type="Hot Work Area",
        description="Heavy hydrocarbon pump seal weeping near hot furnace; maintenance delayed; corrective action in progress",
        hazard="Hydrocarbon leakage near ignition source",
        potential_consequence="Flash fire",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=1,
        risk_level="High",
        action_status="Open",
        report_date=datetime(2026, 2, 6, 14, 0, 0)
    )

    # 3. Elevated Report (Line draining without PPE/supervision -> ELEVATED -> 24h SLA)
    rep_elevated = SafetyReport(
        id="rep-orch-elev-03",
        dataset_id=dataset_id,
        original_id="ORCH-003",
        raw_data={"desc": "Technician working without goggles while supervisor deferred pump maintenance check"},
        refinery_unit="CDU-1",
        equipment="Drain-DR-10",
        department="Maintenance",
        work_type="Line Draining",
        description="Technician working without goggles while supervisor deferred pump maintenance check",
        hazard="Pressurized wash water",
        potential_consequence="Minor facial impact",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Medium",
        action_status="Closed",
        report_date=datetime(2026, 2, 4, 11, 0, 0)
    )

    # 4. Normal Report (Routine inspection, compliant)
    rep_normal = SafetyReport(
        id="rep-orch-norm-04",
        dataset_id=dataset_id,
        original_id="ORCH-004",
        raw_data={"desc": "Routine area inspection; all PPE worn; valid permits on file"},
        refinery_unit="CDU-1",
        equipment="Furnace-F-101",
        department="Operations",
        work_type="Routine Inspection",
        description="Routine area inspection; all PPE worn; valid permits on file",
        hazard="Ambient steam line surface",
        potential_consequence="Minor burn",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 2, 1, 9, 0, 0)
    )

    db_session.add_all([rep_critical, rep_high, rep_elevated, rep_normal])
    db_session.commit()

    return {
        "dataset_id": dataset_id,
        "rep_critical": rep_critical,
        "rep_high": rep_high,
        "rep_elevated": rep_elevated,
        "rep_normal": rep_normal
    }


class TestOrchestratorEngine:

    def test_01_critical_action_generation_and_package(self, db_session: Session, orchestrator_test_data):
        """Test 1: Critical SIF triggers comprehensive 19-field action package."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        assert action is not None
        assert action.severity == "CRITICAL"
        assert action.action_type == "SAFETY_HOLD_REQUEST"
        assert action.status == "PENDING_APPROVAL"
        assert action.approval_status == "PENDING"
        assert action.sla_hours == 2
        assert action.assigned_role == "Unit In-Charge"

        pkg = action.action_package
        assert pkg["report_id"] == rep.id
        assert pkg["refinery_unit"] == "CDU-1"
        assert pkg["equipment"] == "Pump-P-101"
        assert pkg["sif_status"] == "YES"
        assert "immediate_containment_recommendation" in pkg
        assert "verification_requirement" in pkg
        assert "responsible_role" in pkg

    def test_02_role_based_assignment_and_sla(self, db_session: Session, orchestrator_test_data):
        """Test 2: Verifies role matrix and SLA calculation across severities."""
        # Critical -> Unit In-Charge, 2 Hours
        rep_crit = orchestrator_test_data["rep_critical"]
        act_crit = OrchestrationService.generate_action_for_report(db_session, rep_crit.id)
        assert act_crit.assigned_role == "Unit In-Charge"
        assert act_crit.sla_hours == 2

        # High with Maintenance factor -> Department Head, 4 Hours
        rep_high = orchestrator_test_data["rep_high"]
        act_high = OrchestrationService.generate_action_for_report(db_session, rep_high.id)
        assert act_high.assigned_role == "Department Head"
        assert act_high.sla_hours == 4

        # Elevated -> 24 Hours
        rep_elev = orchestrator_test_data["rep_elevated"]
        act_elev = OrchestrationService.generate_action_for_report(db_session, rep_elev.id)
        assert act_elev.sla_hours == 24

        # Normal -> 72 Hours
        rep_norm = orchestrator_test_data["rep_normal"]
        act_norm = OrchestrationService.generate_action_for_report(db_session, rep_norm.id)
        assert act_norm.sla_hours == 72

    def test_03_email_draft_source_vs_ai_separation(self, db_session: Session, orchestrator_test_data):
        """Test 3: Context-aware email draft distinctly separates recorded facts from AI recommendations."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)
        draft = OrchestrationService.get_email_draft(db_session, action.id)

        assert draft is not None
        assert "CRITICAL SIF PRECURSOR" in draft.subject
        assert "SECTION 1: SOURCE DATA" in draft.body_text
        assert "SECTION 2: AI-GENERATED RECOMMENDATIONS" in draft.body_text
        assert "Report ID" in draft.source_data_summary
        assert "Immediate Containment Recommendation" in draft.ai_recommendations_summary

    def test_04_human_approval_workflow(self, db_session: Session, orchestrator_test_data):
        """Test 4: Human officer approves draft, transitioning status to DISPATCHED and generating email log."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        req = SafetyActionApprovalRequest(
            decision="APPROVE",
            reviewer_name="Senior Safety Officer Ramesh"
        )
        approved_act = OrchestrationService.approve_action(db_session, action.id, req)

        assert approved_act.status == "DISPATCHED"
        assert approved_act.approval_status == "APPROVED"
        assert approved_act.approved_by == "Senior Safety Officer Ramesh"
        assert approved_act.approved_at is not None

        # Verify email log generated
        email = db_session.scalar(select(EmailLog).where(EmailLog.report_id == rep.id))
        assert email is not None
        assert "CRITICAL" in email.subject
        assert email.status == "SENT"

    def test_05_human_rejection_workflow(self, db_session: Session, orchestrator_test_data):
        """Test 5: Rejection records feedback justification and marks REJECTED."""
        rep = orchestrator_test_data["rep_elevated"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        req = SafetyActionApprovalRequest(
            decision="REJECT",
            rejection_reason="Duplicate issue already covered under work order WO-9912",
            reviewer_name="Safety Lead Sunita"
        )
        rejected_act = OrchestrationService.reject_action(db_session, action.id, req)

        assert rejected_act.status == "REJECTED"
        assert rejected_act.approval_status == "REJECTED"
        assert "WO-9912" in rejected_act.rejection_reason

    def test_06_edit_and_approve_workflow(self, db_session: Session, orchestrator_test_data):
        """Test 6: Editing SLA/role before approving properly persists modifications."""
        rep = orchestrator_test_data["rep_high"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        req = SafetyActionApprovalRequest(
            decision="EDIT_AND_APPROVE",
            assigned_role="HSE Head",
            sla_hours=1,  # Expedite to 1 hour
            description="High-priority containment escalated directly to HSE Head",
            reviewer_name="Plant Operations Manager"
        )
        edited_act = OrchestrationService.approve_action(db_session, action.id, req)

        assert edited_act.status == "DISPATCHED"
        assert edited_act.assigned_role == "HSE Head"
        assert edited_act.sla_hours == 1
        assert "High-priority" in edited_act.description

    def test_07_action_state_machine_transitions(self, db_session: Session, orchestrator_test_data):
        """Test 7: Validates sequential lifecycle transitions."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        # 1. Approve -> DISPATCHED
        OrchestrationService.approve_action(
            db_session, action.id, SafetyActionApprovalRequest(decision="APPROVE")
        )

        # 2. DISPATCHED -> ACKNOWLEDGED
        act1 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="ACKNOWLEDGED")
        )
        assert act1.status == "ACKNOWLEDGED"
        assert act1.acknowledged_at is not None

        # 3. ACKNOWLEDGED -> IN_PROGRESS
        act2 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="IN_PROGRESS")
        )
        assert act2.status == "IN_PROGRESS"

        # 4. IN_PROGRESS -> CONTAINED
        act3 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="CONTAINED")
        )
        assert act3.status == "CONTAINED"
        assert act3.completed_at is not None

        # 5. CONTAINED -> AWAITING_VERIFICATION
        act4 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="AWAITING_VERIFICATION")
        )
        assert act4.status == "AWAITING_VERIFICATION"

        # 6. AWAITING_VERIFICATION -> VERIFIED
        act5 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="VERIFIED", actor_name="Auditor Verma")
        )
        assert act5.status == "VERIFIED"
        assert act5.verified_at is not None
        assert act5.verified_by == "Auditor Verma"

        # 7. VERIFIED -> CLOSED
        act6 = OrchestrationService.transition_action_status(
            db_session, action.id, SafetyActionTransitionRequest(new_status="CLOSED")
        )
        assert act6.status == "CLOSED"

    def test_08_duplicate_prevention(self, db_session: Session, orchestrator_test_data):
        """Test 8: Re-running action generation on same report does not spawn duplicate pending actions."""
        rep = orchestrator_test_data["rep_critical"]
        action_1 = OrchestrationService.generate_action_for_report(db_session, rep.id)
        action_2 = OrchestrationService.generate_action_for_report(db_session, rep.id)

        assert action_1.id == action_2.id

        total_actions_for_rep = db_session.query(SafetyAction).filter(SafetyAction.report_id == rep.id).count()
        assert total_actions_for_rep == 1

    def test_09_webhook_dispatch_and_logging(self, db_session: Session, orchestrator_test_data):
        """Test 9: Webhook payload synthesis, SHA-256 hashing, and delivery logging to webhook_logs."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        webhook = OrchestrationService.dispatch_webhook(
            db=db_session,
            action_id=action.id,
            endpoint="https://refinery-incident.oil.in/api/v1/alerts",
            event_type="SAFETY_HOLD_TRIGGERED"
        )

        assert webhook is not None
        assert webhook.delivery_status == "SUCCESS"
        assert webhook.response_code == 200
        assert len(webhook.payload_hash) == 64  # SHA-256 hash length
        assert webhook.event_type == "SAFETY_HOLD_TRIGGERED"

    def test_10_auto_orchestrate_high_critical(self, db_session: Session, orchestrator_test_data):
        """Test 10: Batch scanning automatically creates action packages for all High/Critical reports in dataset."""
        dataset_id = orchestrator_test_data["dataset_id"]
        res = OrchestrationService.auto_orchestrate_high_critical(db_session, dataset_id)

        assert res.scanned_reports_count == 4
        assert res.actions_created_count >= 2  # Critical & High reports
        assert len(res.action_ids) >= 2

    def test_11_safety_restrictions_guard(self, db_session: Session, orchestrator_test_data):
        """Test 11: Verifies that generated action packages are workflow/containment advisories and contain zero hardware direct control commands."""
        rep = orchestrator_test_data["rep_critical"]
        action = OrchestrationService.generate_action_for_report(db_session, rep.id)

        pkg_str = str(action.action_package).lower()
        # Verify strict absence of direct hardware actuation instructions
        forbidden_hardware_commands = [
            "open valve", "close valve", "set pressure to", "bypass interlock",
            "override trip", "set temperature to", "actuate motor"
        ]
        for cmd in forbidden_hardware_commands:
            assert cmd not in pkg_str

        # Verify advisory wording
        assert "safety_restrictions" in action.ai_recommendation
        assert "ADVISORY ONLY" in action.ai_recommendation["safety_restrictions"]

    def test_12_orchestrator_api_endpoints_integration(self, client: TestClient, db_session: Session, orchestrator_test_data):
        """Test 12: Full end-to-end integration testing of all FastAPI orchestrator routes."""
        rep_crit = orchestrator_test_data["rep_critical"]

        # 1. POST /api/orchestrator/generate/{report_id}
        res_gen = client.post(f"/api/orchestrator/generate/{rep_crit.id}")
        assert res_gen.status_code == 201
        data_act = res_gen.json()
        action_id = data_act["id"]
        assert data_act["severity"] == "CRITICAL"
        assert data_act["status"] == "PENDING_APPROVAL"

        # 2. GET /api/orchestrator/actions
        res_list = client.get("/api/orchestrator/actions?severity=CRITICAL")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["total"] >= 1

        # 3. GET /api/orchestrator/actions/{action_id}
        res_get = client.get(f"/api/orchestrator/actions/{action_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == action_id

        # 4. GET /api/orchestrator/actions/{action_id}/email-draft
        res_draft = client.get(f"/api/orchestrator/actions/{action_id}/email-draft")
        assert res_draft.status_code == 200
        data_draft = res_draft.json()
        assert "CRITICAL" in data_draft["subject"]
        assert "source_data_summary" in data_draft

        # 5. POST /api/orchestrator/actions/{action_id}/approve
        res_app = client.post(
            f"/api/orchestrator/actions/{action_id}/approve",
            json={"decision": "APPROVE", "reviewer_name": "Duty HSE Officer"}
        )
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "DISPATCHED"

        # 6. POST /api/orchestrator/actions/{action_id}/transition
        res_trans = client.post(
            f"/api/orchestrator/actions/{action_id}/transition",
            json={"new_status": "ACKNOWLEDGED", "actor_name": "Field Officer"}
        )
        assert res_trans.status_code == 200
        assert res_trans.json()["status"] == "ACKNOWLEDGED"

        # 7. POST /api/orchestrator/actions/{action_id}/webhook
        res_wh = client.post(
            f"/api/orchestrator/actions/{action_id}/webhook",
            json={"endpoint": "https://alerts.refinery.oil.in/hook"}
        )
        assert res_wh.status_code == 200
        assert res_wh.json()["delivery_status"] == "SUCCESS"

        # 8. GET /api/orchestrator/summary
        res_sum = client.get("/api/orchestrator/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert data_sum["total_actions"] >= 1

        # 9. POST /api/orchestrator/auto-orchestrate
        res_auto = client.post("/api/orchestrator/auto-orchestrate")
        assert res_auto.status_code == 200
        assert res_auto.json()["scanned_reports_count"] >= 4
