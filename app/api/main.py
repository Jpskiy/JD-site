"""FastAPI app for Finance Co-Pilot v1."""

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.agent.payday_agent import generate_payday_plan
from app.api.schemas import GenericStatus, PaydayPlanRequest, PaydayPlanResponse
from app.db.init_db import init_db
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal

app = FastAPI(title="Finance Co-Pilot", version="1.0.0")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/seed/demo", response_model=GenericStatus)
def seed_demo(db: Session = Depends(get_db)) -> GenericStatus:
    seed_demo_data(db)
    return GenericStatus(status="ok")


@app.post("/plan/payday", response_model=PaydayPlanResponse)
def payday_plan(payload: PaydayPlanRequest, db: Session = Depends(get_db)) -> PaydayPlanResponse:
    result = generate_payday_plan(
        session=db,
        paycheck_amount=payload.paycheck_amount,
        paycheck_date=payload.paycheck_date,
        override_buffer_amount=payload.override_buffer_amount,
    )
    return PaydayPlanResponse.model_validate(result)
