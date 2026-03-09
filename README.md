# SE_ARIES — Internal ARIES Petroleum Economics Platform

An internal clone of Landmark's ARIES® Petroleum Economics & Reserves Software built with modern web technologies.

## Architecture

```
SE_ARIES/
├── backend/          # Python + FastAPI
│   └── app/
│       ├── api/      # REST API endpoints
│       ├── core/     # Config, security
│       ├── db/       # Database session, base
│       ├── models/   # SQLAlchemy ORM models (AC_ schema)
│       ├── schemas/  # Pydantic request/response schemas
│       └── services/ # Business logic
├── frontend/         # React + TypeScript + Vite
│   └── src/
│       ├── components/
│       │   ├── ProjectManager/
│       │   ├── Forecasting/
│       │   ├── Economics/
│       │   └── Common/
│       ├── pages/
│       ├── hooks/
│       ├── store/
│       └── types/
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Modules

| Module | Status | Description |
|---|---|---|
| Project Manager | 🚧 In Progress | Property/well browser, projects, scenarios |
| Forecasting | 📅 Planned | Decline curve analysis (Exp, Hyp, Harmonic) |
| Economic Simulator | 📅 Planned | NPV, IRR, cash flow, keyword model |
| Data Manager | 📅 Planned | Import/export, QC |
| Reserves Management | 📅 Planned | Reserves booking, classification, reporting |

## Database Schema

Follows ARIES AC_ table naming conventions:
- `AC_PROPERTY` — Well/property master data
- `AC_PROJECT` — Project definitions
- `AC_SCENARIO` — Economic scenarios
- `AC_ECONOMIC` — Keyword-driven economic parameters
- `AC_PRODUCT` — Production history (date-series volumes)
- `AC_PRODUCT_FORECAST` — Production forecasts per scenario
- `AC_QUALIFIER` — Data qualifiers/classifications
- `AC_RESERVES` — Reserves bookings

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (Full Stack)
```bash
docker-compose up --build
```
