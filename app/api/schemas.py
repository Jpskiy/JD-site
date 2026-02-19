"""Pydantic API contracts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class PaydayPlanRequest(BaseModel):
    paycheck_amount: Decimal = Field(..., gt=0)
    paycheck_date: date
    override_buffer_amount: Decimal | None = Field(default=None, ge=0)


class Allocation(BaseModel):
    bucket: str
    amount: Decimal


class Checks(BaseModel):
    allocations_sum_ok: bool
    bills_covered_ok: bool
    buffer_met_ok: bool


class PaydayPlanResponse(BaseModel):
    plan_id: str
    allocations: list[Allocation]
    checks: Checks
    summary: str
    details: dict[str, object]


class GenericStatus(BaseModel):
    status: str
