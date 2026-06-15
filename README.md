# AI-Powered Eyewear Order Management System (Eluno)

A production-style full-stack order management system (OMS) designed for eyewear operations. The system integrates traditional inventory management with AI-powered prescription parsing and Machine Learning-based SLA risk prediction.

## Core Features

- **AI Prescription Parser**: Automatically extracts structured lens data (SPH, Add Power, Lens Type) from uploaded PDFs or images using **Gemini 3.5-flash**.
- **ML SLA Prediction**: Uses a **RandomForestClassifier** to predict the probability of an order breaching its SLA based on real-time operational signals (e.g., inventory, rework count, current stage).
- **Inventory Management**: Real-time tracking of lens stock levels with automated low-stock detection.
- **Order Workflow**: A comprehensive 9-stage fulfillment workflow from "Order Placed" to "Delivered".
- **Operational Dashboard**: Real-time stats on active orders, delayed orders, and high-risk shipments.
- **Automated Alerts**: Email notifications triggered by ML risk thresholds or actual SLA breaches.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL/Neon, Pydantic, Scikit-Learn, Joblib
- **Frontend**: React (TypeScript), Vite, Tailwind CSS
- **AI/ML**: Google Gemini (Flash 3.5), RandomForest Classifier

## Project Structure

```text
backend/
  app/
    api/routes/        # API endpoints (Inventory, Orders, Dashboard, Analytics)
    services/          # Business logic (SLA, ML Predictor, Alerts)
    main.py            # FastAPI App factory and configuration
    models.py          # SQLAlchemy Database Models
    schemas.py         # Pydantic Data Validation Schemas
  model/               # ML Model artifacts (.pkl) and training script
  scripts/             # Utility scripts (Backfill, SMTP test, Alert triggers)
  main.py              # Entry point for Uvicorn
frontend/
  src/
    components/        # Reusable UI components (e.g., PrescriptionUpload)
    pages/             # Page-level components
    api.js             # Centralized API client
docs/                  # Detailed documentation for architecture and modules
```

## Setup & Installation

### 1. Environment Configuration
Create a `.env` file in the root directory:

```env
# Gemini API Key (Required for Prescription Parsing)
GOOGLE_API_KEY=your_key_here

# Optional: CORS allowed origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Neon/Postgres database connection
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Optional: SMTP for Email Alerts
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=pass
ALERT_RECIPIENT=ops@example.com
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python check_db.py
uvicorn main:app --reload
```
*Backend: http://localhost:8000 | API Docs: http://localhost:8000/docs*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend: http://localhost:5173*

## SLA & Risk Logic

### SLA Rules
- **Single Vision**: 48 Hours
- **Bifocal**: 72 Hours
- **Progressive**: 96 Hours

### ML Risk Thresholds
The system predicts a **Breach Probability** (clipped to 0.0 - 1.0) and assigns a risk level:
- **Low**: 0% - 30%
- **Medium**: 30% - 70%
- **High**: 70% - 100%

*Note: Automated alerts are triggered when an order is "Breached" or exceeds a **80%** breach probability.*

## Cleanup & Maintenance
The repository is kept "Clean and Clear" by:
- Storing environment-specific values in `.env`.
- Excluding logs, caches (`__pycache__`), and build artifacts via `.gitignore`.
- Using centralized documentation in the `docs/` directory.
