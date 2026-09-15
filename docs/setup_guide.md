# OIL SIF Intelligence Platform - Setup & Execution Guide

## 1. Prerequisites

- Python 3.10+ (Current: Python 3.14)
- Dependencies installed via `pip install -r backend/requirements.txt`

---

## 2. Environment Setup

Create `.env` inside `backend/` (or use default configuration):
```bash
cp backend/.env.example backend/.env
```

---

## 3. Database & Dataset Ingestion

To ingest the initial source of truth dataset (`PPE_Noncomplaince.xlsx`):

```bash
python backend/import_ppe.py
```

This will:
1. Initialize the central SQLite/PostgreSQL database tables.
2. Ingest all 75 records and 18 columns.
3. Automatically perform dynamic schema detection and constant-field detection.
4. Normalize records into canonical safety reports while preserving 100% of raw source data.
5. Generate the automated data quality scorecard.

---

## 4. Running the Industrial Control Room & Backend Server

Start the full platform with a single command:

```bash
python backend/run.py
```

The platform is immediately available at:
- **Industrial Safety Control Room UI**: `http://localhost:8000/` (or `http://localhost:8000/dashboard`)
- **API Base**: `http://localhost:8000/api`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 5. Standalone React / Vite Frontend (Optional Developer Mode)

The complete modular React 18 + TypeScript + Vite + Tailwind CSS source is located in `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

---

## 6. Running Automated Tests

Run the full automated test suite using pytest (21 tests, 100% pass rate):

```bash
python -m pytest backend/tests -v
```
