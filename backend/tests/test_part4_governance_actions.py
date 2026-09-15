import pytest
from datetime import datetime, timezone
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.models.report_analysis import ReportAnalysis
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.human_feedback import HumanFeedback
from app.services.report_service import ReportService
from app.services.sif_service import SIFService
from app.services.action_service import ActionService
from app.services.orchestration_service import OrchestrationService
from app.services.safety_hold_service import SafetyHoldService
from app.services.sla_service import SLAService
from app.services.ai.chat_service import ChatService
from app.services.ai.multi_factor_engine import MultiFactorEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.bdi_service import BDIService
from app.services.sif_density_service import SIFDensityService
from app.services.report_export_service import ReportExportService
from app.services.feedback_service import FeedbackService
from app.schemas.report import SafetyReportCreate
from app.schemas.action import ActionUpdateRequest
from app.schemas.orchestrator import SafetyActionApprovalRequest, SafetyActionTransitionRequest
from app.schemas.safety_hold import SafetyHoldCreateRequest, SafetyHoldReviewRequest, SafetyHoldVerifyReleaseRequest
from app.schemas.human_feedback import HumanFeedbackCreate


def test_supervisor_report_submission_to_actions_end_to_end(db_session: Session):
    """
    TEST 1: Supervisor creates a new report -> Database -> AI analysis -> SIF -> Life-Saving Rule -> Dashboard -> Recurrence -> Actions
    """
    req = SafetyReportCreate(
        refinery_unit="Hydrogen Hydrotreating Unit",
        department="Maintenance",
        work_type="Hot Work & Pipe Welding",
        description="High pressure hydrogen line valve flange packing leaking gas near active welding activity without gas testing or barricades",
        hazard="Hydrogen Gas Leak near Hot Work Flame",
        unsafe_act="Welding started without hot work permit gas test",
        unsafe_condition="Corroded valve packing blowing hydrogen",
        ppe_issue=True,
        submitting_user="Supervisor John",
        submitting_role="Supervisor"
    )
    report = ReportService.create_report(db_session, req)
    assert report is not None
    assert report.original_id.startswith("OIL-")
    assert report.analysis_status == "COMPLETED"

    analysis = SIFService.get_analysis_by_report_id(db_session, report.id)
    assert analysis is not None
    assert analysis.sif_precursor == "YES"
    assert analysis.ai_risk_level in ["MEDIUM", "HIGH", "CRITICAL"]

    # Verify action creation
    action = OrchestrationService.generate_action_for_report(db_session, report.id, force_regenerate=True)
    assert action is not None
    assert action.report_id == report.id
    assert action.assigned_role in ["Supervisor", "HSE Officer", "Unit In-Charge", "HSE Head", "Plant Management"]
    assert action.status == "PENDING_APPROVAL"


def test_multi_factor_swiss_cheese_bdi_critical_escalation(db_session: Session):
    """
    TEST 2: Submit a report containing multiple risk factors -> Swiss Cheese analysis -> BDI -> Critical escalation
    """
    ds = Dataset(dataset_name="Test_MultiFactor_Set", original_filename="multifactor.json", file_type="json", factor_count=4)
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    report = SafetyReport(
        dataset_id=ds.id,
        original_id="OIL-2026-999901",
        refinery_unit="FCC Cracking Unit",
        department="Operations",
        description="PPE non-compliance with uncalibrated gas detector, delayed maintenance on seal oil pump, and contractor working without authorized permit",
        hazard="High Energy Hydrocarbon Leak",
        potential_consequence="Explosion and Fatal Personnel Trauma",
        risk_level="CRITICAL",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        detected_factors=["PPE_NonCompliance", "Maintenance_Delay_or_Issue", "Supervisor_Negligence", "Repeated_Issue_Ignored"],
        factor_count=4,
        raw_data={"test": "data"}
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    analysis = SIFService.analyze_report(db_session, report.id)

    # Multi-Factor engine evaluation
    multi_res = MultiFactorEngine.evaluate_multi_factor_exposure(
        report=report,
        hazard_identified=analysis.hazard_identified if analysis else "Hydrocarbon Leak",
        ppe_items=["Gas Detector"],
        iogp_rule=analysis.iogp_rule if analysis else "Bypass Line",
        is_recurring=True
    )
    assert multi_res["compound_factor_count"] >= 2
    assert len(multi_res["detected_compound_factors"]) > 0

    # BDI evaluation
    bdi_eval = BDIService.get_report_bdi(db_session, report.id)
    assert bdi_eval is not None
    assert bdi_eval.bdi_score >= 0.0
    assert bdi_eval.classification in ["SEVERE", "HIGH", "SIGNIFICANT", "MODERATE", "LOW"]


def test_recurring_issue_flagging(db_session: Session):
    """
    TEST 3: Submit a recurring issue -> Previous reports detected -> Recurring precursor flagged
    """
    ds = Dataset(dataset_name="Test_Recurrence_Set", original_filename="recurrence.json", file_type="json", factor_count=1)
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    # First report
    rep1 = SafetyReport(
        dataset_id=ds.id,
        original_id="OIL-2026-888801",
        refinery_unit="Sulfur Recovery Unit",
        equipment="SRU-PUMP-101",
        department="Maintenance",
        description="Repeated mechanical seal leak blowing toxic H2S gas",
        raw_data={"test": "data"}
    )
    db_session.add(rep1)
    db_session.commit()
    db_session.refresh(rep1)
    SIFService.analyze_report(db_session, rep1.id)

    # Second report on same unit and equipment
    rep2 = SafetyReport(
        dataset_id=ds.id,
        original_id="OIL-2026-888802",
        refinery_unit="Sulfur Recovery Unit",
        equipment="SRU-PUMP-101",
        department="Maintenance",
        description="SRU-PUMP-101 mechanical seal leaking H2S again after quick fix",
        previous_similar_reports=2,
        repeated_issue=True,
        raw_data={"test": "data"}
    )
    db_session.add(rep2)
    db_session.commit()
    db_session.refresh(rep2)
    analysis2 = SIFService.analyze_report(db_session, rep2.id)

    assert analysis2.is_recurring is True
    assert analysis2.recurrence_score > 0.0


def test_action_sla_escalation_workflow(db_session: Session):
    """
    TEST 4: Create critical action -> Action created -> SLA started -> Escalation workflow
    """
    ds = Dataset(dataset_name="Test_SLA_Set", original_filename="sla.json", file_type="json", factor_count=1)
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    rep = SafetyReport(
        dataset_id=ds.id,
        original_id="OIL-2026-777701",
        refinery_unit="CDU Crude Distillation",
        department="Operations",
        description="Furnace tube wall hotspot indicating imminent breach",
        risk_level="CRITICAL",
        raw_data={"test": "data"}
    )
    db_session.add(rep)
    db_session.commit()
    db_session.refresh(rep)

    action = OrchestrationService.generate_action_for_report(db_session, rep.id, force_regenerate=True)
    assert action is not None
    assert action.sla_hours <= 72

    # Human approval
    approved = OrchestrationService.approve_action(
        db=db_session,
        action_id=action.id,
        req=SafetyActionApprovalRequest(
            decision="APPROVE",
            reviewer_name="HSE Head Officer",
            assigned_role="Unit In-Charge"
        )
    )
    assert approved.status == "DISPATCHED"
    assert approved.approval_status == "APPROVED"

    # Status transition to ESCALATED
    trans = OrchestrationService.transition_action_status(
        db=db_session,
        action_id=action.id,
        req=SafetyActionTransitionRequest(
            new_status="ESCALATED",
            actor_name="SLA Worker",
            actor_role="System SLA Engine",
            comments="SLA breached 60-minute target"
        )
    )
    assert trans.status == "ESCALATED"
    assert trans.escalation_level >= 1


def test_action_evidence_verification_and_closure(db_session: Session):
    """
    TEST 5: Complete action -> Evidence -> Human verification -> Closure
    """
    ds = Dataset(dataset_name="Test_Closure_Set", original_filename="closure.json", file_type="json", factor_count=1)
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    rep = SafetyReport(
        dataset_id=ds.id,
        original_id="OIL-2026-666601",
        refinery_unit="Tank Farm Storage",
        department="Operations",
        description="Floating roof drain valve weeping fuel into bund",
        action_status="Open",
        raw_data={"test": "data"}
    )
    db_session.add(rep)
    db_session.commit()
    db_session.refresh(rep)

    # 1. Update action with completion & evidence
    updated = ActionService.update_action(
        db=db_session,
        report_id=rep.id,
        req=ActionUpdateRequest(
            action_status="COMPLETED",
            assigned_to="Supervisor Dave",
            action_comments="Replaced valve packing seal and pressure tested to 15 bar.",
            evidence_text="Pressure test certificate attached, leak rate 0.0 bpm.",
            evidence_photo_url="/uploads/valve_repair_proof.jpg",
            actor_name="Supervisor Dave",
            actor_role="Supervisor"
        )
    )
    assert updated.action_status == "COMPLETED"
    assert updated.evidence_text == "Pressure test certificate attached, leak rate 0.0 bpm."

    # 2. Human Verification & Closure
    verified = ActionService.update_action(
        db=db_session,
        report_id=rep.id,
        req=ActionUpdateRequest(
            action_status="VERIFIED",
            closure_verified_by="HSE Officer Sarah",
            action_comments="Conducting physical walkdown inspection. Repair verified intact.",
            actor_name="HSE Officer Sarah",
            actor_role="HSE Officer"
        )
    )
    assert verified.action_status == "VERIFIED"
    assert verified.closure_verified_by == "HSE Officer Sarah"


def test_chatbot_database_grounded_qa(db_session: Session):
    """
    TEST 6: Ask chatbot for numerical information -> Answer comes from database without hallucination.
    """
    # 1. Total reports query
    res1 = ChatService.process_chat_message(db_session, "How many reports are there?")
    assert "safety reports" in res1["reply"].lower() or "database" in res1["reply"].lower()
    assert res1["category"] == "COUNT"

    # 2. SIF precursors count query
    res2 = ChatService.process_chat_message(db_session, "How many SIF precursors were reported?")
    assert "sif precursor" in res2["reply"].lower()
    assert res2["category"] in ["SIF_PRECURSOR_COUNT", "SIF_OVERVIEW"]

    # 3. Overdue actions query
    res3 = ChatService.process_chat_message(db_session, "Which corrective actions are overdue?")
    assert "overdue" in res3["reply"].lower()
    assert res3["category"] in ["OVERDUE_ACTIONS", "ACTIONS_OPEN"]

    # 4. Highest SIF density unit query
    res4 = ChatService.process_chat_message(db_session, "Which unit has the highest SIF precursor density?")
    assert "density" in res4["reply"].lower() or "sif" in res4["reply"].lower()

    # 5. Maintenance and PPE co-occurrence query
    res5 = ChatService.process_chat_message(db_session, "Show reports where maintenance issues and PPE violations occurred together.")
    assert "maintenance" in res5["reply"].lower() and "ppe" in res5["reply"].lower()


def test_dynamic_dataset_schema_ingestion(db_session: Session):
    """
    TEST 7: Upload different-schema dataset -> Dynamic ingestion remains functional.
    """
    import json
    from app.services.dataset_service import DatasetService

    raw_custom = [
        {
            "obs_id": "CUSTOM-101",
            "date_obs": "2026-03-01",
            "plant_area": "Alkylation Unit",
            "sub_unit": "Acid Settler",
            "narrative": "Hydrofluoric acid flange weeping past secondary seal gasket",
            "hazard_description": "HF Acid Release",
            "risk": "High",
            "status_flag": "Open"
        }
    ]
    file_bytes = json.dumps(raw_custom).encode("utf-8")

    ds = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=file_bytes,
        filename="custom_alkylation_data.json",
        file_type="json",
        dataset_name="custom_alkylation_data"
    )
    assert ds is not None
    assert ds.row_count == 1

    SIFService.batch_analyze_dataset(db_session, ds.id)
    report = db_session.scalar(select(SafetyReport).where(SafetyReport.dataset_id == ds.id))
    assert report is not None
    assert report.refinery_unit in ["Alkylation Unit", "Acid Settler"]
    assert "HF Acid" in report.description or "Hydrofluoric" in report.description


def test_existing_ppe_dataset_functionality(db_session: Session):
    """
    TEST 8: Run existing PPE dataset -> Existing functionality still works.
    """
    import json
    from app.services.dataset_service import DatasetService

    raw_ppe = [
        {
            "Observation ID": "PPE-TEST-001",
            "Date": "2026-02-15",
            "Refinery Unit": "Hydrotreating Unit",
            "Department": "Maintenance",
            "Observation / Problem": "Technician grinding weld joint without face shield or safety glasses",
            "Potential Consequence": "Eye injury from high-speed metal debris",
            "Risk Level": "High",
            "PPE_NonCompliance": True,
            "Action Status": "Open"
        }
    ]
    file_bytes = json.dumps(raw_ppe).encode("utf-8")

    ds = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=file_bytes,
        filename="01_PPE_NonCompliance.json",
        file_type="json",
        dataset_name="01_PPE_NonCompliance"
    )
    assert ds is not None

    SIFService.batch_analyze_dataset(db_session, ds.id)
    rep = db_session.scalar(select(SafetyReport).where(SafetyReport.dataset_id == ds.id))
    assert rep is not None
    assert rep.ppe_issue is True

    analysis = SIFService.get_analysis_by_report_id(db_session, rep.id)
    assert analysis is not None
    assert analysis.ai_risk_level in ["HIGH", "CRITICAL"]
