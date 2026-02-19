"""Pure domain data structures."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Bill:
    id: int
    name: str
    amount: Decimal
    cadence: str
    due_day: int | None
    autopay: bool
    weekday_anchor: int | None = None


@dataclass(frozen=True)
class Debt:
    id: int
    name: str
    balance: Decimal
    apr: Decimal
    min_payment: Decimal
