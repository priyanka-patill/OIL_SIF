import os
import sys
import json

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.session import SessionLocal, init_db
from app.services.sif_service import SIFService
from app.models.safety_report import SafetyReport
from sqlalchemy import select


def run_demonstration():
    init_db()
    db = SessionLocal()
    try:
        print("[*] Running Batch AI/NLP Analysis on all database reports...")
        batch_res = SIFService.batch_analyze_dataset(db)
        print(f"[*] Batch Status: {batch_res['status']}, Total Analyzed: {batch_res['analyzed_count']}")
        print(f"[*] SIF Precursors Flagged: {batch_res['sif_precursor_count']}, High/Critical Risk: {batch_res['high_risk_count']}")

        print("\n[*] Fetching Executive SIF Summary:")
        summary = SIFService.get_sif_summary(db)
        print(json.dumps(summary, indent=2))

        # Select representative reports
        reports = list(db.scalars(select(SafetyReport).order_by(SafetyReport.original_id)).all())
        if not reports:
            print("[ERROR] No safety reports found in database.")
            return

        demo_ids = ["01_P-001", "01_P-050", "01_P-002", "01_P-025"]
        selected_reports = [r for r in reports if r.original_id in demo_ids]
        if not selected_reports:
            selected_reports = reports[:3]

        print("\n" + "=" * 80)
        print("  PART 2 DEMONSTRATION ON ACTUAL PPE DATABASE RECORDS")
        print("=" * 80)

        for rep in selected_reports:
            analysis = SIFService.get_analysis_by_report_id(db, rep.id)
            print(f"\n>>> RECORD: {rep.original_id} <<<")
            print("1. ORIGINAL REPORT:")
            print(f"   - ID: {rep.original_id}")
            print(f"   - Date: {rep.report_date}")
            print(f"   - Unit: {rep.refinery_unit} | Equipment: {rep.equipment}")
            print(f"   - Work Type: {rep.work_type} | Department: {rep.department}")
            print(f"   - Description: \"{rep.description}\"")
            print(f"   - Recorded Risk: {rep.risk_level} | Cause: {rep.immediate_cause} | Consequence: {rep.potential_consequence}")
            print(f"   - Action Status: {rep.action_status} | Prior Reports: {rep.previous_similar_reports}")
            
            print("\n2. NLP EXTRACTION:")
            print(f"   - Extracted PPE Items: {analysis.extracted_ppe_items}")
            print(f"   - Violation Modality: {analysis.extracted_ppe_issue_type}")
            print(f"   - Hazard Identified: {analysis.hazard_identified}")
            print(f"   - Exposure Target: {analysis.exposure_target}")
            
            print("\n3. SIF PRECURSOR & RISK ASSESSMENT:")
            print(f"   - Recorded Risk: {analysis.recorded_risk_level}")
            print(f"   - AI Predicted Risk: {analysis.ai_risk_level}")
            print(f"   - SIF Precursor Potential: {analysis.sif_precursor}")
            print(f"   - SIF Category: {analysis.sif_category}")
            print(f"   - AI Confidence Score: {analysis.confidence_score * 100:.1f}%")
            print(f"   - Is Recurring Hotspot: {analysis.is_recurring} (Score: {analysis.recurrence_score})")
            
            print("\n4. EXPLAINABLE AI REASONING:")
            for r in analysis.reasoning:
                print(f"   * {r}")
                
            print("\n5. PREVENTIVE & IMMEDIATE ACTIONS:")
            print(f"   - Immediate Action Recommendation:\n     {analysis.immediate_action_recommendation}")
            print(f"   - Preventive Action Recommendation:\n     {analysis.preventive_action_recommendation}")
            
            print("\n6. 6-STAGE RISK-ESCALATION SCENARIO:")
            sc = analysis.escalation_scenario
            print(f"   [1] Current Condition:      {sc['current_condition']}")
            print(f"   [2] Continued Exposure:     {sc['continued_exposure']}")
            print(f"   [3] Loss of Control:        {sc['loss_of_control']}")
            print(f"   [4] Incident Event:         {sc['incident_event']}")
            print(f"   [5] Serious Consequence:    {sc['serious_consequence']}")
            print(f"   [6] Potential SIF Outcome:  {sc['potential_fatal_consequence']}")
            print("-" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_demonstration()
