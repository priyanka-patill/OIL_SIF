# OIL SIF Intelligence Platform - API Reference (Parts 1 & 2)

Base URL: `http://localhost:8000/api`
Interactive Swagger Docs: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

---

## 1. System Health

### `GET /api/health`
Checks backend and database connectivity.

---

## 2. Dataset Management

### `GET /api/datasets`
Lists all active datasets with pagination.

### `POST /api/datasets/upload`
Uploads and ingests a dataset (`.xlsx`, `.csv`, `.json`).

### `GET /api/datasets/{dataset_id}`
Retrieves detailed dataset metadata including all registered columns.

### `GET /api/datasets/{dataset_id}/schema`
Retrieves detected schema, data types, constant fields, and canonical mappings.

### `DELETE /api/datasets/{dataset_id}`
Deletes dataset and associated records, columns, and quality metrics.

---

## 3. Safety Reports

### `GET /api/reports`
Queries normalized safety reports with filtering, search, sorting, and pagination.

### `GET /api/reports/count`
Retrieves report counts grouped by `risk_level`, `department`, `refinery_unit`, `action_status`, and `work_type`.

### `GET /api/reports/{report_id}`
Retrieves a single safety report with both normalized canonical fields AND the complete 100% untouched `raw_data` dictionary.

---

## 4. AI/NLP Engine & SIF Preventive Intelligence (Part 2)

### `POST /api/reports/{report_id}/analyze`
Runs on-demand AI/NLP analysis for a single safety report: extracts PPE items, detects energy hazards, calculates SIF precursor potential, assigns AI predicted risk, generates explainable reasoning, formulates immediate and preventive actions, and models the 6-stage risk-escalation scenario.

### `POST /api/reports/analyze-all`
Runs batch AI analysis across all reports in a dataset.

### `GET /api/reports/{report_id}/analysis`
Retrieves full AI analysis, SIF assessment, and escalation scenario for a report.

### `GET /api/sif/summary`
Retrieves executive SIF summary:
- Total analyzed count
- SIF precursors detected & percentage rate
- Distribution by SIF status (`YES`, `NO`, `UNCERTAIN`)
- Distribution by AI risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- Distribution by recorded risk level & count of risk upgrades
- SIF categories breakdown
- Top recurring refinery units & equipment

### `GET /api/sif/high-risk`
Retrieves paginated list of reports classified as SIF Precursors (`YES`) or assessed at `HIGH`/`CRITICAL` AI risk.

### `GET /api/sif/recurring`
Discovers recurring safety clusters grouped by Equipment, Process Units, Departments, and Work Types.

### `POST /api/ai-feedback`
Submits human safety officer review or override (`agrees_with_ai`, `human_risk_level`, `human_sif_precursor`, `feedback_reason`). Preserves original AI assessment while attaching expert feedback.

### `GET /api/ai-feedback/{report_id}`
Retrieves all human safety reviews submitted for a report.

---

## 5. Data Quality

### `GET /api/data-quality/{dataset_id}`
Retrieves data quality scorecard, completeness, duplicate IDs, invalid dates, and constant-field breakdown.

---

## 6. Dynamic Metadata

### `GET /api/metadata/fields`
Returns dynamically discovered filter fields, distinct value choices, and canonical schema definitions.
