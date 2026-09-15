import os
from app.services.dataset_service import DatasetService
from app.services.sif_service import SIFService
from app.services.ai.nlp_engine import NLPEngine
from app.services.ai.sif_engine import SIFPrecursorEngine
from app.services.ai.preventive_engine import PreventiveIntelligenceEngine
from app.services.ai.recurrence_engine import RecurrenceEngine


def test_nlp_concept_and_hazard_extraction():
    text = "Welder worked near high-pressure line without fire-resistant clothing and face shield during hot work."
    ppe_items = NLPEngine.extract_ppe_items(text)
    assert "fire-resistant clothing" in ppe_items
    assert "face shield" in ppe_items

    violation = NLPEngine.detect_violation_modality(text)
    assert violation == "MISSING_PPE"

    hazard, exposure = NLPEngine.identify_hazard_and_exposure(
        combined_text=text,
        department="Mechanical",
        work_type="Hot Work",
        refinery_unit="Hydrogen Unit",
        ppe_items=ppe_items
    )
    assert "Thermal" in hazard or "Fire" in hazard or "Hydrocarbon" in hazard
    assert "Mechanical" in exposure
    assert "Hot Work" in exposure


def test_sif_precursor_classification_and_risk_separation():
    # Test High energy hazard with severe potential consequence
    sif_status, category, ai_risk, conf, reasons, org_factors = SIFPrecursorEngine.evaluate_sif(
        hazard_identified="Thermal / Flash Fire & Hydrocarbon Release",
        ppe_items=["fire-resistant clothing"],
        violation_type="MISSING_PPE",
        recorded_risk="Low",  # Recorded was Low, but AI detects SIF Precursor
        potential_consequence="Fire",
        immediate_cause="Unsafe condition",
        work_type="Hot Work",
        refinery_unit="Hydrogen Unit",
        previous_similar_reports=2,
        action_status="Overdue"
    )

    assert sif_status == "YES"
    assert category == "Thermal / Flash Fire Hazard"
    assert ai_risk in ["HIGH", "CRITICAL"]
    assert conf >= 0.85
    assert len(reasons) >= 3
    # Verify recorded vs AI risk separation note
    assert any("Risk Upgrade Note" in r for r in reasons)
    assert len(org_factors) >= 2


def test_preventive_actions_and_escalation_scenario():
    imm_action = PreventiveIntelligenceEngine.generate_immediate_action(
        observed_problem="Worker entered process area without safety helmet",
        ppe_items=["safety helmet"],
        violation_type="MISSING_PPE",
        work_type="Routine Operation",
        department="Contractor",
        sif_precursor="YES"
    )
    assert "pause" in imm_action.lower() or "don" in imm_action.lower()
    assert "safety helmet" in imm_action.lower()

    prev_action = PreventiveIntelligenceEngine.generate_preventive_action(
        observed_problem="Worker entered process area without safety helmet",
        ppe_items=["safety helmet"],
        immediate_cause="Equipment degradation",
        potential_consequence="Lost-time injury",
        work_type="Preventive Maintenance",
        action_status="Open",
        is_recurring=True,
        previous_similar_reports=1
    )
    assert "audit" in prev_action.lower() or "toolbox" in prev_action.lower() or "ppe" in prev_action.lower()

    scenario = PreventiveIntelligenceEngine.build_escalation_scenario(
        observed_problem="Worker entered process area without safety helmet",
        hazard_identified="Overhead Impact / Mechanical Hazard",
        ppe_items=["safety helmet"],
        work_type="Preventive Maintenance",
        refinery_unit="Hydrogen Unit",
        potential_consequence="Lost-time injury",
        sif_precursor="YES"
    )
    assert "current_condition" in scenario
    assert "continued_exposure" in scenario
    assert "loss_of_control" in scenario
    assert "incident_event" in scenario
    assert "serious_consequence" in scenario
    assert "potential_fatal_consequence" in scenario
    assert "Hydrogen Unit" in scenario["current_condition"]


def test_sif_api_and_batch_analysis_flow(client, db_session, ppe_excel_path):
    # 1. Ingest PPE Dataset
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    dataset = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=file_bytes,
        filename=os.path.basename(ppe_excel_path),
        file_type="xlsx",
        dataset_name="AI Test Dataset"
    )

    # 2. Trigger Batch AI Analysis
    res_batch = client.post(f"/api/reports/analyze-all?dataset_id={dataset.id}")
    assert res_batch.status_code == 200
    batch_data = res_batch.json()
    assert batch_data["analyzed_count"] == 75
    assert batch_data["sif_precursor_count"] > 0

    # 3. Retrieve Single Report Analysis
    reports_res = client.get("/api/reports?page=1&page_size=1")
    report_id = reports_res.json()["items"][0]["id"]

    res_single = client.get(f"/api/reports/{report_id}/analysis")
    assert res_single.status_code == 200
    analysis = res_single.json()
    assert analysis["report_id"] == report_id
    assert analysis["sif_precursor"] in ["YES", "NO", "UNCERTAIN"]
    assert analysis["ai_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "escalation_scenario" in analysis
    assert len(analysis["reasoning"]) > 0

    # 4. SIF Executive Summary API
    res_summary = client.get(f"/api/sif/summary?dataset_id={dataset.id}")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_analyzed"] == 75
    assert summary["sif_precursors_detected"] > 0
    assert summary["sif_precursor_rate_percentage"] > 0
    assert len(summary["top_recurring_units"]) > 0

    # 5. SIF High Risk API
    res_high = client.get(f"/api/sif/high-risk?dataset_id={dataset.id}")
    assert res_high.status_code == 200
    high_items = res_high.json()
    assert high_items["total"] > 0

    # 6. SIF Recurring Issues API
    res_rec = client.get(f"/api/sif/recurring?dataset_id={dataset.id}")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["total_recurring_clusters"] > 0
    assert len(rec_data["by_refinery_unit"]) > 0

    # 7. AI Human Feedback Loop
    feedback_payload = {
        "report_id": report_id,
        "reviewer_name": "Chief Safety Inspector",
        "agrees_with_ai": False,
        "human_risk_level": "Critical",
        "human_sif_precursor": "YES",
        "feedback_reason": "High pressure hydrogen line operating adjacent to observed worker position."
    }
    res_fb_post = client.post("/api/ai-feedback", json=feedback_payload)
    assert res_fb_post.status_code == 201
    fb_data = res_fb_post.json()
    assert fb_data["reviewer_name"] == "Chief Safety Inspector"
    assert fb_data["human_risk_level"] == "Critical"

    # 8. Retrieve Feedback for Report
    res_fb_get = client.get(f"/api/ai-feedback/{report_id}")
    assert res_fb_get.status_code == 200
    fb_list = res_fb_get.json()
    assert len(fb_list) == 1
    assert fb_list[0]["agrees_with_ai"] is False
