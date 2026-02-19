"""Seed demo profile data."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Bill, Debt, Preference


def seed_demo_data(session: Session) -> None:
    if session.execute(select(Account.id)).first():
        return

    checking = Account(name="Main Checking", type="checking", currency="CAD", balance=Decimal("1200.00"))
    savings = Account(name="Emergency Savings", type="savings", currency="CAD", balance=Decimal("2500.00"))
    credit = Account(name="Rewards Card", type="credit", currency="CAD", balance=Decimal("-430.12"))
    session.add_all([checking, savings, credit])
    session.flush()

    bills = [
        Bill(name="Rent", amount=Decimal("1200.00"), cadence="monthly", due_day=1, autopay=True, pay_from_account_id=checking.id),
        Bill(name="Internet", amount=Decimal("85.00"), cadence="monthly", due_day=10, autopay=True, pay_from_account_id=checking.id),
        Bill(name="Phone", amount=Decimal("65.00"), cadence="monthly", due_day=20, autopay=True, pay_from_account_id=checking.id),
        Bill(name="Groceries", amount=Decimal("140.00"), cadence="weekly", due_day=None, autopay=False, pay_from_account_id=checking.id),
    ]
    debts = [
        Debt(name="Student Loan", balance=Decimal("8200.00"), apr=Decimal("4.2"), min_payment=Decimal("130.00"), pay_from_account_id=checking.id),
        Debt(name="Credit Card", balance=Decimal("1800.00"), apr=Decimal("21.99"), min_payment=Decimal("70.00"), pay_from_account_id=checking.id),
    ]
    pref = Preference(buffer_amount_per_paycheck=Decimal("600.00"), currency="CAD", notes="demo profile")

    session.add_all(bills + debts + [pref])
    session.commit()
