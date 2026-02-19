"""Pydantic request/response schemas for payday planning endpoints."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class PaydayPlanRequest(BaseModel):
    paycheck_amount: Decimal = Field(..., gt=0)
    paycheck_date: date
    override_buffer_amount: Decimal | None = Field(default=None, ge=0)


class AllocationItem(BaseModel):
    bucket: str
    amount: Decimal


class PlanChecks(BaseModel):
    allocations_sum_ok: bool
    bills_covered_ok: bool
    buffer_met_ok: bool


class PaydayPlanResponse(BaseModel):
    plan_id: str
    allocations: list[AllocationItem]
    checks: PlanChecks
    summary: str
    details: dict[str, object]


class SeedResponse(BaseModel):
    status: str
