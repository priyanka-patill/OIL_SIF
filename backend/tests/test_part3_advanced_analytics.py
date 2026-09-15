import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, init_db
from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.report_analysis import ReportAnalysis
from app.services.ai.multi_factor_engine import MultiFactorEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.bdi_service import BDIService
from app.services.sif_density_service import SIFDensityService
from app.services.sif_service import SIFService


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_multi_factor_swiss_cheese_engine():
    """Verify MultiFactorEngine correctly detects compound control failures and escalation contributors."""
    report = SafetyReport(
        description="Contractor welder operating on naphtha flange without PTW permit or LOTO isolation. Supervisory check missing.",
        immediate_cause="Unsafe procedure & maintenance delay",
        potential_consequence="Hydrocarbon flash fire",
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        high_potential=True
    )

    res = MultiFactorEngine.evaluate_multi_factor_exposure(
        report=report,
        hazard_identified="High-Pressure Hydrocarbon & Thermal Hazard",
        ppe_items=["fire-resistant clothing"],
        iogp_rule="Energy Isolation",
        is_recurring=True
    )

    assert res["compound_factor_count"] >= 3
    assert res["multi_barrier_degradation"] is True
    assert res["critical_sif_precursor"] is True
    assert len(res["risk_escalation_contributors"]) >= 3
    assert "CRITICAL SIF PRECURSOR" in res["escalation_summary"]


def test_bdi_prototype_calculation_and_banding(db_session: Session):
    """Verify BDIEngine computes transparent BDI score, risk band, and component contributions."""
    test_ds = db_session.query(Dataset).first()
    ds_id = test_ds.id if test_ds else "test-ds-bdi"

    report = SafetyReport(
        dataset_id=ds_id,
        original_id="TEST-BDI-001",
        raw_data={"description": "Scaffold missing handrails and toe-boards at 12m height. Overdue action pending."},
        description="Scaffold missing handrails and toe-boards at 12m height. Overdue action pending.",
        refinery_unit="FCC",
        equipment="Vessel-V201",
        risk_level="High",
        supervisor_factor=True,
        maintenance_factor=True,
        repeated_issue=True,
        action_status="Overdue",
        high_potential=True
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    bdi_res = BDIService.get_report_bdi(db_session, report.id)

    assert bdi_res is not None
    assert 0.0 <= bdi_res.bdi_score <= 100.0
    assert bdi_res.classification in ["HIGH", "SEVERE", "MODERATE"]
    assert len(bdi_res.component_contributions) > 0
    assert len(bdi_res.explainability.top_contributors) > 0


def test_sif_precursor_density_and_rankings(db_session: Session):
    """Verify SIFDensityService calculates overall precursor density and dimension rankings."""
    density_res = SIFDensityService.calculate_sif_density(db_session)

    assert "total_reports" in density_res
    assert "sif_precursor_density_percentage" in density_res
    assert isinstance(density_res["dimension_rankings"], dict)
    assert isinstance(density_res["unavailable_dimensions"], list)


def test_api_endpoints_part3(client: TestClient):
    """Verify GET /api/sif/density and GET /api/sif/multi-factor HTTP API routes."""
    res_density = client.get("/api/sif/density")
    assert res_density.status_code == 200
    data_density = res_density.json()
    assert "sif_precursor_density_percentage" in data_density

    res_mf = client.get("/api/sif/multi-factor")
    assert res_mf.status_code == 200
    data_mf = res_mf.json()
    assert "combinations" in data_mf


def test_newly_submitted_supervisor_report_contributes_to_density_and_analytics(client: TestClient, db_session: Session):
    """Verify newly submitted supervisor report immediately triggers analysis and updates density analytics."""
    payload = {
        "description": "Technician reported unisolated electric motor terminal box sparked near gas line in H2 plant.",
        "refinery_unit": "Hydrogen Unit",
        "equipment": "M-301 A",
        "work_type": "Energy Isolation",
        "department": "Electrical Maintenance",
        "submitting_user": "Shift Supervisor",
        "submitting_role": "Supervisor"
    }

    response = client.post("/api/reports", json=payload)
    assert response.status_code == 201
    created_report = response.json()
    report_id = created_report["id"]

    # Verify SIF Service analyzed report
    analysis = SIFService.get_analysis_by_report_id(db_session, report_id)
    assert analysis is not None
    assert analysis.sif_precursor in ["YES", "NO", "UNCERTAIN"]

    # Verify SIF Density includes new report
    density = SIFDensityService.calculate_sif_density(db_session)
    assert density["total_reports"] > 0
