from datetime import date
from decimal import Decimal

from app.calculators.payday import compute_payday_allocations
from app.domain.models import Bill, Debt


def sample_bills() -> list[Bill]:
    return [
        Bill(id=1, name="Rent", amount=Decimal("1200.00"), cadence="monthly", due_day=1, autopay=True),
        Bill(id=2, name="Internet", amount=Decimal("80.00"), cadence="monthly", due_day=10, autopay=True),
        Bill(id=3, name="Groceries", amount=Decimal("100.00"), cadence="weekly", due_day=None, autopay=False),
    ]


def sample_debts() -> list[Debt]:
    return [
        Debt(id=1, name="Student Loan", balance=Decimal("8000.00"), apr=Decimal("5.00"), min_payment=Decimal("120.00")),
        Debt(id=2, name="Credit Card", balance=Decimal("1200.00"), apr=Decimal("20.00"), min_payment=Decimal("50.00")),
    ]


def test_allocations_sum_to_paycheck() -> None:
    result = compute_payday_allocations(
        paycheck_amount=Decimal("2500.00"),
        bills=sample_bills(),
        debts=sample_debts(),
        paycheck_date=date(2026, 1, 5),
        buffer_target=Decimal("600.00"),
    )
    total = sum(a["amount"] for a in result["allocations"])
    assert total == Decimal("2500.00")
    assert result["checks"]["allocations_sum_ok"] is True


def test_bills_coverage_logic_flags_unfunded_bill() -> None:
    result = compute_payday_allocations(
        paycheck_amount=Decimal("1300.00"),
        bills=sample_bills(),
        debts=sample_debts(),
        paycheck_date=date(2026, 1, 1),
        buffer_target=Decimal("600.00"),
    )
    assert result["checks"]["bills_covered_ok"] is False
    assert any("short by" in item for item in result["unfunded"])


def test_insufficient_funds_failures_are_returned() -> None:
    result = compute_payday_allocations(
        paycheck_amount=Decimal("200.00"),
        bills=sample_bills(),
        debts=sample_debts(),
        paycheck_date=date(2026, 1, 5),
        buffer_target=Decimal("600.00"),
    )
    assert result["checks"]["buffer_met_ok"] is False
    assert result["checks"]["bills_covered_ok"] is False
    assert any("Buffer short" in item for item in result["unfunded"])
