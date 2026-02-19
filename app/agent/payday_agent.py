"""Agent orchestration wrapper for payday plan generation."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.calculators.payday import compute_plan
from app.db.models import Bill as BillModel
from app.db.models import Debt as DebtModel
from app.db.models import PlanRun, Preference
from app.domain.models import Bill, Debt


def d(value: object) -> Decimal:
    return Decimal(str(value))


def _checks_summary(checks: dict[str, bool]) -> str:
    return ", ".join(f"{k}:{'ok' if v else 'fail'}" for k, v in checks.items())


def generate_payday_plan(session: Session, paycheck_amount: Decimal, paycheck_date: date, override_buffer_amount: Decimal | None = None) -> dict[str, object]:
    pref = session.scalar(select(Preference).limit(1))
    buffer_amount = d(pref.buffer_amount_per_paycheck) if pref else Decimal("600.00")
    if override_buffer_amount is not None:
        buffer_amount = d(override_buffer_amount)

    bills = [
        Bill(id=b.id, name=b.name, amount=d(b.amount), cadence=b.cadence, due_day=b.due_day, autopay=b.autopay)
        for b in session.scalars(select(BillModel)).all()
    ]
    debts = [
        Debt(id=x.id, name=x.name, balance=d(x.balance), apr=d(x.apr), min_payment=d(x.min_payment))
        for x in session.scalars(select(DebtModel)).all()
    ]

    calc = compute_plan(paycheck_amount=paycheck_amount, paycheck_date=paycheck_date, bills=bills, debts=debts, buffer_target=buffer_amount)

    checks = calc["checks"]
    summary = (
        "Plan is fully funded: all due bills, buffer, and debt minimums are covered."
        if all(checks.values())
        else "Plan has funding gaps. Review unfunded items and adjust spending or paycheck assumptions."
    )

    response_payload = {
        "allocations": [{"bucket": a["bucket"], "amount": str(a["amount"])} for a in calc["allocations"]],
        "checks": checks,
        "summary": summary,
        "details": {
            "period_start": paycheck_date.isoformat(),
            "period_end": calc["period_end"].isoformat(),
            "bills_due_total": str(calc["details"]["bills_due_total"]),
            "debt_min_total": str(calc["details"]["debt_min_total"]),
            "bills_funded": [
                {
                    **row,
                    "amount_due": str(row["amount_due"]),
                    "amount_funded": str(row["amount_funded"]),
                }
                for row in calc["details"]["bills_funded"]
            ],
            "unfunded_items": calc["details"]["unfunded_items"],
        },
        "inputs": {
            "paycheck_amount": str(d(paycheck_amount)),
            "paycheck_date": paycheck_date.isoformat(),
            "buffer_amount": str(buffer_amount),
        },
    }

    plan_id = str(uuid4())
    session.add(
        PlanRun(
            id=plan_id,
            paycheck_date=paycheck_date.isoformat(),
            paycheck_amount=d(paycheck_amount),
            checks_summary=_checks_summary(checks),
            plan_json=json.dumps(response_payload),
        )
    )
    session.commit()

    return {"plan_id": plan_id, **response_payload}


def list_plan_runs(session: Session, limit: int = 20) -> list[dict[str, object]]:
    runs = session.scalars(select(PlanRun).order_by(desc(PlanRun.created_at)).limit(limit)).all()
    return [
        {
            "plan_id": run.id,
            "created_at": str(run.created_at),
            "paycheck_date": run.paycheck_date,
            "paycheck_amount": str(run.paycheck_amount) if run.paycheck_amount is not None else None,
            "checks_summary": run.checks_summary,
        }
        for run in runs
    ]


def get_plan_run(session: Session, plan_id: str) -> dict[str, object] | None:
    run = session.get(PlanRun, plan_id)
    if not run:
        return None
    return {
        "plan_id": run.id,
        "created_at": str(run.created_at),
        "paycheck_date": run.paycheck_date,
        "paycheck_amount": str(run.paycheck_amount) if run.paycheck_amount is not None else None,
        "checks_summary": run.checks_summary,
        "plan": json.loads(run.plan_json) if run.plan_json else None,
    }
