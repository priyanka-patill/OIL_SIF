# OIL SIF Intelligence Platform

An enterprise AI-powered Safety Intelligence & SIF (Serious Injury & Fatality) Precursor Analysis Platform for oil refineries and heavy industrial facilities.

## Features

- **SIF Precursor Analytics Engine:** Automatic detection and classification of SIF precursor risks from safety reports.
- **Barrier Degradation Index (BDI):** Real-time monitoring and scoring of safety barrier integrity across refinery units.
- **AI Preventive Intelligence & SLA Escalations:** Auto-escalation, containment workflows, and governance tracking for high-risk observations.
- **Export & Reporting System:** Executive-level PDF, RFC-4180 CSV, and multi-sheet formatted Excel report generation.
- **Modern Dashboard:** React 18 + Vite frontend with interactive visualizations, risk matrix convergence cards, and real-time analytics.

## Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy, SQLite, Pandas, ReportLab, OpenPyXL, Pytest
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Recharts

## Project Structure

```
antigravity-project/
├── backend/            # FastAPI backend application, services, and tests
│   ├── app/            # Core logic, API routes, models, schemas, and AI engines
│   ├── tests/          # Pytest suite (130+ unit & integration tests)
│   └── run.py          # Backend entry point
├── frontend/           # React + Vite frontend application
│   ├── src/            # Components, views, services, and styles
│   └── package.json
└── docs/               # System architecture, API docs, and data dictionary
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```
Backend server runs at: `http://127.0.0.1:8000` (Swagger docs at `/docs`)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Frontend app runs at: `http://localhost:3000`

### Running Tests

```bash
cd backend
pytest tests
```
