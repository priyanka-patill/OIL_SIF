import os
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.models.safety_correlation import SafetyCorrelation
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.models.barrier_degradation_assessment import BarrierDegradationAssessment
from app.models.sif_escalation_assessment import SIFEscalationAssessment
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.ai.sif_escalation_engine import SIFEscalationEngine
from app.services.sif_escalation_service import SIFEscalationService


@pytest.fixture(scope="function")
def escalation_test_data(db_session: Session):
    """
    Creates controlled test reports across all severity dimensions for SIF Escalation testing.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="SIF Escalation Test Dataset",
        original_filename="escalation_test.xlsx",
        sheet_name="Escalation_Test",
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

    # 1. NORMAL (Routine compliant report, no barriers degraded)
    rep_normal = SafetyReport(
        id="rep-esc-normal-01",
        dataset_id=dataset_id,
        original_id="ESC-001",
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

    # 2. WATCH (Single isolated barrier deficiency, low energy)
    rep_watch = SafetyReport(
        id="rep-esc-watch-02",
        dataset_id=dataset_id,
        original_id="ESC-002",
        raw_data={"desc": "Worker observed without safety glasses during lube oil top-up"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Operations",
        work_type="Lube Top-up",
        description="Worker observed without safety glasses during lube oil top-up",
        hazard="Lube oil splash",
        potential_consequence="Eye irritation",
        ppe_issue=True,
        supervisor_factor=False,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 2, 2, 10, 0, 0)
    )

    # 3. ELEVATED (Moderate barrier degradation, 2-3 factors without catastrophic energy)
    rep_elevated = SafetyReport(
        id="rep-esc-elev-03",
        dataset_id=dataset_id,
        original_id="ESC-003",
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

    # 4. HIGH (Direct high-energy SIF precursor + open action + maintenance delay)
    rep_high = SafetyReport(
        id="rep-esc-high-04",
        dataset_id=dataset_id,
        original_id="ESC-004",
        raw_data={"desc": "Heavy hydrocarbon pump seal weeping near hot furnace; maintenance delayed; corrective action in progress"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
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

    # 5. CRITICAL (Catastrophic energy + High Potential Near Miss + 3+ failed/degraded barriers + overdue action)
    rep_critical = SafetyReport(
        id="rep-esc-crit-05",
        dataset_id=dataset_id,
        original_id="ESC-005",
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

    # 6. High BDI on Low-Energy Event (Demonstrates false-positive prevention: BDI alone != CRITICAL)
    rep_high_bdi_low_energy = SafetyReport(
        id="rep-esc-lowenergy-06",
        dataset_id=dataset_id,
        original_id="ESC-006",
        raw_data={"desc": "Office storage room shelf audit delayed, supervisor absent during paper archive filing, repeat housekeeping issue, action overdue"},
        refinery_unit="Admin Building",
        equipment="Shelf-S-10",
        department="Administration",
        work_type="Office Archiving",
        description="Office storage room shelf audit delayed, supervisor absent during paper archive filing, repeat housekeeping issue, action overdue",
        hazard="Paper box drop",
        potential_consequence="Minor bruise",
        ppe_issue=False,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=False,
        previous_similar_reports=3,
        risk_level="Low",
        action_status="Overdue",
        report_date=datetime(2026, 2, 10, 8, 0, 0)
    )

    # 7. Insufficient/Neutral Data Report
    rep_neutral = SafetyReport(
        id="rep-esc-neutral-07",
        dataset_id=dataset_id,
        original_id="ESC-007",
        raw_data={"desc": "End of shift daily shift handover log recorded in control room"},
        refinery_unit="Control Room",
        equipment=None,
        department="Operations",
        work_type="Shift Handover",
        description="End of shift daily shift handover log recorded in control room",
        hazard=None,
        potential_consequence=None,
        ppe_issue=None,
        supervisor_factor=None,
        maintenance_factor=None,
        repeated_issue=None,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 2, 12, 18, 0, 0)
    )

    db_session.add_all([
        rep_normal, rep_watch, rep_elevated, rep_high, rep_critical,
        rep_high_bdi_low_energy, rep_neutral
    ])
    db_session.commit()

    return {
        "dataset_id": dataset_id,
        "rep_normal": rep_normal,
        "rep_watch": rep_watch,
        "rep_elevated": rep_elevated,
        "rep_high": rep_high,
        "rep_critical": rep_critical,
        "rep_high_bdi_low_energy": rep_high_bdi_low_energy,
        "rep_neutral": rep_neutral
    }


class TestSIFEscalationEngine:

    def test_01_normal_severity_clean_report(self, db_session: Session, escalation_test_data):
        """Test 1: Verified compliance produces NORMAL severity with intact barriers."""
        rep = escalation_test_data["rep_normal"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] == "NORMAL"
        assert res["severity_color"] == "green"
        assert res["sif_precursor_status"] is False
        assert len(res["which_barriers"]) == 0
        assert "NORMAL" in res["why_escalated"]

    def test_02_watch_severity_isolated_deficiency(self, db_session: Session, escalation_test_data):
        """Test 2: Single degraded barrier without high energy produces WATCH."""
        rep = escalation_test_data["rep_watch"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] == "WATCH"
        assert res["severity_color"] == "cyan"
        assert res["sif_precursor_status"] is False
        assert len(res["which_barriers"]) == 1
        assert "WATCH" in res["why_escalated"]

    def test_03_elevated_severity_two_factors(self, db_session: Session, escalation_test_data):
        """Test 3: 2-3 compromised barriers / moderate BDI produces ELEVATED."""
        rep = escalation_test_data["rep_elevated"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] == "ELEVATED"
        assert res["severity_color"] == "amber"
        assert len(res["which_barriers"]) >= 2
        assert "ELEVATED" in res["why_escalated"]

    def test_04_high_severity_direct_precursor(self, db_session: Session, escalation_test_data):
        """Test 4: High energy hazard + overdue action / high BDI produces HIGH severity and Preventive Intelligence."""
        rep = escalation_test_data["rep_high"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] == "HIGH"
        assert res["severity_color"] == "orange"
        assert res["sif_precursor_status"] is True
        assert res["preventive_intelligence"] is not None
        assert "Flash Fire" in res["sif_category"] or "Hydrocarbon" in res["sif_category"]

    def test_05_critical_severity_multi_dimensional_convergence(self, db_session: Session, escalation_test_data):
        """Test 5: Catastrophic energy + 3+ failed/degraded barriers + overdue action + HiPo near miss produces CRITICAL."""
        rep = escalation_test_data["rep_critical"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] == "CRITICAL"
        assert res["severity_color"] == "red"
        assert res["sif_precursor_status"] is True
        assert len(res["escalation_scenario"]) == 7
        assert res["escalation_scenario"][0].stage_name == "CURRENT CONDITION"
        assert res["escalation_scenario"][6].stage_name == "POTENTIAL FATAL CONSEQUENCE"
        assert res["preventive_intelligence"] is not None
        assert "MANDATORY STOP-WORK" in res["preventive_intelligence"].immediate_containment

    def test_06_not_bdi_alone_critical_rule(self, db_session: Session, escalation_test_data):
        """Test 6: High BDI on low-energy administrative event does NOT trigger CRITICAL, preventing false positives."""
        rep = escalation_test_data["rep_high_bdi_low_energy"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        # Even with high BDI (from repeated issue + overdue action + supervisor factor), because it's paper drop / office,
        # it must NOT be marked CRITICAL
        assert res["severity"] != "CRITICAL"
        assert res["severity"] in ["ELEVATED", "HIGH"]

    def test_07_cross_report_convergence_escalation(self, db_session: Session, escalation_test_data):
        """Test 7: Cross-report physical convergence adds dimension and populates which_reports."""
        rep_high = escalation_test_data["rep_high"]
        rep_crit = escalation_test_data["rep_critical"]
        barriers = BarrierEngine.assess_report_barriers(rep_high)
        bdi_res = BDIEngine.calculate_report_bdi(rep_high, barriers, has_cross_report_correlation=True)

        res = SIFEscalationEngine.evaluate_escalation(
            report=rep_high,
            barriers=barriers,
            bdi_score=bdi_res["bdi_score"],
            bdi_classification=bdi_res["classification"],
            has_cross_report_correlation=True,
            correlated_reports=[rep_crit]
        )

        assert len(res["which_reports"]) >= 2
        assert rep_crit.id in res["which_reports"]
        assert any("Cross-Report" in f for f in res["contributing_factors"])

    def test_08_unresolved_overdue_action_impact(self, db_session: Session, escalation_test_data):
        """Test 8: Overdue corrective action is highlighted in what_remains_unresolved."""
        rep = escalation_test_data["rep_critical"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert any("OVERDUE" in u for u in res["what_remains_unresolved"])

    def test_09_explainability_all_questions_answered(self, db_session: Session, escalation_test_data):
        """Test 9: Verifies that all 8 required explanation questions are addressed in the response."""
        rep = escalation_test_data["rep_critical"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        # 1. Why escalated?
        assert res["why_escalated"] != ""
        # 2. Which barriers?
        assert len(res["which_barriers"]) > 0
        # 3. Which factors?
        assert len(res["which_factors"]) > 0
        # 4. Which reports?
        assert len(res["which_reports"]) > 0
        # 5. What exposure?
        assert res["what_exposure"] != ""
        # 6. What potential consequence?
        assert res["what_potential_consequence"] != ""
        # 7. What remains unresolved?
        assert len(res["what_remains_unresolved"]) > 0
        # 8. What could happen?
        assert res["what_could_happen"] != ""

    def test_10_preventive_intelligence_payload(self, db_session: Session, escalation_test_data):
        """Test 10: High/Critical responses contain complete 6-point containment and prevention payload."""
        rep = escalation_test_data["rep_critical"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        intel = res["preventive_intelligence"]
        assert intel is not None
        assert intel.current_condition != ""
        assert intel.hazard_exposure != ""
        assert intel.control_failure != ""
        assert intel.immediate_containment != ""
        assert intel.preventive_control != ""
        assert intel.potential_escalation != ""

    def test_11_insufficient_data_handling(self, db_session: Session, escalation_test_data):
        """Test 11: Missing/neutral data safely defaults to NORMAL without hallucinating failures."""
        rep = escalation_test_data["rep_neutral"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        bdi_res = BDIEngine.calculate_report_bdi(rep, barriers)
        res = SIFEscalationEngine.evaluate_escalation(rep, barriers, bdi_res["bdi_score"], bdi_res["classification"])

        assert res["severity"] in ["NORMAL", "WATCH"]
        assert res["sif_precursor_status"] is False
        assert len(res["which_barriers"]) == 0

    def test_12_api_routes_and_persistence(self, client: TestClient, db_session: Session, escalation_test_data):
        """Test 12: Full end-to-end integration testing of all 6 FastAPI routes and database persistence."""
        rep_crit = escalation_test_data["rep_critical"]

        # 1. GET /api/sif/escalation/report/{report_id}
        res_rep = client.get(f"/api/sif/escalation/report/{rep_crit.id}")
        assert res_rep.status_code == 200
        data_rep = res_rep.json()
        assert data_rep["severity"] == "CRITICAL"
        assert data_rep["sif_precursor_status"] is True
        assert len(data_rep["escalation_scenario"]) == 7
        assert data_rep["preventive_intelligence"] is not None

        # 2. GET /api/sif/escalation/critical
        res_crit = client.get("/api/sif/escalation/critical")
        assert res_crit.status_code == 200
        data_crit = res_crit.json()
        assert data_crit["total_critical_count"] >= 1
        assert len(data_crit["items"]) >= 1

        # 3. GET /api/sif/escalation/high
        res_high = client.get("/api/sif/escalation/high")
        assert res_high.status_code == 200
        data_high = res_high.json()
        assert data_high["total_high_count"] >= 2

        # 4. GET /api/sif/escalation/summary
        res_sum = client.get("/api/sif/escalation/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert data_sum["total_reports_evaluated"] >= 7
        assert data_sum["critical_count"] >= 1

        # 5. GET /api/sif/escalation/unit/{unit_id}
        res_unit = client.get("/api/sif/escalation/unit/CDU-1")
        assert res_unit.status_code == 200
        data_unit = res_unit.json()
        assert data_unit["refinery_unit"] == "CDU-1"
        assert data_unit["critical_reports_count"] >= 1

        # 6. POST /api/sif/escalation/assess (batch calculation & persistence)
        res_assess = client.post("/api/sif/escalation/assess")
        assert res_assess.status_code == 200
        data_assess = res_assess.json()
        assert data_assess["status"] == "success"
        assert data_assess["assessments_created"] >= 7

        # Verify records stored in DB
        db_count = db_session.query(SIFEscalationAssessment).count()
        assert db_count >= 7

        # 7. 404 for non-existent report
        res_404 = client.get("/api/sif/escalation/report/non-existent-report-id")
        assert res_404.status_code == 404
