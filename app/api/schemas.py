"""Pydantic API contracts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class PaydayPlanRequest(BaseModel):
    paycheck_amount: Decimal = Field(..., gt=0)
    paycheck_date: date
    override_buffer_amount: Decimal | None = Field(default=None, ge=0)
    next_paycheck_date: date | None = None
    use_income_schedule: bool = True


class Allocation(BaseModel):
    bucket: str
    amount: Decimal


class Checks(BaseModel):
    allocations_sum_ok: bool
    bills_covered_ok: bool
    buffer_met_ok: bool
    min_cash_buffer_met_ok: bool


class PaydayPlanResponse(BaseModel):
    plan_id: str
    allocations: list[Allocation]
    checks: Checks
    summary: str
    safe_to_invest: str
    projected_end_cash: str
    starting_liquid_cash: str
    primary_surplus_target: str
    details: dict[str, object]
    inputs: dict[str, object]


class GenericStatus(BaseModel):
    status: str


class PlanRunListItem(BaseModel):
    plan_id: str
    created_at: str
    paycheck_date: str | None
    paycheck_amount: str | None
    checks_summary: str | None


class PlanRunListResponse(BaseModel):
    plans: list[PlanRunListItem]


class PlanRunDetailResponse(BaseModel):
    plan_id: str
    created_at: str
    paycheck_date: str | None
    paycheck_amount: str | None
    checks_summary: str | None
    plan: dict[str, object] | None
