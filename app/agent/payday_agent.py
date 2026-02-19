"""Agent orchestration wrapper for payday plan generation."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.calculators.payday import compute_plan, resolve_period_end
from app.db.models import Account as AccountModel
from app.db.models import Bill as BillModel
from app.db.models import Debt as DebtModel
from app.db.models import IncomeSchedule, PlanRun, Preference
from app.domain.models import Bill, Debt


def d(value: object) -> Decimal:
    return Decimal(str(value))


def _checks_summary(checks: dict[str, bool]) -> str:
    return ", ".join(f"{k}:{'ok' if v else 'fail'}" for k, v in checks.items())


def _determine_period_end(
    session: Session,
    paycheck_date: date,
    next_paycheck_date: date | None,
    use_income_schedule: bool,
) -> date:
    if next_paycheck_date is not None:
        return next_paycheck_date
    if use_income_schedule:
        sched = session.scalar(select(IncomeSchedule).limit(1))
        if sched and sched.frequency == "biweekly":
            sched_date = date.fromisoformat(sched.next_pay_date)
            if paycheck_date == sched_date:
                return paycheck_date + timedelta(days=14)
    return resolve_period_end(paycheck_date)


def _sum_liquid_cash(session: Session) -> Decimal:
    accounts = session.scalars(select(AccountModel)).all()
    total = Decimal("0.00")
    for account in accounts:
        if account.type in {"checking", "savings"}:
            total += d(account.balance)
    return total


def generate_payday_plan(
    session: Session,
    paycheck_amount: Decimal,
    paycheck_date: date,
    override_buffer_amount: Decimal | None = None,
    next_paycheck_date: date | None = None,
    use_income_schedule: bool = True,
) -> dict[str, object]:
    pref = session.scalar(select(Preference).limit(1))
    buffer_amount = d(pref.buffer_amount_per_paycheck) if pref else Decimal("600.00")
    min_cash_buffer = d(pref.min_cash_buffer) if pref else Decimal("2000.00")
    primary_surplus_target = pref.primary_surplus_target if pref else "invest"
    if override_buffer_amount is not None:
        buffer_amount = d(override_buffer_amount)

    bills = [
        Bill(
            id=b.id,
            name=b.name,
            amount=d(b.amount),
            cadence=b.cadence,
            due_day=b.due_day,
            autopay=b.autopay,
            weekday_anchor=b.weekday_anchor,
        )
        for b in session.scalars(select(BillModel)).all()
    ]
    debts = [
        Debt(id=x.id, name=x.name, balance=d(x.balance), apr=d(x.apr), min_payment=d(x.min_payment))
        for x in session.scalars(select(DebtModel)).all()
    ]

    period_end = _determine_period_end(session, paycheck_date, next_paycheck_date, use_income_schedule)
    starting_liquid_cash = _sum_liquid_cash(session)

    calc = compute_plan(
        paycheck_amount=d(paycheck_amount),
        paycheck_date=paycheck_date,
        period_end=period_end,
        bills=bills,
        debts=debts,
        buffer_target=buffer_amount,
        min_cash_buffer=min_cash_buffer,
        primary_surplus_target=primary_surplus_target,
        starting_liquid_cash=starting_liquid_cash,
    )

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
        "safe_to_invest": str(calc["safe_to_invest"]),
        "projected_end_cash": str(calc["projected_end_cash"]),
        "starting_liquid_cash": str(calc["starting_liquid_cash"]),
        "primary_surplus_target": calc["primary_surplus_target"],
        "details": {
            "period_start": paycheck_date.isoformat(),
            "period_end": calc["period_end"].isoformat(),
            "bills_due_total": str(calc["details"]["bills_due_total"]),
            "debt_min_total": str(calc["details"]["debt_min_total"]),
            "min_cash_buffer": str(calc["details"]["min_cash_buffer"]),
            "starting_liquid_cash": str(calc["details"]["starting_liquid_cash"]),
            "projected_end_cash": str(calc["details"]["projected_end_cash"]),
            "safe_to_invest": str(calc["details"]["safe_to_invest"]),
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
            "period_end": period_end.isoformat(),
            "buffer_amount": str(buffer_amount),
            "min_cash_buffer": str(min_cash_buffer),
            "primary_surplus_target": primary_surplus_target,
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
