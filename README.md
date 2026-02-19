# Finance Co-Pilot v1 (Local-First)

Finance Co-Pilot v1 is a deterministic payday planning agent that runs fully local with SQLite + FastAPI.

## Features
- SQLite database schema + init script
- Demo seed profile (accounts, bills, debts, preferences, income schedule) defaulted to CAD
- Deterministic payday planner (no LLM math)
- Balance-aware planning (`starting_liquid_cash`, `projected_end_cash`, `safe_to_invest`)
- Plan output persisted for history/retrieval
- FastAPI endpoints:
  - `POST /seed/demo`
  - `POST /plan/payday`
  - `GET /plans`
  - `GET /plans/{plan_id}`
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
    "next_paycheck_date": "2026-01-12",
    "use_income_schedule": true,
    "override_buffer_amount": 600
  }'
```

## List Recent Plans
```bash
curl http://127.0.0.1:8000/plans
```

## Get One Stored Plan
```bash
curl http://127.0.0.1:8000/plans/<plan_id>
```

## Example Response (POST /plan/payday)
```json
{
  "plan_id": "uuid",
  "allocations": [
    {"bucket": "Bills", "amount": 180.00},
    {"bucket": "Spending", "amount": 600.00},
    {"bucket": "DebtMinimum", "amount": 200.00},
    {"bucket": "Invest", "amount": 410.00},
    {"bucket": "ExtraDebt", "amount": 1000.43}
  ],
  "checks": {
    "allocations_sum_ok": true,
    "bills_covered_ok": true,
    "buffer_met_ok": true,
    "min_cash_buffer_met_ok": true
  },
  "summary": "Plan is fully funded: all due bills, buffer, and debt minimums are covered.",
  "safe_to_invest": "410.00",
  "projected_end_cash": "2410.00",
  "starting_liquid_cash": "3700.00",
  "primary_surplus_target": "invest",
  "details": {
    "period_start": "2026-01-05",
    "period_end": "2026-01-12",
    "bills_due_total": "180.00",
    "debt_min_total": "200.00",
    "min_cash_buffer": "2000.00",
    "starting_liquid_cash": "3700.00",
    "projected_end_cash": "2410.00",
    "safe_to_invest": "410.00",
    "bills_funded": [],
    "unfunded_items": []
  },
  "inputs": {
    "paycheck_amount": "2390.43",
    "paycheck_date": "2026-01-05",
    "period_end": "2026-01-12",
    "buffer_amount": "600.00",
    "min_cash_buffer": "2000.00",
    "primary_surplus_target": "invest"
  }
}
```

## CLI Demo
```bash
python -m app.cli demo-payday --amount 2390.43 --date 2026-01-05 --next-paycheck-date 2026-01-12
```

## Tests
```bash
pytest -q
```
