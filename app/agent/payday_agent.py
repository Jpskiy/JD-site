"""Orchestrator wrapper for deterministic payday plan computation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculators.payday import compute_payday_allocations
from app.db.models import Bill as BillModel
from app.db.models import Debt as DebtModel
from app.db.models import PlanRun, Preferences as PreferencesModel
from app.domain.models import Bill, Debt


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def run_payday_plan(
    session: Session,
    paycheck_amount: Decimal,
    paycheck_date: date,
    override_buffer_amount: Decimal | None = None,
) -> dict[str, object]:
    bills = [
        Bill(
            id=b.id,
            name=b.name,
            amount=_to_decimal(b.amount),
            cadence=b.cadence,
            due_day=b.due_day,
            autopay=b.autopay,
        )
        for b in session.scalars(select(BillModel)).all()
    ]
    debts = [
        Debt(
            id=d.id,
            name=d.name,
            balance=_to_decimal(d.balance),
            apr=_to_decimal(d.apr),
            min_payment=_to_decimal(d.min_payment),
        )
        for d in session.scalars(select(DebtModel)).all()
    ]

    pref = session.scalar(select(PreferencesModel).limit(1))
    default_buffer = _to_decimal(pref.buffer_amount_per_paycheck) if pref else Decimal("600.00")
    buffer_target = override_buffer_amount if override_buffer_amount is not None else default_buffer

    calc = compute_payday_allocations(
        paycheck_amount=paycheck_amount,
        bills=bills,
        debts=debts,
        paycheck_date=paycheck_date,
        buffer_target=buffer_target,
    )

    plan_id = str(uuid4())
    session.add(PlanRun(id=plan_id))
    session.commit()

    checks = calc["checks"]
    if all(checks.values()):
        summary = "Plan is fully funded: bills, buffer, and debt minimums are covered."
    else:
        summary = "Plan has funding gaps. Prioritize listed unfunded items before discretionary spending."

    details = {
        "period_start": paycheck_date.isoformat(),
        "period_end": calc["period_end"].isoformat(),
        "bills_due_total": str(calc["bills_due_total"]),
        "debt_min_total": str(calc["debt_min_total"]),
        "bills_funded": [
            {
                "bill_id": item.bill_id,
                "bill_name": item.bill_name,
                "cadence": item.cadence,
                "amount_due": str(item.amount_due),
                "amount_funded": str(item.amount_funded),
                "fully_funded": item.fully_funded,
            }
            for item in calc["due_bill_funding"]
        ],
        "unfunded_items": calc["unfunded"],
    }

    return {
        "plan_id": plan_id,
        "allocations": [{"bucket": a["bucket"], "amount": str(a["amount"])} for a in calc["allocations"]],
        "checks": checks,
        "summary": summary,
        "details": details,
    }
