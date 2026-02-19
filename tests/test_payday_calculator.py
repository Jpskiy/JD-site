from datetime import date
from decimal import Decimal

from app.calculators.payday import compute_plan
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


def test_allocations_sum_to_paycheck() -> None:
    result = compute_plan(Decimal("2500.00"), date(2026, 1, 5), bills(), debts(), Decimal("600.00"))
    total = sum(item["amount"] for item in result["allocations"])
    assert total == Decimal("2500.00")
    assert result["checks"]["allocations_sum_ok"] is True


def test_bills_coverage_failure_detected() -> None:
    result = compute_plan(Decimal("1250.00"), date(2026, 1, 1), bills(), debts(), Decimal("600.00"))
    assert result["checks"]["bills_covered_ok"] is False
    assert any("short by" in entry for entry in result["details"]["unfunded_items"])


def test_insufficient_funds_flags_buffer_failure() -> None:
    result = compute_plan(Decimal("220.00"), date(2026, 1, 5), bills(), debts(), Decimal("600.00"))
    assert result["checks"]["buffer_met_ok"] is False
    assert any("Buffer short" in entry for entry in result["details"]["unfunded_items"])
