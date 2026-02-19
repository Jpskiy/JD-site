"""Core domain models used by deterministic calculators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Bill:
    id: int
    name: str
    amount: Decimal
    cadence: str
    due_day: int | None
    autopay: bool


@dataclass(frozen=True)
class Debt:
    id: int
    name: str
    balance: Decimal
    apr: Decimal
    min_payment: Decimal


@dataclass(frozen=True)
class Preferences:
    id: int
    buffer_amount_per_paycheck: Decimal
    currency: str
    notes: str | None = None


@dataclass(frozen=True)
class DueBillFunding:
    bill_id: int
    bill_name: str
    cadence: str
    amount_due: Decimal
    amount_funded: Decimal
    fully_funded: bool


@dataclass(frozen=True)
class PaydayPlanResult:
    plan_id: str
    paycheck_date: date
    next_paycheck_date: date
    allocations: list[dict[str, Decimal]]
    checks: dict[str, bool]
    summary: str
    details: dict[str, object]
