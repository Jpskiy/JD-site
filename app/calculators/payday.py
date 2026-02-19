"""Deterministic payday planning calculations."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.domain.models import Bill, Debt

CENT = Decimal("0.01")


VALID_SURPLUS_TARGETS = {"invest", "extra_debt", "emergency_fund"}


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def resolve_period_end(paycheck_date: date, next_paycheck_date: date | None = None) -> date:
    return next_paycheck_date if next_paycheck_date is not None else paycheck_date + timedelta(days=14)


def count_weekly_occurrences(start: date, end: date, anchor_weekday: int) -> int:
    """Count weekly occurrences in [start, end) for a given weekday anchor (0=Mon)."""
    if end <= start:
        return 0
    days_until_anchor = (anchor_weekday - start.weekday()) % 7
    first_occurrence = start + timedelta(days=days_until_anchor)
    if first_occurrence >= end:
        return 0
    span_days = (end - first_occurrence).days
    return 1 + (span_days - 1) // 7


def is_monthly_due(due_day: int | None, start: date, end: date) -> bool:
    if due_day is None:
        return False
    current = start
    while current < end:
        month_end_day = 31
        if current.month in (4, 6, 9, 11):
            month_end_day = 30
        if current.month == 2:
            month_end_day = 29 if (current.year % 4 == 0 and (current.year % 100 != 0 or current.year % 400 == 0)) else 28
        candidate = date(current.year, current.month, min(due_day, month_end_day))
        if start <= candidate < end:
            return True
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return False


def due_amount(bill: Bill, start: date, end: date) -> Decimal:
    if bill.cadence == "weekly":
        # TODO: Store bill weekday explicitly for all weekly bills and enforce it at data model validation.
        anchor = bill.weekday_anchor if bill.weekday_anchor is not None else start.weekday()
        occurrences = count_weekly_occurrences(start, end, anchor)
        return money(bill.amount * Decimal(occurrences))
    if bill.cadence == "biweekly":
        return money(bill.amount)
    if bill.cadence == "monthly" and is_monthly_due(bill.due_day, start, end):
        return money(bill.amount)
    return Decimal("0.00")


def compute_plan(
    paycheck_amount: Decimal,
    paycheck_date: date,
    period_end: date,
    bills: list[Bill],
    debts: list[Debt],
    buffer_target: Decimal,
    min_cash_buffer: Decimal,
    primary_surplus_target: str,
    starting_liquid_cash: Decimal,
) -> dict[str, object]:
    paycheck_amount = money(paycheck_amount)
    buffer_target = money(buffer_target)
    min_cash_buffer = money(min_cash_buffer)
    starting_liquid_cash = money(starting_liquid_cash)
    primary_surplus_target = primary_surplus_target if primary_surplus_target in VALID_SURPLUS_TARGETS else "invest"

    remaining = paycheck_amount
    bill_details: list[dict[str, object]] = []
    total_bills_due = Decimal("0.00")
    funded_bills = Decimal("0.00")

    ordered = sorted(bills, key=lambda b: ((b.due_day or 99), b.name))
    for bill in ordered:
        due = due_amount(bill, paycheck_date, period_end)
        if due <= 0:
            continue
        total_bills_due += due
        funded = money(min(remaining, due))
        remaining = money(remaining - funded)
        funded_bills += funded
        bill_details.append(
            {
                "bill_id": bill.id,
                "bill_name": bill.name,
                "cadence": bill.cadence,
                "amount_due": money(due),
                "amount_funded": funded,
                "fully_funded": funded + CENT >= due,
            }
        )

    buffer_allocated = money(min(remaining, buffer_target))
    remaining = money(remaining - buffer_allocated)

    debt_min_total = money(sum(money(d.min_payment) for d in debts))
    debt_min_allocated = money(min(remaining, debt_min_total))
    remaining = money(remaining - debt_min_allocated)

    projected_end_cash = money(starting_liquid_cash + paycheck_amount - money(total_bills_due) - buffer_target - debt_min_total)
    safe_to_invest = money(max(Decimal("0.00"), projected_end_cash - min_cash_buffer))

    target_alloc = Decimal("0.00")
    target_bucket = None
    if primary_surplus_target == "invest":
        target_bucket = "Invest"
        target_alloc = money(min(remaining, safe_to_invest))
    elif primary_surplus_target == "emergency_fund":
        target_bucket = "EmergencyFundTopUp"
        target_alloc = money(min(remaining, safe_to_invest))

    extra_debt = remaining
    allocations = [
        {"bucket": "Bills", "amount": money(funded_bills)},
        {"bucket": "Spending", "amount": buffer_allocated},
        {"bucket": "DebtMinimum", "amount": debt_min_allocated},
    ]
    if target_bucket:
        allocations.append({"bucket": target_bucket, "amount": target_alloc})
        extra_debt = money(remaining - target_alloc)
    allocations.append({"bucket": "ExtraDebt", "amount": money(extra_debt)})

    alloc_sum = money(sum(a["amount"] for a in allocations))
    checks = {
        "allocations_sum_ok": abs(alloc_sum - paycheck_amount) <= CENT,
        "bills_covered_ok": money(funded_bills) + CENT >= money(total_bills_due),
        "buffer_met_ok": buffer_allocated + CENT >= buffer_target,
        "min_cash_buffer_met_ok": projected_end_cash + CENT >= min_cash_buffer,
    }

    unfunded = []
    for b in bill_details:
        if not b["fully_funded"]:
            short = money(b["amount_due"] - b["amount_funded"])
            unfunded.append(f"{b['bill_name']} short by ${short}")
    if buffer_allocated + CENT < buffer_target:
        unfunded.append(f"Buffer short by ${money(buffer_target - buffer_allocated)}")
    if debt_min_allocated + CENT < debt_min_total:
        unfunded.append(f"Debt minimums short by ${money(debt_min_total - debt_min_allocated)}")

    return {
        "period_end": period_end,
        "allocations": allocations,
        "checks": checks,
        "safe_to_invest": safe_to_invest,
        "starting_liquid_cash": starting_liquid_cash,
        "projected_end_cash": projected_end_cash,
        "primary_surplus_target": primary_surplus_target,
        "details": {
            "bills_due_total": money(total_bills_due),
            "debt_min_total": debt_min_total,
            "min_cash_buffer": min_cash_buffer,
            "starting_liquid_cash": starting_liquid_cash,
            "projected_end_cash": projected_end_cash,
            "safe_to_invest": safe_to_invest,
            "bills_funded": bill_details,
            "unfunded_items": unfunded,
        },
    }
