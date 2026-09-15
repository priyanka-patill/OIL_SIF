import os
import pytest
from app.models.dataset import Dataset
from app.models.safety_report import SafetyReport
from app.services.dataset_service import DatasetService
from app.services.factor_service import FactorService
from app.services.ai.chat_service import ChatService


@pytest.fixture(scope="module")
def indian_refinery_path():
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "datasets", "Indian_Refinery_Near_Miss_Datasets.xlsx"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Indian_Refinery_Near_Miss_Datasets.xlsx"),
        r"c:\Users\sahan\antigravity-project\Indian_Refinery_Near_Miss_Datasets.xlsx",
        r"C:\Users\sahan\Downloads\Indian_Refinery_Near_Miss_Datasets.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    pytest.skip("Indian_Refinery_Near_Miss_Datasets.xlsx not found")


@pytest.fixture(scope="function")
def populated_session(db_session, indian_refinery_path):
    """Ingests the complete workbook into the test transaction."""
    with open(indian_refinery_path, "rb") as f:
        content = f.read()
    datasets = DatasetService.ingest_multi_sheet_workbook(
        db_session, content, os.path.basename(indian_refinery_path)
    )
    return db_session, datasets


class TestIndianRefineryIntegration:

    def test_multi_sheet_workbook_ingestion(self, populated_session):
        """Verify that all 13 sheets from the Indian Refinery workbook are correctly ingested."""
        db_session, datasets = populated_session
        assert len(datasets) == 13, f"Expected 13 datasets, got {len(datasets)}"

        # Verify summary sheet segregation
        summary_ds = [d for d in datasets if d.is_summary_dataset]
        assert len(summary_ds) == 1, "Expected exactly 1 summary sheet"
        assert summary_ds[0].sheet_name == "00_Summary"
        # Verify 0 safety reports imported for summary sheet
        summary_reports = db_session.query(SafetyReport).filter(
            SafetyReport.dataset_id == summary_ds[0].id
        ).count()
        assert summary_reports == 0, "Summary sheet must have 0 safety reports imported"

        # Verify single factor sheets (4 sheets)
        single_factor_ds = [d for d in datasets if d.dataset_type == "single_factor"]
        assert len(single_factor_ds) == 4, f"Expected 4 single factor datasets, got {len(single_factor_ds)}"

        # Verify multi factor sheets (7 sheets: 2-factor, 3-factor, 4-factor)
        multi_factor_ds = [d for d in datasets if d.dataset_type == "multi_factor"]
        assert len(multi_factor_ds) == 7, f"Expected 7 multi factor datasets, got {len(multi_factor_ds)}"

        # Verify high potential sheet
        hipo_ds = [d for d in datasets if d.dataset_type == "high_potential"]
        assert len(hipo_ds) == 1, "Expected 1 high potential dataset"
        assert hipo_ds[0].sheet_name == "12_High_Potential"
        assert hipo_ds[0].row_count == 100

        # Verify total reports imported (950 across operational sheets)
        total_reports = db_session.query(SafetyReport).filter(
            SafetyReport.dataset_id.in_([d.id for d in datasets if not d.is_summary_dataset])
        ).count()
        assert total_reports == 950, f"Expected 950 reports, got {total_reports}"

    def test_factor_compounding_escalation(self, populated_session):
        """Verify that moving from 1-factor to 4-factor tiers exhibits non-linear risk escalation."""
        db_session, _ = populated_session
        comb = FactorService.get_factor_combinations(db_session)

        assert comb.level_1_count == 300
        assert comb.level_2_count == 225
        assert comb.level_3_count == 225
        assert comb.level_4_count == 200

        # Danger scores must be highest for 4-factor combinations
        top_danger = comb.danger_ranked_combinations[0]
        assert top_danger.factor_count == 4
        assert top_danger.danger_level in ["CRITICAL", "HIGH"]
        assert top_danger.danger_score > 50.0

        # Lowest danger item has factor_count == 1
        lowest_danger = comb.danger_ranked_combinations[-1]
        assert lowest_danger.factor_count == 1
        assert lowest_danger.danger_score < top_danger.danger_score

    def test_dataset_comparison(self, populated_session):
        """Verify side-by-side comparative analysis between Single Factor and 4-Factor datasets."""
        db_session, _ = populated_session
        single_ds = db_session.query(Dataset).filter(Dataset.dataset_type == "single_factor", Dataset.row_count > 0).first()
        multi_ds = db_session.query(Dataset).filter(Dataset.factor_count == 4, Dataset.row_count > 0).first()

        assert single_ds is not None and multi_ds is not None

        comp = FactorService.compare_datasets(db_session, single_ds.id, multi_ds.id)
        assert comp.dataset_a["id"] == single_ds.id
        assert comp.dataset_b["id"] == multi_ds.id
        assert len(comp.comparative_insights) >= 2

    def test_high_potential_intelligence(self, populated_session):
        """Verify high potential intelligence returns 100 records and root causes."""
        db_session, _ = populated_session
        hipo = FactorService.get_high_potential_intelligence(db_session)
        assert hipo.total_high_potential_incidents == 100
        assert (hipo.high_risk_count + hipo.critical_risk_count) >= 50
        assert len(hipo.top_immediate_causes) > 0
        assert len(hipo.top_potential_consequences) > 0
        assert len(hipo.key_failure_patterns) >= 2
        assert len(hipo.preventive_imperatives) >= 3

    def test_chatbot_database_grounded_queries(self, populated_session):
        """Verify natural language chatbot handles new multi-factor, hipo, and comparison questions."""
        db_session, _ = populated_session

        # 1. Most dangerous combination
        r1 = ChatService.process_chat_message(db_session, "Which combination of safety factors is most dangerous?")
        assert "4-Factor" in r1["reply"] or "Critical" in r1["reply"] or "danger" in r1["reply"].lower()
        assert r1["category"] in ["COMBINATION_INTEL", "FACTOR_COMBINATIONS"]

        # 2. High-potential near miss
        r2 = ChatService.process_chat_message(db_session, "Show high-potential near-miss reports.")
        assert "100" in r2["reply"] or "high-potential" in r2["reply"].lower()
        assert r2["category"] in ["HIPO_INTEL", "HIGH_POTENTIAL_INTEL", "HIGH_POTENTIAL"]

        # 3. Supervisor negligence
        r3 = ChatService.process_chat_message(db_session, "How many reports involve supervisor negligence?")
        assert "Supervisor Negligence" in r3["reply"]
        assert r3["category"] in ["FACTOR_INTEL", "SAFETY_FACTORS"]

        # 4. Maintenance delay
        r4 = ChatService.process_chat_message(db_session, "How many reports involve maintenance delay?")
        assert "Maintenance Delay" in r4["reply"]
        assert r4["category"] in ["FACTOR_INTEL", "SAFETY_FACTORS"]

        # 5. Repeated issues
        r5 = ChatService.process_chat_message(db_session, "How many reports involve repeated issues?")
        assert "Repeated Issues" in r5["reply"]
        assert r5["category"] in ["FACTOR_INTEL", "SAFETY_FACTORS"]

        # 6. Compare single-factor vs multi-factor
        r6 = ChatService.process_chat_message(db_session, "Compare single-factor vs multi-factor datasets.")
        assert "1-Factor" in r6["reply"] or "Single-Factor" in r6["reply"] or "Multi-Factor" in r6["reply"] or "Dataset" in r6["reply"]
        assert r6["category"] in ["COMPARISON", "DATASET_COMPARISON", "DATASET_SCOPING"]

        # 7. PPE only
        r7 = ChatService.process_chat_message(db_session, "Show reports where only PPE is violated.")
        assert "PPE" in r7["reply"]
        assert r7["category"] in ["FACTOR_INTEL", "SAFETY_FACTORS"]

    def test_factors_and_comparison_api_endpoints(self, client, populated_session):
        """Verify FastAPI routes for factor intelligence and comparison."""
        res_sum = client.get("/api/factors/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert "factors" in data_sum

        res_comb = client.get("/api/factors/combinations")
        assert res_comb.status_code == 200
        data_comb = res_comb.json()
        assert "level_1_count" in data_comb
        assert "danger_ranked_combinations" in data_comb

        res_hipo = client.get("/api/factors/high-potential")
        assert res_hipo.status_code == 200
        data_hipo = res_hipo.json()
        assert data_hipo["total_high_potential_incidents"] == 100
