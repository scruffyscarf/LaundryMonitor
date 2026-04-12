# Laundry Monitor

## Overview

Simple web application where dormitory students can report and view the real‑time status of washing and drying machines, reducing unnecessary trips to the laundry room.

---

## Core Components and Functionality

### Backend API (FastAPI)

| Endpoint | Description |
|----------|-------------|
| `POST /report` | Accept a report containing: `machine_id` (int), `status` (enum: `busy`, `free`, `unavailable`), `time_remaining` (optional int, minutes) — for drying machines the time is not displayed right after you start the program, so this value is optional |
| `GET /machines` | Return list of all machines with their inferred current status (see inference rules below) |
| `GET /machines/{id}/history` | Return last few reports for a machine (optional, for debugging) |

### Database (SQLite)

- **Table `machines`**: `id` (PK), `name` (e.g., "Washer 1"), `type` (`wash`/`dry`)
- **Table `reports`**: `id` (PK), `machine_id` (FK), `timestamp` (datetime), `status` (`free`/`busy`/`unavailable`), `time_remaining` (int, nullable)

### Frontend (Streamlit)

- Main view displays all machines in a grid/card layout
- For each machine: name, type, and inferred status with colour code:
  - 🟢 **Free** (green)
  - 🔴 **Busy** (red)
  - 🟡 **Probably free** (yellow)
  - ⚪ **Unavailable** (grey)
- A form to submit a new report (dropdown for machine, radio for status, optional time field, optional reporter name)
- Refresh button (or auto‑refresh every 30 seconds)

---

## Inference Rules

| Status | Condition |
|--------|-----------|
| **Unavailable** | if the latest report for a machine has status `unavailable` |
| **Busy (with known end time)** | if latest report is `busy` AND `report.time_remaining` is not null AND `current_time < report.timestamp + report.time_remaining` |
| **Busy (no known end time)** | if latest report is `busy` AND `report.time_remaining` is null AND `current_time < report.timestamp + 4 hours` |
| **Probably free** | if latest report is `busy` AND `report.time_remaining` is null AND `current_time >= report.timestamp + 4 hours` |
| **Free** | if latest report is `free` (user explicitly marks it free) OR if latest report is `busy` AND `report.time_remaining` is not null AND `current_time >= report.timestamp + report.time_remaining` |

---

## Constraints & Simplifications

- No user authentication (anyone can report)
- Machines are pre‑loaded via a seed script (no admin UI required)
- The UI is functional and clean, not visually polished
- All data is stored locally; no external APIs
- Simple admin page (password‑protected) to add/edit machines
- "Report as free" button directly from the machine card

---

## App Quality

- Average complexity: A (2.111111111111111)
- Total coverage: 87.45%
- Vulnerabilities: 0
---

## Quality Gates

| Gate | When | Blockers |
|------|------|----------|
| **Pre-commit** | Before git commit (developer machine) | • `flake8` errors<br>• `bandit` high‑severity issues |
| **Pull Request** | When a PR is opened against `main` | • Any `pytest` failure<br>• Coverage drops below 70%<br>• `radon` complexity > 8 in any function<br>• `bandit` errors<br>• No approval from another team member |
| **Release** | Before demo | • Any CI gate red<br>• Critical feature not working (cannot report, cannot view status) |

---

## How to use

1. Clone repository:

```bash
git clone https://github.com/scruffyscarf/LaundryMonitor

cd LaundryMonitor
```

2. Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

3. Run the App

```bash
mv .env.sample .env
./scripts/run.sh
```
