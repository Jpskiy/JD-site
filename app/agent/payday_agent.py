"""Agent orchestration wrapper for payday plan generation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculators.payday import compute_plan
from app.db.models import Bill as BillModel
from app.db.models import Debt as DebtModel
from app.db.models import PlanRun, Preference
from app.domain.models import Bill, Debt


def d(value: object) -> Decimal:
    return Decimal(str(value))


def generate_payday_plan(session: Session, paycheck_amount: Decimal, paycheck_date: date, override_buffer_amount: Decimal | None = None) -> dict[str, object]:
    pref = session.scalar(select(Preference).limit(1))
    buffer_amount = d(pref.buffer_amount_per_paycheck) if pref else Decimal("600.00")
    if override_buffer_amount is not None:
        buffer_amount = override_buffer_amount

    bills = [
        Bill(id=b.id, name=b.name, amount=d(b.amount), cadence=b.cadence, due_day=b.due_day, autopay=b.autopay)
        for b in session.scalars(select(BillModel)).all()
    ]
    debts = [
        Debt(id=x.id, name=x.name, balance=d(x.balance), apr=d(x.apr), min_payment=d(x.min_payment))
        for x in session.scalars(select(DebtModel)).all()
    ]

    calc = compute_plan(paycheck_amount=paycheck_amount, paycheck_date=paycheck_date, bills=bills, debts=debts, buffer_target=buffer_amount)

    plan_id = str(uuid4())
    session.add(PlanRun(id=plan_id))
    session.commit()

    checks = calc["checks"]
    summary = (
        "Plan is fully funded: all due bills, buffer, and debt minimums are covered."
        if all(checks.values())
        else "Plan has funding gaps. Review unfunded items and adjust spending or paycheck assumptions."
    )

    return {
        "plan_id": plan_id,
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
    }
