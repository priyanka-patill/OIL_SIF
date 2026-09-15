# OIL SIF Intelligence Platform - Architecture Documentation (Parts 1 & 2)

## 1. System Overview

The **OIL SIF Intelligence Platform** is an industrial safety intelligence engine designed to detect Serious Injury & Fatality (SIF) precursors in Unsafe Act, Unsafe Condition, and Near-Miss safety reports.

- **Part 1 (Backend & Central Data Foundation)**: Scalable ingestion for XLSX, CSV, and JSON datasets, dynamic schema detection, constant-field detection, dual-layer raw JSON + canonical normalization, automated data quality engine, and dataset registry.
- **Part 2 (AI/NLP Engine + SIF Analysis + Preventive Intelligence)**: Entity extraction, PPE concept recognition, SIF precursor potential classification, AI risk assessment (independent of recorded risk), explainable AI reasoning, 6-stage risk-escalation scenarios, immediate/preventive action generation, recurrence hotspot engine, and human safety officer feedback loops.

---

## 2. Layered Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Client Layer / Consumers                    │
│      (Web Dashboards, Mobile Clients, Automated CLI Tools)     │
└───────────────────────────────┬────────────────────────────────┘
                                │ HTTP / REST API
┌───────────────────────────────▼────────────────────────────────┐
│                      FastAPI Routing Layer                     │
│   /api/health      /api/datasets        /api/reports           │
│   /api/metadata    /api/data-quality    /api/sif/summary       │
│   /api/sif/high-risk /api/sif/recurring /api/ai-feedback       │
└───────────────────────────────┬────────────────────────────────┘
                                │
┌───────────────────────────────▼────────────────────────────────┐
│                         Service Layer                          │
│   DatasetService   │   ReportService   │   QualityService      │
│   AuditService     │   SIFService      │                       │
└───────────────────┬───────────────────────────┬────────────────┘
                    │                           │
┌───────────────────▼───────────┐   ┌───────────▼────────────────┐
│       Ingestion Engine        │   │     AI / NLP & SIF Core    │
│  - FileReader                 │   │  - NLPEngine               │
│  - SchemaDetector             │   │  - SIFPrecursorEngine      │
│  - SemanticMapper             │   │  - PreventiveEngine        │
│  - DataNormalizer             │   │  - RecurrenceEngine        │
└───────────────────┬───────────┘   └───────────┬────────────────┘
                    │                           │
┌───────────────────▼───────────────────────────▼────────────────┐
│                 Data Persistence (SQLAlchemy 2.0)              │
│   models: Dataset, DatasetColumn, SafetyReport,                │
│           DataQualitySummary, AuditLog, ReportAnalysis,        │
│           AIFeedback                                           │
└───────────────────────────────┬────────────────────────────────┘
                                │ SQL (Parameterized)
┌───────────────────────────────▼────────────────────────────────┐
│                     Central Database Engine                    │
│          PostgreSQL (Production) / SQLite (Development)        │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Preventive Intelligence & Escalation Scenario Pipeline

```
[ Raw Report Text & Attributes ]
              │
              ▼
    [ NLP Entity Extraction ] (PPE Items, Modality, Energy Hazards)
              │
              ▼
    [ SIF Precursor Engine ] (YES / NO / UNCERTAIN, SIF Category, Confidence)
              │
              ▼
  [ Independent Risk Assessment ] (Recorded Risk preserved, AI Risk evaluated)
              │
              ▼
  [ 6-Stage Risk-Escalation Scenario ]
    (1) Current Condition
    (2) Continued Exposure
    (3) Loss of Control
    (4) Incident Event
    (5) Serious Consequence
    (6) Potential SIF Outcome
              │
              ▼
  [ Contextual Actions & Human Feedback Loop ]
    - Tailored Immediate Action
    - Tailored Preventive Strategy
    - HSE Officer Review & Override (ai_feedback)
```
