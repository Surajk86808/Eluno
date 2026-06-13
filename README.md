# AI-Powered Eyewear Order Management System

Production-style full-stack order management system for an eyewear company. It tracks lens inventory, prescription orders, fulfillment workflow, SLA health, risk prediction, and operational alerts.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React, Vite, Tailwind CSS
- AI layer: RandomForest SLA breach prediction with saved model and encoders

## Project Structure

```text
backend/
  main.py            Compatibility entry point for uvicorn main:app
  app/
    api/routes/        FastAPI route modules
    services/          SLA, prediction, and alert logic
    constants.py       Workflow, SLA, lens, and store constants
    crud.py            Database operations and order serialization
    database.py        SQLite connection and SQLAlchemy session
    main.py            FastAPI application factory and route registration
    models.py          SQLAlchemy tables
    schemas.py         Pydantic request and response models
  seed.py              Dummy inventory and order generator
  requirements.txt
frontend/
  src/
    App.jsx            React pages and components
    api.js             API client
    styles.css         Tailwind component classes
docs/
  *.md                 Architecture, module, API, and interview documentation
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`.

API docs are available at:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

If `uvicorn main:app --reload` shows `[WinError 10013]`, port `8000` is already in use or blocked. Check the process:

```powershell
netstat -ano | findstr :8000
```

Then either stop the listed process:

```powershell
taskkill /PID <PID> /F
uvicorn main:app --reload
```

Or run the backend on another port:

```powershell
uvicorn main:app --reload --port 8001
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Core APIs

- `GET /health`
- `GET /api/inventory`
- `GET /api/inventory/check?lens_type=Single%20Vision&power=-2.0`
- `GET /api/orders`
- `GET /api/orders?status=Lens%20Cutting`
- `GET /api/orders?lens_type=Progressive`
- `GET /api/orders?store_location=Chicago%20Loop`
- `POST /api/orders`
- `PATCH /api/orders/{order_id}/status`
- `GET /api/orders/{order_id}/delay-history`
- `POST /predict-risk`
- `POST /api/predict-risk`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/active-orders`
- `GET /api/dashboard/delayed-orders`
- `GET /api/analytics/operations`

## Seed Data

`python seed.py` creates:

- 75 inventory rows: 3 lens types x 25 powers from `-6.0` to `+6.0`
- 150 realistic sample orders across workflow statuses and store locations

## SLA Rules

- Single Vision: 24 hours
- Bifocal: 48 hours
- Progressive: 72 hours

ML risk prediction:

- 0-40 percent breach probability: Low
- 40-70 percent breach probability: Medium
- 70-100 percent breach probability: High
