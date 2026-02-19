"""FastAPI app entrypoint for Finance Co-Pilot."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.agent.payday_agent import run_payday_plan
from app.api.schemas import PaydayPlanRequest, PaydayPlanResponse, SeedResponse
from app.db.init_db import init_db
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal

app = FastAPI(title="Finance Co-Pilot", version="0.1.0")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/seed/demo", response_model=SeedResponse)
def seed_demo(db: Session = Depends(get_db)) -> SeedResponse:
    seed_demo_data(db)
    return SeedResponse(status="ok")


@app.post("/plan/payday", response_model=PaydayPlanResponse)
def create_payday_plan(payload: PaydayPlanRequest, db: Session = Depends(get_db)) -> PaydayPlanResponse:
    result = run_payday_plan(
        session=db,
        paycheck_amount=payload.paycheck_amount,
        paycheck_date=payload.paycheck_date,
        override_buffer_amount=payload.override_buffer_amount,
    )
    return PaydayPlanResponse.model_validate(result)
