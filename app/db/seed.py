"""Seed demo profile data."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Bill, Debt, IncomeSchedule, Preference


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
        Bill(name="Groceries", amount=Decimal("140.00"), cadence="weekly", due_day=None, autopay=False, pay_from_account_id=checking.id, weekday_anchor=5),
    ]
    debts = [
        Debt(name="Student Loan", balance=Decimal("8200.00"), apr=Decimal("4.2"), min_payment=Decimal("130.00"), pay_from_account_id=checking.id),
        Debt(name="Credit Card", balance=Decimal("1800.00"), apr=Decimal("21.99"), min_payment=Decimal("70.00"), pay_from_account_id=checking.id),
    ]
    pref = Preference(
        buffer_amount_per_paycheck=Decimal("600.00"),
        min_cash_buffer=Decimal("2000.00"),
        primary_surplus_target="invest",
        currency="CAD",
        notes="demo profile",
    )
    schedule = IncomeSchedule(
        name="Paycheck",
        frequency="biweekly",
        next_pay_date="2026-01-05",
        typical_net_amount=Decimal("2390.43"),
    )

    session.add_all(bills + debts + [pref, schedule])
    session.commit()
