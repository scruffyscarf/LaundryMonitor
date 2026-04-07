# Laundry Monitor:
Prepared by: Grigorii Fil (@Fil126) [g.fil@innopolis.university](mailto:g.fil@innopolis.university)

Innopolis, 2026

Simple web application where dormitory students can report and view the real‑time status of washing and drying machines, reducing unnecessary trips to the laundry room.

Core Components and Functionality

- Backend API (FastAPI)
  - POST /report - Accept a report containing:
    - machine_id (integer)
    - status (enum: busy, free, unavailable)
    - time_remaining (optional integer, minutes) - for drying machines the time is not displayed right after you start the program, so this value is optional
  - GET /machines - Return list of all machines with their inferred current status (see rules below).
  - GET /machines/{id}/history - Return last few reports for a machine (optional, for debugging).
- Database (SQLite)
  - Table machines: id (PK), name (e.g., "Washer 1"), type (wash/dry).
  - Table reports: id (PK), machine_id (FK), timestamp (datetime), status (free/busy/unavailable), time_remaining (integer, nullable).
- Frontend (Streamlit)
  - Main view displays all machines in a grid/card layout.
  - For each machine: name, type, and inferred status with a colour code:
    - Free (green)
    - Busy (red)
    - Probably free (yellow) - see inference rules
    - Unavailable (grey)
  - A form to submit a new report (dropdown for machine, radio for status, optional time field, optional reporter name).
  - Refresh button (or auto‑refresh every 30 seconds).

Inference Rules (implemented in backend)

- Unavailable - if the latest report for a machine has status unavailable.
- Busy (with known end time) - if latest report is busy AND report.time_remaining is not null AND current_time < report.timestamp + report.time_remaining.
- Busy (no known end time) - if latest report is busy AND report.time_remaining is null AND current_time < report.timestamp + 4 hours.
- Probably free - if latest report is busy AND report.time_remaining is null AND current_time >= report.timestamp + 4 hours.
- Free - if latest report is free (user explicitly marks it free) OR if latest report is busy AND report.time_remaining is not null AND current_time >= report.timestamp + report.time_remaining.

Constraints & Simplifications

- No user authentication (anyone can report)
- Machines are pre‑loaded via a seed script (no admin UI required)
- The UI is functional and clean, not visually polished
- All data is stored locally; no external APIs

Stretch Goals (if time permits)

- Simple admin page (password‑protected) to add/edit machines
- "Report as free" button directly from the machine card

Quality Requirements

| Attribute       | Metric                        | Threshold                           | Tool             | Is CI Gate? |
| --------------- | ----------------------------- | ----------------------------------- | ---------------- | ----------- |
| Maintainability | Cyclomatic Complexity         | < 8 per function                    | radon            | Yes         |
| Maintainability | Style Conformance (PEP8)      | 0 errors                            | flake8           | Yes         |
| Maintainability | Maintainability Index         | \> 65 (A or B grade)                | radon            | No          |
| Reliability     | Unit Tests Pass Rate          | 100% pass                           | pytest           | Yes         |
| Reliability     | Line Coverage                 | ≥ 70%                               | pytest-cov       | Yes         |
| Security        | High‑severity vulnerabilities | 0 findings                          | bandit           | Yes         |
| Documentation   | OpenAPI Contract Completeness | All endpoints documented in OpenAPI | FastAPI/ Swagger | No          |
| Performance     | API Response Time             | P95 < 300ms (local)                 | locust           | No          |
| Code Quality    | Imports & structure           | No unused imports/variables         | flake8           | Yes         |

Quality Gates

<div class="joplin-table-wrapper"><table><tbody><tr><th><p>Gate</p></th><th><p>When</p></th><th><p>Blockers</p></th></tr><tr><td><p>Pre‑commit</p></td><td><p>Before git commit (developer machine)</p></td><td><ul><li>flake8 errors</li><li>bandit high‑severity issues</li></ul></td></tr><tr><td><p>Pull Request</p></td><td><p>When a PR is opened against main</p></td><td><ul><li>Any pytest failure</li><li>Coverage drops below 70%</li><li>radon complexity &gt; 8 in any function</li><li>bandit errors</li><li>No approval from another team member</li></ul></td></tr><tr><td><p>Release</p></td><td><p>Before demo</p></td><td><ul><li>Any CI gate red.</li><li>Critical feature not working (cannot report, cannot view status)</li></ul></td></tr></tbody></table></div>

Quality Assessment Tools (with commands)

| Requirement                   | Tool            | Command (run from project root)                                                |
| ----------------------------- | --------------- | ------------------------------------------------------------------------------ |
| Cyclomatic Complexity         | radon           | radon cc src/ -a -s                                                            |
| Maintainability Index         | radon           | radon mi src/ -s                                                               |
| Style (PEP8)                  | flake8          | flake8 src/ tests/                                                             |
| Unit Tests Pass Rate          | pytest          | pytest                                                                         |
| Line Coverage                 | pytest-cov      | pytest --cov=src<br><br>\--cov-report=term-missing<br><br>\--cov-fail-under=70 |
| Security Scan                 | bandit          | bandit -r src/ -ll                                                             |
| OpenAPI Contract Completeness | FastAPI/Swagger | _Manual verification at /docs endpoint_                                        |
| Performance Smoke Test        | locust          | locust -f tests/load/locustfile.py<br><br>\--headless -u 1 -r 1 -t 10s         |
| Dependency Validation         | poetry          | poetry check                                                                   |

---

### Frontend Implementation (Streamlit)

The frontend is implemented in:

- `frontend/app.py` - launcher entry point
- `frontend/src/app.py` - main Streamlit application
- `frontend/src/api.py` - backend API client
- `frontend/src/models.py` - typed models and status inference logic
- `frontend/src/ui.py` - UI rendering and custom styling

Quick Start (Frontend)

1. Install dependencies:

  pip install -r frontend/requirements.txt

2. Set backend URL (optional, default is `http://localhost:8000`):

  export BACKEND_API_URL=http://localhost:8000

3. Run frontend:

  streamlit run frontend/app.py

Frontend Features

- Live machine board with card/grid layout
- Status color coding:
  - Free (green)
  - Busy (red)
  - Probably free (yellow)
  - Unavailable (grey)
- Submit report form with optional remaining time and optional reporter name
- Manual refresh and auto-refresh (30s by default)
- Sidebar filters by machine type and status
- Backend communication with robust error handling

Test command for frontend logic:

pytest frontend/tests/

---

### Backend Implementation (FastAPI)

The backend is implemented in:

* `src/main.py` – FastAPI application entry point
* `src/schemas.py` – Pydantic models for request/response validation
* `src/models.py` – SQLAlchemy models
* `src/crud.py` – Database access and report logic
* `src/database.py` – Session and SQLite connection

Quick Start (Backend)

1. Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run backend:

```bash
uvicorn src.main:app --reload
```

---

## Testing

Run all tests with:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=src --cov-report=term-missing
```

For security report:

```bash
> cd backend
backend> bandit ./src/
```

---