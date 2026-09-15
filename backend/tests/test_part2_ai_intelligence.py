import pytest
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, init_db
from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.report_analysis import ReportAnalysis
from app.services.ai.iogp_engine import IOGPEngine
from app.services.ai.nlp_engine import NLPEngine
from app.services.ai.sif_engine import SIFPrecursorEngine
from app.services.ai.preventive_engine import PreventiveIntelligenceEngine
from app.services.ai.recurrence_engine import RecurrenceEngine
from app.services.sif_service import SIFService
from app.schemas.sif import AIFeedbackCreate


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_iogp_rules_classifier_all_9_rules():
    """Verify IOGPEngine correctly classifies all 9 IOGP Life-Saving Rules."""

    test_cases = [
        ("Operator bypassed safety interlock on relief valve.", "Bypassing Safety Controls"),
        ("Entering vessel without confined space gas testing permit.", "Confined Space"),
        ("Driver operating forklift over speed limit without seatbelt.", "Driving"),
        ("Line breakdown maintenance performed without LOTO electrical isolation.", "Energy Isolation"),
        ("Welding sparks near flammable gas drain line without fire watch.", "Hot Work"),
        ("Rigger standing in line of fire under suspended pipe load.", "Line of Fire"),
        ("Crane hoist sling frayed beyond safety load capacity limit.", "Safe Mechanical Lifting"),
        ("Worker starting maintenance without valid Permit to Work (PTW).", "Work Authorisation"),
        ("Scaffold technician working at 8m height without safety harness tie-off.", "Working at Height"),
    ]

    for narrative, expected_rule in test_cases:
        rule, secondary, conf, reasoning = IOGPEngine.classify_iogp_rules(narrative)
        assert rule == expected_rule, f"Expected '{expected_rule}', got '{rule}' for text: {narrative}"
        assert conf > 0.6
        assert len(reasoning) > 10


def test_iogp_fallback_when_no_evidence():
    """Verify IOGP engine returns default fallback when report narrative lacks explicit indicators."""
    narrative = "Minor paperwork typo noted on shift handover log."
    rule, secondary, conf, reasoning = IOGPEngine.classify_iogp_rules(narrative)
    assert rule == "No clear Life-Saving Rule match"
    assert conf == 0.0
    assert "No explicit evidence" in reasoning


def test_sif_precursor_and_risk_evaluation():
    """Verify SIFPrecursorEngine evaluates precursors and AI risk while preserving recorded risk."""
    sif, cat, ai_risk, conf, reasons, org = SIFPrecursorEngine.evaluate_sif(
        hazard_identified="Thermal / Flash Fire",
        ppe_items=["fire-resistant clothing"],
        violation_type="MISSING_PPE",
        recorded_risk="Low",
        potential_consequence="Severe thermal burn & lost-time injury",
        immediate_cause="Worker unbuttoned FR coverall near hot pipe",
        work_type="Hot Work",
        refinery_unit="CDU",
        previous_similar_reports=2,
        action_status="Open",
        high_potential_flag=True
    )

    assert sif == "YES"
    assert cat == "Thermal / Flash Fire Hazard"
    assert ai_risk in ["HIGH", "CRITICAL"]
    assert conf >= 0.80
    assert any("High-energy hazard" in r for r in reasons)
    assert any("High Potential" in r for r in reasons)


def test_preventive_intelligence_and_escalation_scenario():
    """Verify PreventiveIntelligenceEngine generates containment and 6-stage escalation scenarios."""
    imm = PreventiveIntelligenceEngine.generate_immediate_action(
        observed_problem="Welder working without face shield",
        ppe_items=["face shield"],
        violation_type="MISSING_PPE",
        work_type="Hot Work",
        department="Maintenance",
        sif_precursor="YES"
    )
    assert "hot work" in imm.lower() or "pause" in imm.lower()

    scenario = PreventiveIntelligenceEngine.build_escalation_scenario(
        observed_problem="Scaffold worker missing lanyard",
        hazard_identified="Fall from Elevated Structure",
        ppe_items=["safety harness"],
        work_type="Work at Height",
        refinery_unit="FCC",
        potential_consequence="Fatality / Traumatic Fall",
        sif_precursor="YES"
    )
    assert "current_condition" in scenario
    assert "continued_exposure" in scenario
    assert "loss_of_control" in scenario
    assert "incident_event" in scenario
    assert "serious_consequence" in scenario
    assert "potential_fatal_consequence" in scenario


def test_end_to_end_report_analysis_service(db_session: Session):
    """Verify full end-to-end report analysis with IOGP, SIF, barrier, and recurrence persistence."""
    db_session.rollback()
    test_ds = db_session.query(Dataset).first()
    ds_id = test_ds.id if test_ds else "test-ds-part2"

    report = SafetyReport(
        dataset_id=ds_id,
        original_id="TEST-PART2-001",
        raw_data={"description": "Technician observed breaking flange on pressurized naphtha line without energy isolation LOTO or face shield."},
        description="Technician observed breaking flange on pressurized naphtha line without energy isolation LOTO or face shield.",
        refinery_unit="Hydrotreating Unit",
        equipment="Naphtha Line Pump-101",
        work_type="Energy Isolation",
        department="Operations",
        hazard="High-Pressure Hydrocarbon & Thermal Hazard",
        risk_level="Medium",
        supervisor_factor=True,
        high_potential=True,
        previous_similar_reports=3,
        repeated_issue=True
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Perform analysis
    analysis = SIFService.analyze_report(db_session, report.id)

    assert analysis is not None
    assert analysis.report_id == report.id
    assert analysis.iogp_rule in ["Energy Isolation", "Bypassing Safety Controls"]
    assert analysis.sif_precursor == "YES"
    assert analysis.recorded_risk_level == "Medium"
    assert analysis.ai_risk_level in ["HIGH", "CRITICAL"]
    assert analysis.is_recurring is True
    assert len(analysis.reasoning) > 0
    assert analysis.barrier_failure is not None

    # Submit Human Feedback Override
    fb_data = AIFeedbackCreate(
        report_id=report.id,
        reviewer_name="Chief Safety Inspector",
        agrees_with_ai=False,
        human_risk_level="Critical",
        human_sif_precursor="YES",
        feedback_reason="Confirmed high-pressure naphtha exposure with multi-barrier failure."
    )
    fb = SIFService.submit_feedback(db_session, fb_data)
    assert fb.human_risk_level == "Critical"

    # Re-fetch analysis to verify override fields updated
    updated_analysis = SIFService.get_analysis_by_report_id(db_session, report.id)
    assert updated_analysis.human_overridden is True
    assert updated_analysis.human_risk_level == "Critical"
    assert updated_analysis.human_feedback_reason == fb_data.feedback_reason


def test_batch_analyze_dataset_regression(db_session: Session):
    """Verify batch dataset analysis processes all ingested reports cleanly."""
    res = SIFService.batch_analyze_dataset(db_session)
    assert res["status"] in ["completed", "empty"]
    assert res["total_reports"] >= 0
