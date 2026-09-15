import pandas as pd
from datetime import datetime
from app.ingestion.schema_detector import SchemaDetector
from app.ingestion.semantic_mapper import SemanticMapper


def test_schema_type_detection():
    data = {
        "Incident_ID": ["INC-001", "INC-002", "INC-003"],
        "Observation_Date": ["2025-10-15", "2025-10-16", "2025-10-17"],
        "Is_Urgent": [True, False, True],
        "Count_Prior": [0, 2, 5],
        "Severity_Score": [1.5, 2.7, 3.2],
        "Full_Description": [
            "A lengthy narrative detailing the occurrence of a hazardous event at the sulfur recovery unit during nighttime operations.",
            "Another extended explanation describing worker behavior and protective gear non-compliance during valve maintenance.",
            "Detailed investigation summary regarding equipment malfunction and emergency shutdown protocol execution."
        ]
    }
    df = pd.DataFrame(data)
    meta = SchemaDetector.analyze_schema(df)

    meta_dict = {m["original_name"]: m for m in meta}

    assert meta_dict["Incident_ID"]["detected_data_type"] == "STRING"
    assert meta_dict["Observation_Date"]["detected_data_type"] == "DATETIME"
    assert meta_dict["Is_Urgent"]["detected_data_type"] == "BOOLEAN"
    assert meta_dict["Count_Prior"]["detected_data_type"] == "INTEGER"
    assert meta_dict["Severity_Score"]["detected_data_type"] == "FLOAT"
    assert meta_dict["Full_Description"]["detected_data_type"] == "TEXT"


def test_constant_field_detection():
    data = {
        "PPE_Violation": [True, True, True, True],
        "Supervisor_Fault": [False, False, False, False],
        "Plant_Code": ["REF-1", "REF-1", "REF-1", "REF-1"],
        "Variable_Field": ["A", "B", "C", "D"],
        "All_Nulls": [None, None, None, None]
    }
    df = pd.DataFrame(data)
    meta = SchemaDetector.analyze_schema(df)
    meta_dict = {m["original_name"]: m for m in meta}

    assert meta_dict["PPE_Violation"]["is_constant"] is True
    assert meta_dict["PPE_Violation"]["constant_value"] == "True"
    assert meta_dict["PPE_Violation"]["unique_count"] == 1

    assert meta_dict["Supervisor_Fault"]["is_constant"] is True
    assert meta_dict["Supervisor_Fault"]["constant_value"] == "False"
    assert meta_dict["Supervisor_Fault"]["unique_count"] == 1

    assert meta_dict["Plant_Code"]["is_constant"] is True
    assert meta_dict["Plant_Code"]["constant_value"] == "REF-1"

    assert meta_dict["Variable_Field"]["is_constant"] is False
    assert meta_dict["Variable_Field"]["unique_count"] == 4

    assert meta_dict["All_Nulls"]["is_constant"] is True


def test_semantic_mapping():
    assert SemanticMapper.match_column("Near_Miss_ID", "STRING")[0] == "original_id"
    assert SemanticMapper.match_column("Observation_Date", "DATETIME")[0] == "report_date"
    assert SemanticMapper.match_column("Refinery_Unit", "STRING")[0] == "refinery_unit"
    assert SemanticMapper.match_column("Equipment_ID", "STRING")[0] == "equipment"
    assert SemanticMapper.match_column("Near_Miss_Description", "TEXT")[0] == "description"
    assert SemanticMapper.match_column("PPE_NonCompliance", "BOOLEAN")[0] == "ppe_issue"
    assert SemanticMapper.match_column("Supervisor_Negligence", "BOOLEAN")[0] == "supervisor_factor"
    assert SemanticMapper.match_column("Maintenance_Delay_or_Issue", "BOOLEAN")[0] == "maintenance_factor"
    assert SemanticMapper.match_column("Repeated_Issue_Ignored", "BOOLEAN")[0] == "repeated_issue"
    assert SemanticMapper.match_column("Previous_Similar_Reports", "INTEGER")[0] == "previous_similar_reports"
    assert SemanticMapper.match_column("Immediate_Cause", "STRING")[0] == "immediate_cause"
    assert SemanticMapper.match_column("Potential_Consequence", "STRING")[0] == "potential_consequence"
    assert SemanticMapper.match_column("Risk_Level", "STRING")[0] == "risk_level"
    assert SemanticMapper.match_column("Corrective_Action", "TEXT")[0] == "corrective_action"
    assert SemanticMapper.match_column("Action_Status", "STRING")[0] == "action_status"
    assert SemanticMapper.match_column("High_Potential_Near_Miss", "BOOLEAN")[0] == "high_potential"
