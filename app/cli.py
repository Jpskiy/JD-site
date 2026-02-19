"""CLI helpers for demoing payday planning locally."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal

from app.agent.payday_agent import run_payday_plan
from app.db.init_db import init_db
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal


def demo_payday(amount: Decimal, paycheck_date: date) -> None:
    init_db()
    with SessionLocal() as session:
        seed_demo_data(session)
        plan = run_payday_plan(session=session, paycheck_amount=amount, paycheck_date=paycheck_date)
    print(json.dumps(plan, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Finance Co-Pilot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo-payday", help="Run payday planner against sample profile")
    demo.add_argument("--amount", required=True, type=Decimal, help="Paycheck amount")
    demo.add_argument("--date", default=date.today().isoformat(), help="Paycheck date YYYY-MM-DD")

    args = parser.parse_args()

    if args.command == "demo-payday":
        demo_payday(amount=args.amount, paycheck_date=date.fromisoformat(args.date))


if __name__ == "__main__":
    main()
