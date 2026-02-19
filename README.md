# Finance Co-Pilot (v1)

Local-first finance agent focused on a deterministic **Payday Plan Generator**.

## What v1 includes

- SQLite database with schema/init script and demo seeding
- Deterministic payday planning calculator (no LLM math)
- FastAPI endpoint for plan generation
- CLI demo command
- Pytest unit tests for allocation and validation rules

## Tech stack

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Pydantic
- Pytest

## Project structure

```text
app/
  api/          # FastAPI app and schemas
  agent/        # orchestration wrapper (plan -> compute -> verify -> explain)
  calculators/  # deterministic pure functions
  db/           # sqlite models/session/init/seed
  domain/       # core domain models
  cli.py        # local demo CLI
tests/
```

## Quickstart (under 5 minutes)

### 1) Setup virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run API

```bash
uvicorn app.api.main:app --reload
```

### 3) Seed demo profile

```bash
curl -X POST http://127.0.0.1:8000/seed/demo
```

### 4) Generate payday plan

```bash
curl -X POST http://127.0.0.1:8000/plan/payday \
  -H "Content-Type: application/json" \
  -d '{
    "paycheck_amount": 2390.43,
    "paycheck_date": "2026-01-05"
  }'
```

Example response:

```json
{
  "plan_id": "3f9b3d1f-9cb6-4cd7-b4cb-4f4e280ec0bc",
  "allocations": [
    {"bucket": "Bills", "amount": 335.00},
    {"bucket": "Spending", "amount": 600.00},
    {"bucket": "DebtMinimum", "amount": 195.00},
    {"bucket": "ExtraDebt", "amount": 1260.43}
  ],
  "checks": {
    "allocations_sum_ok": true,
    "bills_covered_ok": true,
    "buffer_met_ok": true
  },
  "summary": "Plan is fully funded: bills, buffer, and debt minimums are covered.",
  "details": {
    "period_start": "2026-01-05",
    "period_end": "2026-01-19",
    "bills_due_total": "335.00",
    "debt_min_total": "195.00",
    "bills_funded": [
      {
        "bill_id": 2,
        "bill_name": "Internet",
        "cadence": "monthly",
        "amount_due": "80.00",
        "amount_funded": "80.00",
        "fully_funded": true
      }
    ],
    "unfunded_items": []
  }
}
```

## CLI demo

```bash
python -m app.cli demo-payday --amount 2390.43
```

Optional date override:

```bash
python -m app.cli demo-payday --amount 2390.43 --date 2026-01-05
```

## Tests

```bash
pytest
```

## Allocation rules (deterministic)

Given `paycheck_amount` and `paycheck_date` (next paycheck assumed +14 days):

1. Fund due bills in window `[paycheck_date, next_paycheck_date)`
2. Fund spending buffer (default from preferences, default value 600)
3. Fund debt minimum payments
4. Put remainder into `ExtraDebt`

Checks returned:

- `allocations_sum_ok` (sum equals paycheck within 1 cent)
- `bills_covered_ok`
- `buffer_met_ok`

If insufficient funds, plan still returns with failed checks and `details.unfunded_items` suggestions.
