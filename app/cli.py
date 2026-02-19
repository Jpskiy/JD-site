"""CLI entrypoint for local payday demo."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal

from app.agent.payday_agent import generate_payday_plan
from app.db.init_db import init_db
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal


def run_demo(amount: Decimal, paycheck_date: date, next_paycheck_date: date | None = None) -> None:
    init_db()
    with SessionLocal() as session:
        seed_demo_data(session)
        plan = generate_payday_plan(
            session,
            amount,
            paycheck_date,
            next_paycheck_date=next_paycheck_date,
        )
    print(json.dumps(plan, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Finance Co-Pilot CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo-payday", help="Run payday plan demo")
    demo.add_argument("--amount", required=True, type=Decimal)
    demo.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")
    demo.add_argument("--next-paycheck-date", default=None, help="Optional YYYY-MM-DD period end")

    args = parser.parse_args()

    if args.command == "demo-payday":
        next_pay = date.fromisoformat(args.next_paycheck_date) if args.next_paycheck_date else None
        run_demo(args.amount, date.fromisoformat(args.date), next_paycheck_date=next_pay)


if __name__ == "__main__":
    main()
