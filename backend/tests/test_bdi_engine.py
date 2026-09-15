import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.models.safety_correlation import SafetyCorrelation
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.models.barrier_degradation_assessment import BarrierDegradationAssessment
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.barrier_service import BarrierService
from app.services.correlation_service import CorrelationService
from app.services.bdi_service import BDIService


@pytest.fixture(scope="function")
def bdi_test_data(db_session: Session):
    """
    Creates controlled test reports for BDI Engine testing.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="BDI Test Dataset",
        original_filename="bdi_test.xlsx",
        sheet_name="BDI_Test",
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

    # 1. Clean Report (No barriers compromised -> BDI = 0.0, MINIMAL)
    rep_clean = SafetyReport(
        id="rep-bdi-clean-01",
        dataset_id=dataset_id,
        original_id="BDI-001",
        raw_data={"desc": "Routine area inspection; all PPE worn; valid permits on file"},
        refinery_unit="CDU-1",
        equipment="Furnace-F-101",
        department="Operations",
        work_type="Routine Inspection",
        description="Routine area inspection; all PPE worn; valid permits on file",
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

    # 2. Single Degraded Barrier Report (PPE only -> LOW BDI: 12.0 pts)
    rep_low = SafetyReport(
        id="rep-bdi-low-02",
        dataset_id=dataset_id,
        original_id="BDI-002",
        raw_data={"desc": "Worker observed without safety glasses during lube oil top-up"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Operations",
        work_type="Lube Top-up",
        description="Worker observed without safety glasses during lube oil top-up",
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

    # 3. Three Degraded Barriers (PPE + Supervisor + Maintenance -> MODERATE BDI: 54.0 pts)
    rep_moderate = SafetyReport(
        id="rep-bdi-mod-03",
        dataset_id=dataset_id,
        original_id="BDI-003",
        raw_data={"desc": "Technician working without goggles while supervisor deferred pump maintenance check"},
        refinery_unit="CDU-1",
        equipment="Drain-DR-10",
        department="Maintenance",
        work_type="Line Draining",
        description="Technician working without goggles while supervisor deferred pump maintenance check",
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

    # 4. High Degradation (Maintenance Delay + Failed Recurrence + 1 Prev Report -> HIGH BDI: 62.0 pts)
    rep_high = SafetyReport(
        id="rep-bdi-high-04",
        dataset_id=dataset_id,
        original_id="BDI-004",
        raw_data={"desc": "Pump mechanical seal leak recurring; maintenance delayed"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Maintenance",
        work_type="Pump Overhaul",
        description="Pump mechanical seal leak recurring; maintenance delayed",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=False,
        previous_similar_reports=1,
        risk_level="Medium",
        action_status="Closed",
        report_date=datetime(2026, 2, 6, 14, 0, 0)
    )

    # 5. Severe Compound Collapse (Failed Barriers + Repeated Issue + Overdue + High Potential -> SEVERE BDI: 100.0 pts)
    rep_severe = SafetyReport(
        id="rep-bdi-sev-05",
        dataset_id=dataset_id,
        original_id="BDI-005",
        raw_data={"desc": "Booster pump seal catastrophic blowout; worker without PPE; supervisor absent; repeat failure ignored; action overdue"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Operations",
        work_type="Hot Work",
        description="Booster pump seal catastrophic blowout; worker without PPE; supervisor absent; repeat failure ignored; action overdue",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=True,
        previous_similar_reports=4,
        risk_level="Medium",  # Intentionally "Medium" recorded risk to test independence!
        action_status="Overdue",
        report_date=datetime(2026, 2, 8, 16, 0, 0)
    )


    db_session.add_all([rep_clean, rep_low, rep_moderate, rep_high, rep_severe])
    db_session.commit()

    return {
        "dataset_id": dataset_id,
        "rep_clean": rep_clean,
        "rep_low": rep_low,
        "rep_moderate": rep_moderate,
        "rep_high": rep_high,
        "rep_severe": rep_severe
    }


class TestBDIEngine:

    def test_01_minimal_low_bdi_isolated_deficiency(self, db_session: Session, bdi_test_data):
        """Test 1: Single degraded barrier yields LOW BDI (score <= 40)."""
        rep_low = bdi_test_data["rep_low"]
        barriers = BarrierEngine.assess_report_barriers(rep_low)
        res = BDIEngine.calculate_report_bdi(rep_low, barriers)

        assert res["bdi_score"] > 0.0
        assert res["bdi_score"] <= 40.0
        assert res["classification"] in ["MINIMAL", "LOW"]
        assert len(res["component_contributions"]) >= 1
        assert "Personal Protection" in res["component_contributions"][0].description or "Degraded" in res["component_contributions"][0].component_name

    def test_02_moderate_bdi_two_factors(self, db_session: Session, bdi_test_data):
        """Test 2: Two compromised barriers / factors yields MODERATE BDI (40.1 - 60.0)."""
        rep_mod = bdi_test_data["rep_moderate"]
        barriers = BarrierEngine.assess_report_barriers(rep_mod)
        res = BDIEngine.calculate_report_bdi(rep_mod, barriers)

        assert 40.1 <= res["bdi_score"] <= 60.0
        assert res["classification"] == "MODERATE"
        assert res["classification_color"] == "amber"
        comp_names = [c.component_name for c in res["component_contributions"]]
        assert any("Degraded" in c for c in comp_names)
        assert any("Convergence" in c or "Factor" in c for c in comp_names)

    def test_03_high_bdi_multiple_failures_unresolved_actions(self, db_session: Session, bdi_test_data):
        """Test 3: Multiple failed barriers + overdue actions yields HIGH BDI (60.1 - 80.0)."""
        rep_high = bdi_test_data["rep_high"]
        barriers = BarrierEngine.assess_report_barriers(rep_high)
        res = BDIEngine.calculate_report_bdi(rep_high, barriers)

        assert 60.1 <= res["bdi_score"] <= 80.0
        assert res["classification"] == "HIGH"
        assert res["classification_color"] == "orange"
        assert res["explainability"].why_summary != ""
        assert len(res["explainability"].top_contributors) >= 2

    def test_04_severe_bdi_compound_collapse(self, db_session: Session, bdi_test_data):
        """Test 4: 3+ failed/degraded barriers + repeated issue + overdue action + high potential precursor yields SEVERE BDI (80.1 - 100.0)."""
        rep_sev = bdi_test_data["rep_severe"]
        barriers = BarrierEngine.assess_report_barriers(rep_sev)
        res = BDIEngine.calculate_report_bdi(rep_sev, barriers)

        assert 80.1 <= res["bdi_score"] <= 100.0
        assert res["classification"] == "SEVERE"
        assert res["classification_color"] == "red"
        assert "CRITICAL" in res["explainability"].remediation_guidance

    def test_05_no_evidence_fallback(self, db_session: Session, bdi_test_data):
        """Test 5: Report with complete lack of failure evidence maintains MINIMAL BDI and score = 0.0 with clear explainability."""
        rep_clean = bdi_test_data["rep_clean"]
        barriers = BarrierEngine.assess_report_barriers(rep_clean)
        res = BDIEngine.calculate_report_bdi(rep_clean, barriers)

        assert res["bdi_score"] == 0.0
        assert res["classification"] == "MINIMAL"
        assert res["classification_color"] == "green"
        assert len(res["component_contributions"]) == 0
        assert "minimal" in res["explainability"].why_summary.lower()

    def test_06_metric_independence_separation(self, db_session: Session, bdi_test_data):
        """Test 6: Verify Recorded Risk_Level, AI_Risk_Level, BDI, SIF_Precursor, High_Potential remain strictly distinct."""
        rep_sev = bdi_test_data["rep_severe"]
        # Recorded risk is "Medium", but BDI is SEVERE (>= 80), AI Risk is "High", and High Potential is True
        barriers = BarrierEngine.assess_report_barriers(rep_sev)
        res = BDIEngine.calculate_report_bdi(rep_sev, barriers)

        metrics = res["independent_metrics"]
        assert metrics.recorded_risk_level == "Medium"
        assert metrics.bdi_classification == "SEVERE"
        assert metrics.bdi_score >= 80.1
        assert metrics.ai_risk_level == "High"
        assert metrics.high_potential_status is True
        assert metrics.sif_precursor_status is True
        # Recorded risk was NOT overwritten
        assert rep_sev.risk_level == "Medium"

    def test_07_cross_report_convergence_contribution(self, db_session: Session, bdi_test_data):
        """Test 7: Cross-report physical convergence adds points according to transparent weight matrix without double counting."""
        rep_low = bdi_test_data["rep_low"]
        barriers = BarrierEngine.assess_report_barriers(rep_low)

        res_without = BDIEngine.calculate_report_bdi(rep_low, barriers, has_cross_report_correlation=False)
        res_with = BDIEngine.calculate_report_bdi(rep_low, barriers, has_cross_report_correlation=True)

        expected_diff = BDIEngine.DEFAULT_WEIGHTS["cross_report_convergence_points"]
        assert round(res_with["bdi_score"] - res_without["bdi_score"], 1) == expected_diff
        
        cross_comp = next((c for c in res_with["component_contributions"] if "Cross-Report" in c.component_name), None)
        assert cross_comp is not None
        assert cross_comp.points_added == expected_diff

    def test_08_unit_level_bdi_aggregation(self, db_session: Session, bdi_test_data):
        """Test 8: Unit BDI utilizes density and cluster modeling rather than naive average."""
        all_reps = list(db_session.scalars(select(SafetyReport).where(SafetyReport.refinery_unit == "CDU-1")).all())
        all_barriers = []
        for r in all_reps:
            all_barriers.extend(BarrierEngine.assess_report_barriers(r))

        unit_res = BDIEngine.calculate_unit_bdi("CDU-1", all_reps, all_barriers)

        assert unit_res["refinery_unit"] == "CDU-1"
        assert unit_res["data_adequacy_status"] == "SUFFICIENT"
        assert unit_res["total_contributing_reports"] == len(all_reps)
        assert unit_res["unit_bdi_score"] > 0.0
        assert len(unit_res["dominant_degraded_barriers"]) > 0
        assert len(unit_res["dominant_factors"]) > 0
        assert "weighted density modeling" in unit_res["calculation_methodology_note"]

    def test_09_bdi_config_transparency(self):
        """Test 9: Active weights and thresholds are exposed via configuration endpoint with full documentation."""
        cfg = BDIService.get_bdi_config()

        assert "failed_barrier_per_item" in cfg.weights
        assert "max_failed_barriers" in cfg.weights
        assert "degraded_barrier_per_item" in cfg.weights
        assert "MINIMAL" in cfg.thresholds
        assert "SEVERE" in cfg.thresholds
        assert cfg.version == BDIEngine.VERSION
        assert len(cfg.documentation) > 0

    def test_10_bdi_api_routes_integration(self, client: TestClient, db_session: Session, bdi_test_data):
        """Test 10: End-to-end testing of all BDI FastAPI endpoints."""
        rep_sev = bdi_test_data["rep_severe"]

        # 1. GET /api/bdi/report/{report_id}
        res_rep = client.get(f"/api/bdi/report/{rep_sev.id}")
        assert res_rep.status_code == 200
        data_rep = res_rep.json()
        assert data_rep["bdi_score"] >= 80.0
        assert data_rep["classification"] == "SEVERE"
        assert "independent_metrics" in data_rep
        assert data_rep["independent_metrics"]["recorded_risk_level"] == "Medium"

        # 2. GET /api/bdi/unit/{unit_id}
        res_unit = client.get("/api/bdi/unit/CDU-1")
        assert res_unit.status_code == 200
        data_unit = res_unit.json()
        assert data_unit["refinery_unit"] == "CDU-1"
        assert data_unit["unit_bdi_score"] > 0.0

        # 3. GET /api/bdi/high
        res_high = client.get("/api/bdi/high?threshold=60.0")
        assert res_high.status_code == 200
        data_high = res_high.json()
        assert data_high["total_high_bdi_count"] >= 2
        assert len(data_high["items"]) >= 2

        # 4. GET /api/bdi/summary
        res_sum = client.get("/api/bdi/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert data_sum["total_reports_analyzed"] >= 5
        assert data_sum["average_bdi"] > 0.0
        assert "active_weights" in data_sum

        # 5. GET /api/bdi/trends
        res_trends = client.get("/api/bdi/trends")
        assert res_trends.status_code == 200
        data_trends = res_trends.json()
        assert len(data_trends["monthly_trends"]) > 0

        # 6. GET /api/bdi/config
        res_cfg = client.get("/api/bdi/config")
        assert res_cfg.status_code == 200
        data_cfg = res_cfg.json()
        assert "weights" in data_cfg
        assert "thresholds" in data_cfg

        # 7. POST /api/bdi/assess (batch persistence)
        res_assess = client.post("/api/bdi/assess")
        assert res_assess.status_code == 200
        data_assess = res_assess.json()
        assert data_assess["status"] == "success"
        assert data_assess["assessments_created"] >= 5

        # Verify records persisted in DB
        db_count = db_session.query(BarrierDegradationAssessment).count()
        assert db_count >= 5

        # 8. 404 for non-existent report
        res_404 = client.get("/api/bdi/report/non-existent-report-id")
        assert res_404.status_code == 404
