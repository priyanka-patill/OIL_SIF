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
from app.services.ai.correlation_engine import CorrelationEngine
from app.services.correlation_service import CorrelationService


@pytest.fixture(scope="function")
def correlation_test_data(db_session: Session):
    """
    Creates controlled test safety reports across various factor combinations and equipment.
    """
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        dataset_name="Correlation Test Dataset",
        original_filename="correlation_test.xlsx",
        sheet_name="Correlation_Test",
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

    # 1. Single-factor report (PPE only)
    rep_1 = SafetyReport(
        id="rep-single-factor-01",
        dataset_id=dataset_id,
        original_id="R-001",
        raw_data={"desc": "Worker observed without safety goggles in workshop"},
        refinery_unit="Workshop Area",
        equipment="Grinding-Machine-01",
        department="Fabrication",
        work_type="Hot Work",
        description="Worker observed without safety goggles during grinding",
        ppe_issue=True,
        supervisor_factor=False,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 1, 10, 10, 0, 0)
    )

    # 2. Two-factor report (PPE + Supervisor Negligence)
    rep_2 = SafetyReport(
        id="rep-two-factor-02",
        dataset_id=dataset_id,
        original_id="R-002",
        raw_data={"desc": "No safety harness used and supervisor absent during vessel entry"},
        refinery_unit="CDU-1",
        equipment="Column-C-101",
        department="Operations",
        work_type="Vessel Entry",
        description="No safety harness used and supervisor absent during vessel entry",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Medium",
        action_status="In Progress",
        report_date=datetime(2026, 1, 12, 11, 0, 0)
    )

    # 3. Three-factor report (PPE + Supervisor + Maintenance)
    rep_3 = SafetyReport(
        id="rep-three-factor-03",
        dataset_id=dataset_id,
        original_id="R-003",
        raw_data={"desc": "Defective safety valve, lack of PPE, and uncertified contractor"},
        refinery_unit="CDU-1",
        equipment="Pump-P-201A",
        department="Maintenance",
        work_type="Pump Overhaul",
        description="Defective safety valve, lack of PPE, and uncertified contractor",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=True,
        previous_similar_reports=0,
        risk_level="High",
        action_status="Open",
        report_date=datetime(2026, 1, 15, 14, 0, 0)
    )

    # 4. Four-factor report (PPE + Supervisor + Maintenance + Repeated Issue)
    rep_4 = SafetyReport(
        id="rep-four-factor-04",
        dataset_id=dataset_id,
        original_id="R-004",
        raw_data={"desc": "Critical seal leak on booster pump, previous 3 notifications unaddressed"},
        refinery_unit="CDU-1",
        equipment="Pump-P-201A",
        department="Maintenance",
        work_type="Rotating Equipment Repair",
        description="Critical seal leak on booster pump, previous 3 notifications unaddressed, no supervisor on site, missing face shield",
        ppe_issue=True,
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=True,
        previous_similar_reports=3,
        risk_level="Critical",
        action_status="Overdue",
        report_date=datetime(2026, 1, 20, 9, 30, 0)
    )

    # 5. Same-equipment report (Maintenance issue on Pump-P-201A)
    rep_5 = SafetyReport(
        id="rep-same-equip-05",
        dataset_id=dataset_id,
        original_id="R-005",
        raw_data={"desc": "Severe vibration and oil weeping on Pump-P-201A"},
        refinery_unit="CDU-1",
        equipment="Pump-P-201A",
        department="Operations",
        work_type="Routine Inspection",
        description="Severe vibration and oil weeping on Pump-P-201A",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=True,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Medium",
        action_status="Open",
        report_date=datetime(2026, 1, 22, 16, 0, 0)
    )

    # 6. Isolated report (no shared equipment, unique unit, no correlations)
    rep_isolated = SafetyReport(
        id="rep-isolated-06",
        dataset_id=dataset_id,
        original_id="R-006",
        raw_data={"desc": "Office lighting switch loose in admin building"},
        refinery_unit="Admin Building",
        equipment="Switch-SB-99",
        department="Administration",
        work_type="Facility Maintenance",
        description="Office lighting switch loose in admin building corridor",
        ppe_issue=False,
        supervisor_factor=False,
        maintenance_factor=False,
        repeated_issue=False,
        high_potential=False,
        previous_similar_reports=0,
        risk_level="Low",
        action_status="Closed",
        report_date=datetime(2026, 1, 5, 8, 0, 0)
    )

    db_session.add_all([rep_1, rep_2, rep_3, rep_4, rep_5, rep_isolated])
    db_session.commit()

    return {
        "dataset_id": dataset_id,
        "rep_1": rep_1,
        "rep_2": rep_2,
        "rep_3": rep_3,
        "rep_4": rep_4,
        "rep_5": rep_5,
        "rep_isolated": rep_isolated
    }


class TestCorrelationEngine:

    def test_01_single_factor_report(self, db_session: Session, correlation_test_data):
        """Test 1: Single-factor report has exactly 1 factor and no erroneous multi-factor convergence."""
        rep_1 = correlation_test_data["rep_1"]
        factors = CorrelationEngine.extract_factors(rep_1)
        assert len(factors) == 1
        assert "PPE_NonCompliance" in factors

        res = CorrelationService.correlate_single_report(db_session, rep_1.id)
        assert res is not None
        assert res.single_report_factors == ["PPE_NonCompliance"]

    def test_02_two_factor_report(self, db_session: Session, correlation_test_data):
        """Test 2: Two-factor report detects single-report multi-factor convergence."""
        rep_2 = correlation_test_data["rep_2"]
        factors = CorrelationEngine.extract_factors(rep_2)
        # Factors include PPE_NonCompliance, Supervisor_Negligence, Unresolved_Action (action_status="In Progress")
        assert "PPE_NonCompliance" in factors
        assert "Supervisor_Negligence" in factors
        assert len(factors) >= 2

        res = CorrelationService.correlate_single_report(db_session, rep_2.id)
        assert res is not None
        assert res.has_correlations is True
        assert "Single-report multi-factor convergence" in res.evidence_statement

    def test_03_three_factor_report(self, db_session: Session, correlation_test_data):
        """Test 3: Three-factor report detects 3 distinct barrier failures and elevated compound risk."""
        rep_3 = correlation_test_data["rep_3"]
        factors = CorrelationEngine.extract_factors(rep_3)
        assert "PPE_NonCompliance" in factors
        assert "Supervisor_Negligence" in factors
        assert "Maintenance_Delay_or_Issue" in factors
        assert len(factors) >= 3

        res = CorrelationService.correlate_single_report(db_session, rep_3.id)
        assert res is not None
        assert res.compound_risk_score > 40.0

    def test_04_four_factor_report(self, db_session: Session, correlation_test_data):
        """Test 4: Four-factor report detects 4 barrier failures and highest danger ranking."""
        rep_4 = correlation_test_data["rep_4"]
        factors = CorrelationEngine.extract_factors(rep_4)
        assert "PPE_NonCompliance" in factors
        assert "Supervisor_Negligence" in factors
        assert "Maintenance_Delay_or_Issue" in factors
        assert "Repeated_Issue_Ignored" in factors
        assert "High_Potential_Near_Miss" in factors
        assert "Previous_Similar_Reports" in factors

        res = CorrelationService.correlate_single_report(db_session, rep_4.id)
        assert res is not None
        assert res.compound_risk_score >= 70.0

    def test_05_same_equipment_reports(self, db_session: Session, correlation_test_data):
        """Test 5: Reports referencing the same equipment are linked with structured evidence."""
        rep_3 = correlation_test_data["rep_3"]
        rep_5 = correlation_test_data["rep_5"]

        rel = CorrelationEngine.evaluate_relationship(rep_3, rep_5)
        assert rel is not None
        assert rel["relationship_type"] in ["SAME_EQUIPMENT", "MULTI_FACTOR_CONVERGENCE"]
        assert rel["evidence"]["matched_fields"] == ["equipment", "refinery_unit"]
        assert rel["evidence"]["matched_values"]["equipment"] == "Pump-P-201A"
        assert rel["correlation_score"] >= 0.40
        assert "Pump-P-201A" in rel["evidence"]["notes"]

    def test_06_recurring_reports(self, db_session: Session, correlation_test_data):
        """Test 6: Repeated reports on equipment are correctly flagged with historical recurrence."""
        rep_4 = correlation_test_data["rep_4"]
        rep_5 = correlation_test_data["rep_5"]

        rel = CorrelationEngine.evaluate_relationship(rep_4, rep_5)
        assert rel is not None
        assert rel["evidence"]["unresolved_actions"] is True
        assert len(rel["convergence_factors"]) >= 2

    def test_07_cross_report_convergence(self, db_session: Session, correlation_test_data):
        """Test 7: Cross-report convergence identifies multiple reports converging on same physical exposure without merging."""
        rep_3 = correlation_test_data["rep_3"]
        rep_4 = correlation_test_data["rep_4"]
        rep_5 = correlation_test_data["rep_5"]

        # Run correlation service
        res_3 = CorrelationService.correlate_single_report(db_session, rep_3.id)
        assert res_3 is not None
        assert res_3.total_correlations >= 1
        assert "Pump-P-201A" in res_3.evidence_statement
        # Original reports must remain separate in database
        assert db_session.query(SafetyReport).count() == 6

    def test_08_no_match_case(self, db_session: Session, correlation_test_data):
        """Test 8: Isolated report returns 'Insufficient evidence for reliable correlation.'."""
        rep_isolated = correlation_test_data["rep_isolated"]
        res = CorrelationService.correlate_single_report(db_session, rep_isolated.id)
        assert res is not None
        assert res.has_correlations is False
        assert res.total_correlations == 0
        assert res.evidence_statement == "Insufficient evidence for reliable correlation."

    def test_09_duplicate_records_and_idempotency(self, db_session: Session, correlation_test_data):
        """Test 9: Batch correlation computation is idempotent and does not create duplicate pairs."""
        dataset_id = correlation_test_data["dataset_id"]

        count_1 = CorrelationService.batch_compute_correlations(db_session, dataset_id)
        count_2 = CorrelationService.batch_compute_correlations(db_session, dataset_id)

        # Second run should insert 0 duplicates
        assert count_2 == 0

        # Verify no self correlations
        self_corrs = db_session.query(SafetyCorrelation).filter(
            SafetyCorrelation.source_report_id == SafetyCorrelation.related_report_id
        ).count()
        assert self_corrs == 0

    def test_10_api_endpoints_and_regression(self, client: TestClient, db_session: Session, correlation_test_data):
        """Test 10: Verify all FastAPI correlation endpoints."""
        dataset_id = correlation_test_data["dataset_id"]
        CorrelationService.batch_compute_correlations(db_session, dataset_id)

        rep_4 = correlation_test_data["rep_4"]

        # 1. GET /api/correlations/report/{report_id}
        res_rep = client.get(f"/api/correlations/report/{rep_4.id}")
        assert res_rep.status_code == 200
        data_rep = res_rep.json()
        assert data_rep["has_correlations"] is True
        assert len(data_rep["single_report_factors"]) >= 4

        # 2. GET /api/correlations/unit/{unit_id}
        res_unit = client.get("/api/correlations/unit/CDU-1")
        assert res_unit.status_code == 200
        data_unit = res_unit.json()
        assert data_unit["total_correlated_reports"] >= 4
        assert len(data_unit["top_convergent_equipment"]) > 0

        # 3. GET /api/correlations/high-risk
        res_high = client.get("/api/correlations/high-risk")
        assert res_high.status_code == 200
        data_high = res_high.json()
        assert "total_high_risk_correlations" in data_high

        # 4. GET /api/correlations/recurring
        res_rec = client.get("/api/correlations/recurring")
        assert res_rec.status_code == 200
        data_rec = res_rec.json()
        assert "total_recurring_correlations" in data_rec

        # 5. GET /api/correlations/multi-factor
        res_multi = client.get("/api/correlations/multi-factor")
        assert res_multi.status_code == 200
        data_multi = res_multi.json()
        assert data_multi["total_convergence_clusters"] > 0
        assert len(data_multi["clusters"]) > 0

        # 6. GET /api/correlations/summary
        res_sum = client.get("/api/correlations/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert "factor_co_occurrence_matrix" in data_sum
        assert "dataset_provenance" in data_sum

        # 7. 404 on non-existent report
        res_404 = client.get("/api/correlations/report/non-existent-id")
        assert res_404.status_code == 404
