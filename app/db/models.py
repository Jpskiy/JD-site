"""SQLAlchemy models for local-first finance app."""

from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CAD")
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cadence: Mapped[str] = mapped_column(String(20), nullable=False)
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    autopay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pay_from_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    weekday_anchor: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    apr: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    min_payment: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    pay_from_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buffer_amount_per_paycheck: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=600)
    min_cash_buffer: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=2000)
    primary_surplus_target: Mapped[str] = mapped_column(String(30), nullable=False, default="invest")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CAD")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class IncomeSchedule(Base):
    __tablename__ = "income_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="biweekly")
    next_pay_date: Mapped[str] = mapped_column(String(10), nullable=False)
    typical_net_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class PlanRun(Base):
    __tablename__ = "plan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paycheck_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    paycheck_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    checks_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
