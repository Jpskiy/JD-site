# Finance Co-Pilot v1 (Local-First)

Finance Co-Pilot v1 is a deterministic payday planning agent that runs fully local with SQLite + FastAPI.

## Features
- SQLite database schema + init script
- Demo seed profile (accounts, bills, debts, preferences)
- Deterministic payday planner (no LLM math)
- FastAPI endpoints:
  - `POST /seed/demo`
  - `POST /plan/payday`
- CLI demo command:
  - `python -m app.cli demo-payday --amount 2390.43`
- Unit/API tests with pytest

## Architecture
```
app/
  db/
  domain/
  calculators/
  agent/
  api/
  cli.py
tests/
```

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run API
```bash
uvicorn app.api.main:app --reload
```

## Seed Demo Data
```bash
curl -X POST http://127.0.0.1:8000/seed/demo
```

## Generate Payday Plan
```bash
curl -X POST http://127.0.0.1:8000/plan/payday \
  -H "Content-Type: application/json" \
  -d '{
    "paycheck_amount": 2390.43,
    "paycheck_date": "2026-01-05",
    "override_buffer_amount": 600
  }'
```

## Example Response
```json
{
  "plan_id": "uuid",
  "allocations": [
    {"bucket": "Bills", "amount": 365.00},
    {"bucket": "Spending", "amount": 600.00},
    {"bucket": "DebtMinimum", "amount": 200.00},
    {"bucket": "ExtraDebt", "amount": 1225.43}
  ],
  "checks": {
    "allocations_sum_ok": true,
    "bills_covered_ok": true,
    "buffer_met_ok": true
  },
  "summary": "Plan is fully funded: all due bills, buffer, and debt minimums are covered.",
  "details": {
    "period_start": "2026-01-05",
    "period_end": "2026-01-19",
    "bills_due_total": "365.00",
    "debt_min_total": "200.00",
    "bills_funded": [],
    "unfunded_items": []
  }
}
```

## CLI Demo
```bash
python -m app.cli demo-payday --amount 2390.43
```

## Tests
```bash
pytest -q
```

## Deterministic Allocation Rules
1. Fund bills due before next paycheck date (`paycheck_date + 14 days`).
2. Fund spending buffer (default from preferences, default 600).
3. Fund debt minimum payments.
4. Allocate remainder to `ExtraDebt`.

Validation checks returned:
- `allocations_sum_ok`
- `bills_covered_ok`
- `buffer_met_ok`

When funds are insufficient, response still returns a plan plus `details.unfunded_items` guidance.
