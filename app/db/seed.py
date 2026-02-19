"""Seed utilities for loading a sample profile for demos/tests."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Bill, Debt, Preferences


def seed_demo_data(session: Session) -> None:
    existing = session.execute(select(Account.id)).first()
    if existing:
        return

    checking = Account(name="Main Checking", type="checking", currency="USD", balance=Decimal("1800.00"))
    savings = Account(name="Emergency Savings", type="savings", currency="USD", balance=Decimal("2500.00"))
    credit = Account(name="Rewards Credit", type="credit", currency="USD", balance=Decimal("-420.00"))
    session.add_all([checking, savings, credit])
    session.flush()

    session.add_all(
        [
            Bill(name="Rent", amount=Decimal("1200.00"), cadence="monthly", due_day=1, autopay=True, pay_from_account_id=checking.id),
            Bill(name="Internet", amount=Decimal("80.00"), cadence="monthly", due_day=10, autopay=True, pay_from_account_id=checking.id),
            Bill(name="Phone", amount=Decimal("55.00"), cadence="monthly", due_day=18, autopay=True, pay_from_account_id=checking.id),
            Bill(name="Groceries", amount=Decimal("120.00"), cadence="weekly", due_day=None, autopay=False, pay_from_account_id=checking.id),
        ]
    )

    session.add_all(
        [
            Debt(name="Student Loan", balance=Decimal("8200.00"), apr=Decimal("4.20"), min_payment=Decimal("130.00"), pay_from_account_id=checking.id),
            Debt(name="Credit Card", balance=Decimal("1460.00"), apr=Decimal("21.99"), min_payment=Decimal("65.00"), pay_from_account_id=checking.id),
        ]
    )

    session.add(Preferences(buffer_amount_per_paycheck=Decimal("600.00"), currency="USD", notes="Starter profile"))
    session.commit()
