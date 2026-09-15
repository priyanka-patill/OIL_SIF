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
from app.services.ai.barrier_engine import BarrierEngine
from app.services.barrier_service import BarrierService
from app.services.correlation_service import CorrelationService


@pytest.fixture(scope="function")
def barrier_test_data(db_session: Session):
    """
    Creates controlled test reports for Swiss Cheese Barrier Model testing.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="Barrier Test Dataset",
        original_filename="barrier_test.xlsx",
        sheet_name="Barrier_Test",
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

    # 1. Intact Barrier Report (verified compliance)
    rep_intact = SafetyReport(
        id="rep-barrier-intact-01",
        dataset_id=dataset_id,
        original_id="BAR-001",
        raw_data={"desc": "Routine inspection; wearing all PPE; supervisor verified permit on site"},
        refinery_unit="CDU-1",
        equipment="Furnace-F-101",
        department="Operations",
        work_type="Routine Inspection",
        description="Routine inspection in furnace area. Wearing all PPE and supervisor verified on site with valid permit.",
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

    # 2. Single Degraded Barrier Report (PPE only)
    rep_single_degraded = SafetyReport(
        id="rep-barrier-degraded-02",
        dataset_id=dataset_id,
        original_id="BAR-002",
        raw_data={"desc": "Technician observed without safety glasses near sampling point"},
        refinery_unit="CDU-1",
        equipment="Sampler-SP-10",
        department="Quality",
        work_type="Sampling",
        description="Technician observed without safety glasses near sampling point",
        ppe_issue=True,
        supervisor_factor=False,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 2, 3, 10, 30, 0)
    )

    # 3. Failed Barrier Report (Repeated issue ignored & overdue action)
    rep_failed = SafetyReport(
        id="rep-barrier-failed-03",
        dataset_id=dataset_id,
        original_id="BAR-003",
        raw_data={"desc": "Recurrence of valve packing leakage on Pump-P-101; 4th occurrence this quarter"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Maintenance",
        work_type="Pump Maintenance",
        description="Recurrence of valve packing leakage on Pump-P-101; 4th occurrence this quarter",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=False,
        previous_similar_reports=4,
        risk_level="High",
        action_status="Overdue",
        report_date=datetime(2026, 2, 5, 14, 0, 0)
    )

    # 4. Multi-Barrier Breakdown Report (PPE + Supervisor + Maintenance + Open Action)
    rep_multi = SafetyReport(
        id="rep-barrier-multi-04",
        dataset_id=dataset_id,
        original_id="BAR-004",
        raw_data={"desc": "Booster pump seal failure; worker without visor; supervisor absent during hot work"},
        refinery_unit="CDU-1",
        equipment="Pump-P-101",
        department="Operations",
        work_type="Hot Work",
        description="Booster pump seal failure; worker without visor; supervisor absent during hot work; no permit authorization",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=True,
        previous_similar_reports=0,
        risk_level="Critical",
        action_status="Open",
        report_date=datetime(2026, 2, 8, 11, 0, 0)
    )

    # 5. Clean Report with No Barrier Data (neutral/administrative)
    rep_clean = SafetyReport(
        id="rep-barrier-clean-05",
        dataset_id=dataset_id,
        original_id="BAR-005",
        raw_data={"desc": "Administrative filing of daily shift log in control room"},
        refinery_unit="Control Room",
        equipment=None,
        department="Administration",
        work_type="Office Work",
        description="Administrative filing of daily shift log in control room",
        ppe_issue=None,
        supervisor_factor=None,
        maintenance_factor=None,
        repeated_issue=None,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 2, 10, 8, 0, 0)
    )

    db_session.add_all([rep_intact, rep_single_degraded, rep_failed, rep_multi, rep_clean])
    db_session.commit()

    return {
        "dataset_id": dataset_id,
        "rep_intact": rep_intact,
        "rep_single_degraded": rep_single_degraded,
        "rep_failed": rep_failed,
        "rep_multi": rep_multi,
        "rep_clean": rep_clean
    }


class TestBarrierEngine:

    def test_01_intact_barrier(self, db_session: Session, barrier_test_data):
        """Test 1: Report with positive compliance evidence marks barriers as INTACT."""
        rep = barrier_test_data["rep_intact"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        intact_barriers = [b for b in barriers if b.status == "INTACT"]
        assert len(intact_barriers) >= 2
        # Corrective action closed and verified
        act_b = next((b for b in barriers if b.barrier_id == "CORRECTIVE_ACTION"), None)
        assert act_b is not None
        assert act_b.status == "INTACT"

    def test_02_degraded_barrier(self, db_session: Session, barrier_test_data):
        """Test 2: Non-compliance / maintenance delay / in-progress action marked as DEGRADED."""
        rep = barrier_test_data["rep_single_degraded"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        ppe_b = next((b for b in barriers if b.barrier_id == "PERSONAL_PROTECTION"), None)
        assert ppe_b is not None
        assert ppe_b.status == "DEGRADED"
        assert ppe_b.explainability.why != ""
        assert "ppe_issue" in ppe_b.source_fields

    def test_03_failed_barrier(self, db_session: Session, barrier_test_data):
        """Test 3: Repeated issue ignored / overdue action marked as FAILED."""
        rep = barrier_test_data["rep_failed"]
        barriers = BarrierEngine.assess_report_barriers(rep)

        # Recurrence prevention barrier must be FAILED because repeat occurred
        rec_b = next((b for b in barriers if b.barrier_id == "RECURRENCE_PREVENTION"), None)
        assert rec_b is not None
        assert rec_b.status == "FAILED"
        assert "repeated_issue" in rec_b.source_fields

        # Corrective action overdue must be FAILED
        act_b = next((b for b in barriers if b.barrier_id == "CORRECTIVE_ACTION"), None)
        assert act_b is not None
        assert act_b.status == "FAILED"

    def test_04_unknown_barrier(self, db_session: Session, barrier_test_data):
        """Test 4: Unspecified / missing fields remain UNKNOWN and are NOT classified as failed."""
        rep = barrier_test_data["rep_clean"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        # Should NOT classify unmentioned barriers as FAILED
        failed = [b for b in barriers if b.status == "FAILED"]
        assert len(failed) == 0

    def test_05_single_barrier_degradation(self, db_session: Session, barrier_test_data):
        """Test 5: Single barrier failure generates 1 hole and MINOR convergence."""
        rep = barrier_test_data["rep_single_degraded"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        swiss = BarrierEngine.build_swiss_cheese_model(barriers, exposure_target="CDU-1 / Sampler")

        assert swiss.holes_aligned_count == 1
        assert swiss.convergence_level == "MINOR"
        assert len(swiss.escalation_pathway) > 0

    def test_06_multiple_barrier_degradation(self, db_session: Session, barrier_test_data):
        """Test 6: Multiple barrier failures generate 3+ holes aligned and CRITICAL_CONVERGENCE."""
        rep = barrier_test_data["rep_multi"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        swiss = BarrierEngine.build_swiss_cheese_model(barriers, exposure_target="CDU-1 / Pump-P-101")

        assert swiss.holes_aligned_count >= 3
        assert swiss.convergence_level == "CRITICAL_CONVERGENCE"
        assert "URGENT" in swiss.preventive_barrier_imperative

    def test_07_cross_report_barrier_convergence(self, db_session: Session, barrier_test_data):
        """Test 7: Cross-report convergence merges barrier holes across correlated reports without merging original records."""
        rep_failed = barrier_test_data["rep_failed"]  # Pump-P-101: Recurrence FAILED + Action FAILED + Maintenance DEGRADED
        rep_multi = barrier_test_data["rep_multi"]    # Pump-P-101: PPE DEGRADED + Supervision DEGRADED + Procedural DEGRADED

        # Synthesize cross-report barrier model
        syn_barriers = BarrierEngine.synthesize_cross_report_barriers(rep_failed, [rep_multi])
        swiss = BarrierEngine.build_swiss_cheese_model(syn_barriers, exposure_target="CDU-1 / Pump-P-101")

        # Holes aligned across combined reports
        assert swiss.holes_aligned_count >= 4
        assert swiss.failed_count >= 2
        assert swiss.convergence_level == "CRITICAL_CONVERGENCE"

        # Reports must remain separate in database
        assert db_session.query(SafetyReport).count() == 5

    def test_08_no_evidence(self, db_session: Session, barrier_test_data):
        """Test 8: Neutral report does not activate spurious barriers."""
        rep = barrier_test_data["rep_clean"]
        barriers = BarrierEngine.assess_report_barriers(rep)
        degraded_or_failed = [b for b in barriers if b.status in ["DEGRADED", "FAILED"]]
        assert len(degraded_or_failed) == 0

    def test_09_barrier_api_endpoints(self, client: TestClient, db_session: Session, barrier_test_data):
        """Test 9: Verify all 6 FastAPI barrier endpoints."""
        rep_multi = barrier_test_data["rep_multi"]

        # 1. GET /api/barriers/report/{report_id}
        res_rep = client.get(f"/api/barriers/report/{rep_multi.id}")
        assert res_rep.status_code == 200
        data_rep = res_rep.json()
        assert "swiss_cheese" in data_rep
        assert data_rep["swiss_cheese"]["holes_aligned_count"] >= 3

        # 2. GET /api/barriers/unit/{unit_id}
        res_unit = client.get("/api/barriers/unit/CDU-1")
        assert res_unit.status_code == 200
        data_unit = res_unit.json()
        assert data_unit["total_assessments"] > 0
        assert "barrier_health_scores" in data_unit

        # 3. GET /api/barriers/critical
        res_crit = client.get("/api/barriers/critical")
        assert res_crit.status_code == 200
        data_crit = res_crit.json()
        assert "total_critical_convergences" in data_crit
        assert len(data_crit["convergences"]) > 0

        # 4. GET /api/barriers/summary
        res_sum = client.get("/api/barriers/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert "total_barrier_assessments" in data_sum
        assert "top_weakened_barriers" in data_sum

        # 5. GET /api/barriers/convergence
        res_conv = client.get("/api/barriers/convergence")
        assert res_conv.status_code == 200
        data_conv = res_conv.json()
        assert "total_convergence_clusters" in data_conv

        # 6. POST /api/barriers/assess
        res_assess = client.post("/api/barriers/assess")
        assert res_assess.status_code == 200
        data_assess = res_assess.json()
        assert data_assess["status"] == "success"

        # 7. 404 for non-existent report
        res_404 = client.get("/api/barriers/report/non-existent-id")
        assert res_404.status_code == 404

    def test_10_full_regression_with_correlation(self, db_session: Session, barrier_test_data):
        """Test 10: Verify seamless integration between Phase 1 Correlation Service and Phase 2 Barrier Service."""
        dataset_id = barrier_test_data["dataset_id"]
        # Batch compute Phase 1 correlations
        CorrelationService.batch_compute_correlations(db_session, dataset_id)

        rep_multi = barrier_test_data["rep_multi"]
        corr_res = CorrelationService.correlate_single_report(db_session, rep_multi.id)
        assert corr_res is not None

        barrier_res = BarrierService.get_report_barriers(db_session, rep_multi.id)
        assert barrier_res is not None
        assert barrier_res.swiss_cheese.holes_aligned_count >= 3
