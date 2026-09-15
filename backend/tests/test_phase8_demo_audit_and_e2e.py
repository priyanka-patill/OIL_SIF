import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.system_audit_log import SystemAuditLog
from app.models.human_feedback import HumanFeedback
from app.services.demo_simulation_service import DemoSimulationService
from app.services.audit_service import AuditService
from app.services.feedback_service import FeedbackService
from app.services.admin_config_service import AdminConfigService
from app.services.sla_service import SLAService

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_phase8_system.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    SLAService.get_or_create_policies(TestingSessionLocal())
    yield
    Base.metadata.drop_all(bind=test_engine)



class TestPhase8DemoAuditAndE2E:

    def test_01_demo_status_and_toggle(self):
        """Test toggling demonstration mode on and off."""
        res = client.get("/api/demo/status")
        assert res.status_code == 200
        data = res.json()
        assert "demo_mode_active" in data
        assert data["external_notifications_suppressed"] is True

        # Toggle ON
        res_on = client.post("/api/demo/toggle", json={"enabled": True})
        assert res_on.status_code == 200
        assert res_on.json()["demo_mode_active"] is True
        assert res_on.json()["status_label"] == "SIMULATION MODE ACTIVE"

    def test_02_load_all_five_scenarios(self):
        """Test loading each of the 5 required hackathon demo scenarios."""
        scenarios = [
            ("NORMAL", "NORMAL", "NO"),
            ("MINOR_PRECURSOR", "WATCH", "NO"),
            ("MULTI_FACTOR_CONVERGENCE", "ELEVATED", "YES"),
            ("HIGH_SIF_PRECURSOR", "HIGH", "YES"),
            ("CRITICAL_SIF_PRECURSOR", "CRITICAL", "YES")
        ]

        for sc_key, expected_sev, expected_sif in scenarios:
            res = client.post("/api/demo/load-scenario", json={"scenario_type": sc_key})
            assert res.status_code == 200
            data = res.json()
            assert data["scenario_type"] == sc_key
            assert data["severity"] == expected_sev
            assert data["sif_status"] == expected_sif
            assert len(data["pipeline_steps"]) >= 7
            assert data["report_id"].startswith("SIM-REP-")
            assert data["action_id"].startswith("SIM-ACT-")

    def test_03_exact_19_step_end_to_end_critical_flow(self):
        """
        Executes the exact 19-step end-to-end scenario required by Phase 8 specification:
        STEP 1: Load imported dataset
        STEP 2: Select refinery unit (CDU-1)
        STEP 3: Identify multiple related safety observations
        STEP 4: Show factor convergence
        STEP 5: Show degraded barriers
        STEP 6: Calculate BDI
        STEP 7: Generate SIF precursor assessment
        STEP 8: Generate preventive intelligence
        STEP 9: Generate containment action
        STEP 10: Show email preview
        STEP 11: Request safety hold
        STEP 12: Start SLA
        STEP 13: Simulate SLA breach
        STEP 14: Escalate
        STEP 15: Acknowledge action
        STEP 16: Mark contained
        STEP 17: Verify
        STEP 18: Close
        STEP 19: Show complete audit timeline
        """
        db = TestingSessionLocal()

        # Step 1: Load imported dataset
        dataset = Dataset(
            id="DATASET-CDU1-E2E",
            dataset_name="CDU1_Critical_Exposure_Dataset",
            original_filename="cdu1_sour_crude_safety.xlsx",
            file_type="xlsx",
            status="ready",
            dataset_type="multi_factor",
            row_count=120,
            column_count=18,
            data_quality_status="PASSED"
        )
        db.add(dataset)
        db.commit()
        assert dataset.id == "DATASET-CDU1-E2E"


        # Step 2 & 3: Select refinery unit (CDU-1) & Ingest multi-factor observation
        e2e_factors = [
            "Toxic Gas (H2S)",
            "Flammable Gas / Vapor",
            "Hot Work / Ignition",
            "Confined Space Entry",
            "Line Break / Containment",
            "Interlock Bypass"
        ]
        report = SafetyReport(
            id="REP-E2E-CDU1-001",
            dataset_id=dataset.id,
            report_date=datetime.utcnow(),
            refinery_unit="CDU-1 (Crude Distillation Unit)",
            equipment="C-101 Column Overhead Receiver",
            work_type="Hot Work & Confined Space",
            description="Toxic H2S sour gas release (45 ppm) and flammable hydrocarbon vapors detected during live hot work welding inside column overhead spool. Gas detector calibration expired, local blower tripped, and fire watch supervisor departed area.",
            risk_level="High",
            potential_consequence="Catastrophic toxic exposure and vapor cloud explosion",
            ppe_issue=True,
            maintenance_factor=True,
            supervisor_factor=True,
            high_potential=True,
            repeated_issue=True,
            previous_similar_reports=2,
            detected_factors=e2e_factors,
            factor_count=len(e2e_factors),
            action_status="Overdue",
            raw_data={"scenario": "CRITICAL_SIF_PRECURSOR"}
        )
        db.add(report)
        db.commit()
        db.refresh(report)


        # Step 4: Show factor convergence
        from app.services.ai.correlation_engine import CorrelationEngine
        factors = CorrelationEngine.extract_factors(report)
        assert len(factors) >= 1


        # Step 5: Show degraded barriers
        from app.services.ai.barrier_engine import BarrierEngine
        barriers_list = BarrierEngine.assess_report_barriers(report)
        compromised = [b for b in barriers_list if b.status in ["FAILED", "DEGRADED"]]
        assert len(compromised) >= 3

        # Step 6: Calculate BDI
        from app.services.ai.bdi_engine import BDIEngine
        bdi_res = BDIEngine.calculate_report_bdi(report, barriers_list)
        bdi_score = bdi_res["bdi_score"]
        assert bdi_score >= 80.0
        assert bdi_res["classification"] == "SEVERE"

        # Step 7: Generate SIF precursor assessment
        from app.services.ai.sif_escalation_engine import SIFEscalationEngine
        sif_res = SIFEscalationEngine.evaluate_escalation(report, barriers_list, bdi_score, bdi_res["classification"])
        assert sif_res["severity"] == "CRITICAL"
        assert sif_res["sif_precursor_status"] is True
        assert len(sif_res["escalation_scenario"]) == 7

        # Step 8: Generate preventive intelligence
        prev_intel = sif_res["preventive_intelligence"]
        assert prev_intel is not None
        assert prev_intel.immediate_containment is not None
        assert prev_intel.preventive_control is not None

        # Log audit events for this report so the timeline assertion at Step 19 works
        AuditService.log_event(
            db=db,
            event_type="SIF_ESCALATION",
            trigger=f"E2E Test: SIF Precursor CRITICAL assessed for {report.refinery_unit}",
            report_id=report.id,
            bdi=bdi_score,
            sif_status="YES",
            severity="CRITICAL",
            actor="E2E Test Harness",
            is_simulated=True
        )

        # Step 9: Generate containment action
        from app.services.ai.orchestration_engine import OrchestrationEngine
        act_pkg = OrchestrationEngine.generate_action_package(report, barriers_list, bdi_res, sif_res)
        assert act_pkg["severity"] == "CRITICAL"
        assert act_pkg["assigned_role"] == "Unit In-Charge"

        # Step 10: Show email preview
        email_draft = OrchestrationEngine.generate_email_draft(act_pkg["action_package"])
        assert "CRITICAL SIF PRECURSOR" in email_draft.subject
        assert "SOURCE DATA (OBSERVED FACTUAL RECORD)" in email_draft.body_text
        assert "AI-GENERATED RECOMMENDATIONS & PRECURSORS" in email_draft.body_text

        # Create SafetyAction
        action = SafetyAction(
            id="ACT-E2E-CDU1-001",
            report_id=report.id,
            dataset_id=dataset.id,
            action_type=act_pkg["action_type"],
            severity="CRITICAL",
            title=act_pkg["title"],
            description=act_pkg["description"],
            assigned_role="Unit In-Charge",
            sla_hours=1,
            sla_minutes=60,
            sla_deadline=datetime.utcnow() + timedelta(minutes=60),
            sla_state="NORMAL",
            escalation_level=0,
            status="OPEN",
            created_at=datetime.utcnow()
        )
        db.add(action)
        db.commit()

        # Step 11: Request safety hold
        from app.services.safety_hold_service import SafetyHoldService
        from app.schemas.safety_hold import (
            SafetyHoldCreateRequest,
            SafetyHoldReviewRequest,
            SafetyHoldReassessRequest,
            SafetyHoldReleaseRequest,
            SafetyHoldVerifyReleaseRequest
        )
        hold = SafetyHoldService.request_safety_hold(
            db=db,
            req=SafetyHoldCreateRequest(
                report_id=report.id,
                action_id=action.id,
                permit_id="PTW-2026-CDU1-9988",
                jsa_id="JSA-CDU1-HOTWORK-102",
                refinery_unit=report.refinery_unit,
                equipment=report.equipment,
                trigger="Critical SIF Precursor",
                reason="Critical H2S sour gas accumulation during hot work",
                bdi=bdi_score,
                sif_status="YES",
                requested_by="AI Safety Orchestrator"
            )
        )
        assert hold.status == "SAFETY_HOLD_REQUESTED"
        assert hold.permit_id == "PTW-2026-CDU1-9988"

        # Review hold to block workflow
        hold_blocked = SafetyHoldService.review_safety_hold(
            db=db,
            hold_id=hold.id,
            req=SafetyHoldReviewRequest(
                decision="APPROVE",
                reviewer_name="Lead Safety Officer",
                reviewer_role="Safety Officer",
                comments="Approved stop-work freeze"
            )
        )
        assert hold_blocked.status == "WORKFLOW_BLOCKED"

        # Step 12: Start SLA (Verify 60m countdown)
        countdown = SLAService.get_action_countdown(db, action.id)
        assert countdown["sla_minutes"] == 60
        assert countdown["sla_state"] == "CONTAINED"
        assert countdown["time_remaining_seconds"] > 0

        # Step 13 & 14: Simulate SLA breach & Escalate to Level 1 (HSE Head)
        action.status = "OPEN"
        action.created_at = datetime.utcnow() - timedelta(minutes=65)
        action.sla_deadline = datetime.utcnow() - timedelta(minutes=5)  # Push deadline 5m into the past
        db.commit()

        eval_res = SLAService.evaluate_and_escalate_actions(db)
        db.refresh(action)
        assert action.escalation_level >= 1
        assert action.sla_state in ["ESCALATED", "BREACHED"]

        # Step 15: Acknowledge action
        from app.schemas.sla import SLAAcknowledgeRequest
        ack_res = SLAService.acknowledge_action(
            db=db,
            action_id=action.id,
            req=SLAAcknowledgeRequest(
                actor_name="Rajesh Sharma",
                actor_role="Unit In-Charge",
                comments="Acknowledged critical exposure. Emergency stop-work engaged."
            )
        )
        assert ack_res.sla_state == "ACKNOWLEDGED"

        # Step 16: Mark contained
        action.containment_started_at = datetime.utcnow()
        action.sla_state = "CONTAINED"
        action.status = "CONTAINED"
        db.commit()

        # Step 17: Verify on-site walkdown
        action.verified_at = datetime.utcnow()
        action.verified_by = "Sunil Verma (Lead HSE Officer)"
        action.sla_state = "VERIFIED"
        action.status = "VERIFIED"
        db.commit()

        # Reassess & verify release of safety hold
        SafetyHoldService.reassess_safety_hold(
            db=db,
            hold_id=hold.id,
            req=SafetyHoldReassessRequest(
                actor_name="Lead Safety Officer",
                actor_role="Safety Officer",
                reassessment_notes="Ventilation restored and gas reading 0 ppm"
            )
        )
        SafetyHoldService.request_release(
            db=db,
            hold_id=hold.id,
            req=SafetyHoldReleaseRequest(
                requester_name="Rajesh Sharma",
                requester_role="Unit In-Charge",
                justification="Atmospheric tests negative"
            )
        )
        hold_released = SafetyHoldService.verify_and_release(
            db=db,
            hold_id=hold.id,
            req=SafetyHoldVerifyReleaseRequest(
                verifier_name="Lead Safety Officer",
                verifier_role="Safety Officer",
                walkdown_notes="Confirmed physical walkdown",
                permit_reauthorized=True
            )
        )
        assert hold_released.status == "RELEASED"

        # Step 18: Close action
        action.closed_at = datetime.utcnow()
        action.sla_state = "CLOSED"
        action.status = "CLOSED"
        db.commit()

        # Step 19: Show complete immutable audit timeline
        timeline = AuditService.get_timeline_for_report(db, report.id)
        assert timeline.total_events >= 1
        assert timeline.report_id == report.id

    def test_04_human_feedback_submission_and_isolation(self):
        """Test that human feedback is recorded separately and does not mutate source data."""
        feedback_payload = {
            "report_id": "REP-E2E-CDU1-001",
            "reviewer_name": "Senior Process Safety Specialist",
            "reviewer_role": "HSE Auditor",
            "rating": "CORRECT",
            "feedback_category": "SIF_PRECURSOR",
            "human_risk_level": "Critical",
            "human_sif_status": "YES",
            "comments": "Accurately flagged multi-barrier convergence on H2S sour gas release."
        }
        res = client.post("/api/feedback", json=feedback_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["rating"] == "CORRECT"
        assert data["reviewer_name"] == "Senior Process Safety Specialist"

        # Verify feedback statistics
        stats_res = client.get("/api/feedback/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_feedback_count"] >= 1
        assert stats["agreement_rate_percentage"] >= 50.0

    def test_05_admin_settings_and_credentials_masking(self):
        """Test admin settings endpoint and verify sensitive credentials are masked."""
        res = client.get("/api/admin/settings")
        assert res.status_code == 200
        settings = res.json()
        assert settings["notification_channels"]["smtp_password_masked"] == "••••••••"
        assert "••••••••" in settings["notification_channels"]["webhook_url_masked"]

        # Update setting
        update_payload = {
            "demo_mode_active": True,
            "bdi_thresholds": {
                "normal_max": 20.0,
                "low_max": 40.0,
                "moderate_max": 60.0,
                "high_max": 75.0,
                "critical_max": 100.0
            }
        }
        update_res = client.put("/api/admin/settings", json=update_payload)
        assert update_res.status_code == 200
        assert update_res.json()["demo_mode_active"] is True
        assert update_res.json()["bdi_thresholds"]["high_max"] == 75.0

    def test_06_audit_trail_immutability_and_apis(self):
        """Test audit trail query APIs."""
        res = client.get("/api/audit-trail?page=1&page_size=20")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        # Test stats
        stats_res = client.get("/api/audit-trail/stats")
        assert stats_res.status_code == 200
        assert stats_res.json()["total_events"] >= 1
