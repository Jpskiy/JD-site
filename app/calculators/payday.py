"""Deterministic payday planning rules for Finance Co-Pilot."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.domain.models import Bill, Debt, DueBillFunding

CENT = Decimal("0.01")


def q(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def next_paycheck_date(paycheck_date: date) -> date:
    return paycheck_date + timedelta(days=14)


def _monthly_due_in_window(start: date, end: date, due_day: int | None) -> bool:
    if due_day is None:
        return False
    cursor = start
    while cursor < end:
        month_day = min(due_day, 28 if cursor.month == 2 else 30 if cursor.month in {4, 6, 9, 11} else 31)
        candidate = date(cursor.year, cursor.month, month_day)
        if start <= candidate < end:
            return True
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return False


def due_amount_for_window(bill: Bill, period_start: date, period_end: date) -> Decimal:
    if bill.cadence == "weekly":
        return q(bill.amount * Decimal("2"))
    if bill.cadence == "biweekly":
        return q(bill.amount)
    if bill.cadence == "monthly":
        return q(bill.amount) if _monthly_due_in_window(period_start, period_end, bill.due_day) else Decimal("0.00")
    return Decimal("0.00")


def compute_due_bill_funding(bills: list[Bill], period_start: date, period_end: date, available: Decimal) -> tuple[list[DueBillFunding], Decimal]:
    funding: list[DueBillFunding] = []
    remaining = q(available)

    due_bills = []
    for bill in bills:
        due_amount = due_amount_for_window(bill, period_start, period_end)
        if due_amount > 0:
            due_bills.append((bill, due_amount))

    due_bills.sort(key=lambda item: (item[0].due_day or 99, item[0].name))

    for bill, due_amount in due_bills:
        funded = q(min(remaining, due_amount))
        remaining = q(remaining - funded)
        funding.append(
            DueBillFunding(
                bill_id=bill.id,
                bill_name=bill.name,
                cadence=bill.cadence,
                amount_due=due_amount,
                amount_funded=funded,
                fully_funded=funded >= due_amount,
            )
        )

    total_funded = q(sum(item.amount_funded for item in funding))
    return funding, total_funded


def compute_payday_allocations(
    paycheck_amount: Decimal,
    bills: list[Bill],
    debts: list[Debt],
    paycheck_date: date,
    buffer_target: Decimal,
) -> dict[str, object]:
    paycheck_amount = q(paycheck_amount)
    buffer_target = q(buffer_target)
    period_end = next_paycheck_date(paycheck_date)

    due_funding, bills_allocated = compute_due_bill_funding(bills, paycheck_date, period_end, paycheck_amount)
    remaining = q(paycheck_amount - bills_allocated)

    buffer_allocated = q(min(remaining, buffer_target))
    remaining = q(remaining - buffer_allocated)

    debt_min_target = q(sum(q(debt.min_payment) for debt in debts))
    debt_min_allocated = q(min(remaining, debt_min_target))
    remaining = q(remaining - debt_min_allocated)

    extra_debt = remaining

    allocations = [
        {"bucket": "Bills", "amount": bills_allocated},
        {"bucket": "Spending", "amount": buffer_allocated},
        {"bucket": "DebtMinimum", "amount": debt_min_allocated},
        {"bucket": "ExtraDebt", "amount": extra_debt},
    ]

    allocations_sum = q(sum(a["amount"] for a in allocations))
    bills_due_total = q(sum(item.amount_due for item in due_funding))

    checks = {
        "allocations_sum_ok": abs(allocations_sum - paycheck_amount) <= CENT,
        "bills_covered_ok": bills_allocated + CENT >= bills_due_total,
        "buffer_met_ok": buffer_allocated + CENT >= buffer_target,
    }

    unfunded: list[str] = []
    for bill in due_funding:
        if not bill.fully_funded:
            short = q(bill.amount_due - bill.amount_funded)
            unfunded.append(f"{bill.bill_name} short by ${short}")
    if buffer_allocated + CENT < buffer_target:
        unfunded.append(f"Buffer short by ${q(buffer_target - buffer_allocated)}")
    if debt_min_allocated + CENT < debt_min_target:
        unfunded.append(f"Debt minimums short by ${q(debt_min_target - debt_min_allocated)}")

    return {
        "period_end": period_end,
        "allocations": allocations,
        "checks": checks,
        "due_bill_funding": due_funding,
        "unfunded": unfunded,
        "bills_due_total": bills_due_total,
        "debt_min_total": debt_min_target,
    }
