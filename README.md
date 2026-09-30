# MetraSure — SIH MVP

MetraSure is a digital compliance platform designed to modernize Legal Metrology inspections. It replaces manual, error-prone paper workflows with a deterministic, mathematically verifiable compliance engine based strictly on international OIML R-76 recommendations for Non-Automatic Weighing Instruments (NAWIs).

## Project Overview

MetraSure aims to solve the core problem of opaque and slow legal metrology certifications by providing:
1. **Deterministic Rule Engine:** An auditable, backend-driven verification engine that strictly computes MPEs (Maximum Permissible Errors) without hallucinatory AI interference.
2. **Automated Report Generation:** Real-time generation of OIML-compliant prototype PDF test reports.
3. **QR Verification System:** Public-facing validation portal to verify test certificates instantly and counter fraud.
4. **AI-Assisted Explanations (Optional):** Contextual plain-language explanations of *why* a test failed, strictly derived from deterministic engine outputs.

## Architecture

* **Frontend:** Next.js 14 (App Router), React, Tailwind CSS, Recharts, Lucide Icons.
* **Backend:** Python 3, FastAPI, SQLAlchemy (ORM), Alembic (Migrations).
* **Database:** SQLite (development / MVP).
* **Document Engine:** ReportLab & Pillow (PDF generation), `qrcode` (verification linking).
* **AI Module:** Pluggable interface utilizing OpenAI or Gemini (Gracefully degrades to deterministic modes if API keys are missing).

## Setup Instructions

### Prerequisites
* Node.js v18+
* Python 3.10+ (Tested up to 3.14)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### Environment Variables
Create `.env` files in both directories if needed, but defaults work out-of-the-box.
* **Backend (`backend/.env` optional):**
  * `SECRET_KEY` = your_secret_jwt_key
  * `OPENAI_API_KEY` = sk-... (Optional: Enables AI Explanation module)
  * `GEMINI_API_KEY` = AIza... (Optional fallback for AI Explanation)
* **Frontend (`frontend/.env.local` optional):**
  * `NEXT_PUBLIC_API_URL` = http://localhost:8000/api

### Database Setup
The MVP uses SQLite. To initialize and seed the DB with SIH Demo Data:
```bash
cd backend
source venv/bin/activate
alembic upgrade head
PYTHONPATH=. python seed.py
```
*Note: This creates two demo instruments (DEMO-001, DEMO-002) and populates realistic historical dashboard metrics.*

### Running the Application
**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The API will be available at [http://localhost:8000](http://localhost:8000) (docs at `/docs`). On startup it creates any missing tables and seeds demo data if the `users` table is empty.

**Frontend:**
```bash
cd frontend
npm run dev
```
The application will be available at [http://localhost:3000](http://localhost:3000).

## Test Commands
To run the deterministic rule engine unit tests:
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

## Deployment

**Backend → Render (Web Service)**
* Root directory: `backend`
* Build command: `pip install -r requirements.txt`
* Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
* Environment variables:
  * `PYTHON_VERSION` = the Python version you tested with locally (e.g. `3.14.7`)
  * `SECRET_KEY` = a long random string
  * `FRONTEND_URL` = `https://<your-app>.vercel.app` (used for the QR verification link in PDFs)
  * `CORS_ORIGINS` = `https://<your-app>.vercel.app` (comma-separated if more than one)
  * `DATABASE_URL` (optional) = defaults to SQLite; set a Postgres URL for persistence
  * `OPENAI_API_KEY` / `GEMINI_API_KEY` (optional)
* The free tier has an ephemeral disk: the SQLite DB and generated PDFs are wiped on every restart/redeploy. The app recreates tables and re-seeds the demo data automatically on startup.

**Frontend → Vercel**
* Root directory: `frontend` (framework preset: Next.js)
* Environment variable: `NEXT_PUBLIC_API_URL` = `https://<your-backend>.onrender.com/api`
* `NEXT_PUBLIC_*` values are baked in at build time, so redeploy after changing it.

## Demo Credentials (SIH)

The system is seeded with Role-Based Access Control (RBAC):

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access. Can configure the OIML Rule Engine and view all registries. |
| **Officer** | `officer` | `officer123` | Can view dashboards, register instruments, and verify reports. |
| **Technician**| `tech` | `tech123` | Can execute field calibration tests and input measurements. |

**Recommended SIH Demo Flow:**
1. Login as `admin`.
2. View **Dashboard** analytics.
3. Select **Instruments** -> `DEMO-001` (Pass Scenario) or `DEMO-002` (Fail Scenario).
4. Click **Start Calibration Session**.
5. Input test measurements across the 5 modules.
6. Click **Evaluate** (Engine calculates instantly).
7. Complete all tabs and click **View Test Summary**.
8. Click **Generate Official PDF Report**.
9. Scan the QR code on the PDF (or click the URL) to see the Public Verification Page.
10. Check **History & Audit** or individual **Instrument Lifecycle** to see immutable audit logs.

## Supported OIML Tests (MVP)
The backend deterministically supports the core R-76 evaluation modules:
1. **Accuracy / Error of Indication** (OIML R-76-1: 3.5.1)
2. **Repeatability** (OIML R-76-1: 3.6.1)
3. **Eccentric Loading** (OIML R-76-1: 3.6.2)
4. **Zero Indication** (OIML R-76-1: 4.5.2)
5. **Tare Device** (OIML R-76-1: 4.6.1)

## Known Limitations
* **Step-based MPEs:** The MVP uses a simplified linear MPE calculation (`e` multiplier) based on active rules. Fully scaling to OIML's stepped weight bounds (e.g., `0 <= m <= 500e = 0.5e`) requires deeper parser logic in the engine.
* **Authentication:** Uses localized JWT tokens without long-lived refresh-token rotation.
* **Database:** SQLite is single-file; production deployments will require a migration to PostgreSQL.

## Future Enhancements
* **PostgreSQL Migration:** Full relational database scaling for high-concurrency environments.
* **IoT / Bluetooth Scale Integration:** Directly ingest weight telemetry from physical NAWI devices via Web-Serial or Bluetooth, bypassing manual technician entry.
* **Blockchain Hash Verification:** Tie the PDF verification token to a decentralized ledger to make retroactive report forgery mathematically impossible.
* **Complex Condition Parser:** Implement an AST (Abstract Syntax Tree) parser in the Python engine to natively interpret complex condition strings like `500e < m <= 2000e` dynamically from the DB.
