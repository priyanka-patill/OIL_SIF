# OIL SIF Intelligence Platform - Data Dictionary

## 1. PPE Dataset (`PPE_Noncomplaince.xlsx`) Specifications

Source Records: 75
Source Columns: 18

| Column Name | Inferred Type | Semantic Type | Canonical Mapping | Constant Field? |
|-------------|---------------|---------------|-------------------|-----------------|
| `Near_Miss_ID` | STRING | ID | `original_id` | No (75 unique) |
| `Date` | DATETIME | DATE | `report_date` | No (73 unique) |
| `Refinery_Unit` | STRING | LOCATION | `refinery_unit` | No (10 unique) |
| `Equipment_ID` | STRING | EQUIPMENT | `equipment` | No (14 unique) |
| `Work_Type` | STRING | WORK_TYPE | `work_type` | No (8 unique) |
| `Department` | STRING | DEPARTMENT | `department` | No (6 unique) |
| `Near_Miss_Description` | TEXT | NARRATIVE | `description` | No (10 unique) |
| `PPE_NonCompliance` | BOOLEAN | FLAG | `ppe_issue` | **YES (All True)** |
| `Supervisor_Negligence` | BOOLEAN | FLAG | `supervisor_factor` | **YES (All False)** |
| `Maintenance_Delay_or_Issue` | BOOLEAN | FLAG | `maintenance_factor` | **YES (All False)** |
| `Repeated_Issue_Ignored` | BOOLEAN | FLAG | `repeated_issue` | **YES (All False)** |
| `Previous_Similar_Reports` | INTEGER | NUMERIC | `previous_similar_reports` | No (3 unique: 0, 1, 2) |
| `Immediate_Cause` | STRING | CAUSE | `immediate_cause` | No (7 unique) |
| `Potential_Consequence` | STRING | CONSEQUENCE | `potential_consequence` | No (5 unique) |
| `Risk_Level` | STRING | RISK_LEVEL | `risk_level` | No (3 unique: Low, Medium, High) |
| `Corrective_Action` | TEXT | ACTION | `corrective_action` | No (7 unique) |
| `Action_Status` | STRING | STATUS | `action_status` | No (4 unique: Open, In Progress, Closed, Overdue) |
| `High_Potential_Near_Miss` | BOOLEAN | FLAG | `high_potential` | **YES (All False)** |

---

## 2. Canonical Safety Report Model Fields

All canonical fields are optional/nullable to guarantee compatibility across diverse present and future safety datasets:

- `report_id`: Unique platform identifier (UUID string)
- `dataset_id`: Parent dataset identifier (UUID string FK)
- `original_id`: Source record identifier (e.g., `01_P-001`)
- `raw_data`: 100% complete source row representation stored as JSON/dict
- `report_date`: Incident / observation timestamp
- `location`: Facility or site location
- `refinery_unit`: Specific refinery unit (e.g. `Hydrogen Unit`, `Sulfur Unit`)
- `equipment`: Machine / equipment tag (e.g. `P-305`, `E-207`)
- `work_type`: Work category (e.g. `Preventive Maintenance`, `Routine Operation`)
- `department`: Department or contractor (e.g. `HSE`, `Contractor`, `Maintenance`)
- `report_type`: Event classification (e.g. `Near Miss`, `Unsafe Act`)
- `description`: Text narrative of the event
- `hazard`: Specific hazard identified
- `unsafe_act`: Observed unsafe behavior
- `unsafe_condition`: Physical unsafe condition
- `ppe_issue`: Boolean flag for PPE non-compliance
- `immediate_cause`: Direct cause identified
- `potential_consequence`: Worst-case potential outcome
- `risk_level`: Severity risk rating (`Low`, `Medium`, `High`)
- `sif_precursor`: Serious Injury & Fatality precursor flag
- `high_potential`: High potential event flag
- `previous_similar_reports`: Count of previous similar events
- `repeated_issue`: Flag for repeated/ignored issue
- `supervisor_factor`: Flag for supervisor negligence
- `maintenance_factor`: Flag for maintenance delay/issue
- `corrective_action`: Assigned remediation action
- `action_status`: Status of action (`Open`, `In Progress`, `Closed`, `Overdue`)
- `source_dataset`: Name of originating dataset
- `created_at`: Ingestion timestamp
