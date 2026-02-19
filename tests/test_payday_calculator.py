from datetime import date
from decimal import Decimal

from app.calculators.payday import compute_plan, count_weekly_occurrences, due_amount
from app.domain.models import Bill, Debt


def bills(weekday_anchor: int | None = None) -> list[Bill]:
    return [
        Bill(id=1, name="Rent", amount=Decimal("1200.00"), cadence="monthly", due_day=1, autopay=True),
        Bill(id=2, name="Internet", amount=Decimal("80.00"), cadence="monthly", due_day=10, autopay=True),
        Bill(
            id=3,
            name="Groceries",
            amount=Decimal("100.00"),
            cadence="weekly",
            due_day=None,
            autopay=False,
            weekday_anchor=weekday_anchor,
        ),
from app.calculators.payday import compute_plan, count_weekly_occurrences
from app.domain.models import Bill, Debt


def bills() -> list[Bill]:
    return [
        Bill(id=1, name="Rent", amount=Decimal("1200.00"), cadence="monthly", due_day=1, autopay=True),
        Bill(id=2, name="Internet", amount=Decimal("80.00"), cadence="monthly", due_day=10, autopay=True),
        Bill(id=3, name="Groceries", amount=Decimal("100.00"), cadence="weekly", due_day=None, autopay=False),
    ]


def debts() -> list[Debt]:
    return [
        Debt(id=1, name="Student Loan", balance=Decimal("8000.00"), apr=Decimal("5.00"), min_payment=Decimal("120.00")),
        Debt(id=2, name="Credit Card", balance=Decimal("1800.00"), apr=Decimal("21.00"), min_payment=Decimal("65.00")),
    ]


def test_weekly_occurrences_count_from_monday_anchor() -> None:
    assert count_weekly_occurrences(date(2026, 1, 5), date(2026, 1, 19), 0) == 2


def test_weekly_occurrences_count_with_offset_anchor() -> None:
    assert count_weekly_occurrences(date(2026, 1, 5), date(2026, 1, 19), 2) == 2


def test_weekly_bill_uses_weekday_anchor() -> None:
    bill = bills(weekday_anchor=5)[2]  # saturday
    amount = due_amount(bill, date(2026, 1, 5), date(2026, 1, 19))
    assert amount == Decimal("200.00")


def test_schedule_override_changes_period_end_bill_selection() -> None:
    result = compute_plan(
        paycheck_amount=Decimal("2500.00"),
        paycheck_date=date(2026, 1, 5),
        period_end=date(2026, 1, 12),
        bills=bills(),
        debts=debts(),
        buffer_target=Decimal("600.00"),
        min_cash_buffer=Decimal("2000.00"),
        primary_surplus_target="invest",
        starting_liquid_cash=Decimal("3700.00"),
    )
    # monthly internet due on 10th should be included, weekly groceries only once in 7-day window.
    assert result["details"]["bills_due_total"] == Decimal("180.00")


def test_safe_to_invest_zero_when_below_min_cash_buffer() -> None:
    result = compute_plan(
        paycheck_amount=Decimal("1200.00"),
        paycheck_date=date(2026, 1, 5),
        period_end=date(2026, 1, 19),
        bills=bills(),
        debts=debts(),
        buffer_target=Decimal("600.00"),
        min_cash_buffer=Decimal("6000.00"),
        primary_surplus_target="invest",
        starting_liquid_cash=Decimal("1000.00"),
    )
    assert result["safe_to_invest"] == Decimal("0.00")


def test_safe_to_invest_positive_when_cash_exceeds_floor() -> None:
    result = compute_plan(
        paycheck_amount=Decimal("2500.00"),
        paycheck_date=date(2026, 1, 5),
        period_end=date(2026, 1, 19),
        bills=bills(),
        debts=debts(),
        buffer_target=Decimal("600.00"),
        min_cash_buffer=Decimal("2000.00"),
        primary_surplus_target="invest",
        starting_liquid_cash=Decimal("5000.00"),
    )
    assert result["safe_to_invest"] > Decimal("0.00")


def test_allocations_sum_to_paycheck() -> None:
    result = compute_plan(
        paycheck_amount=Decimal("2500.00"),
        paycheck_date=date(2026, 1, 5),
        period_end=date(2026, 1, 19),
        bills=bills(),
        debts=debts(),
        buffer_target=Decimal("600.00"),
        min_cash_buffer=Decimal("2000.00"),
        primary_surplus_target="invest",
        starting_liquid_cash=Decimal("5000.00"),
    )
def test_weekly_occurrences_count_from_wednesday_anchor() -> None:
    assert count_weekly_occurrences(date(2026, 1, 7), date(2026, 1, 21), 2) == 2


def test_allocations_sum_to_paycheck() -> None:
    result = compute_plan(Decimal("2500.00"), date(2026, 1, 5), bills(), debts(), Decimal("600.00"))
    total = sum(item["amount"] for item in result["allocations"])
    assert total == Decimal("2500.00")
    assert result["checks"]["allocations_sum_ok"] is True


def test_invest_routing_allocates_safe_to_invest_capped_by_remaining() -> None:
    result = compute_plan(
        paycheck_amount=Decimal("2500.00"),
        paycheck_date=date(2026, 1, 5),
        period_end=date(2026, 1, 19),
        bills=bills(),
        debts=debts(),
        buffer_target=Decimal("600.00"),
        min_cash_buffer=Decimal("2000.00"),
        primary_surplus_target="invest",
        starting_liquid_cash=Decimal("5500.00"),
    )
    buckets = {row["bucket"]: row["amount"] for row in result["allocations"]}
    assert "Invest" in buckets
    mandatory = buckets["Bills"] + buckets["Spending"] + buckets["DebtMinimum"]
    remaining = Decimal("2500.00") - mandatory
    assert buckets["Invest"] == min(result["safe_to_invest"], remaining)
def test_bills_coverage_failure_detected() -> None:
    result = compute_plan(Decimal("1250.00"), date(2026, 1, 1), bills(), debts(), Decimal("600.00"))
    assert result["checks"]["bills_covered_ok"] is False
    assert any("short by" in entry for entry in result["details"]["unfunded_items"])


def test_insufficient_funds_flags_buffer_failure() -> None:
    result = compute_plan(Decimal("220.00"), date(2026, 1, 5), bills(), debts(), Decimal("600.00"))
    assert result["checks"]["buffer_met_ok"] is False
    assert any("Buffer short" in entry for entry in result["details"]["unfunded_items"])
