"""Create local SQLite schema and apply lightweight dev migrations."""

from sqlalchemy import inspect, text

from app.db.models import Base
from app.db.session import engine


def _add_column_if_missing(table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns(table_name)} if inspector.has_table(table_name) else set()
    if column_name in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Lightweight dev migration strategy for sqlite: ALTER table to add newly required columns.
    _add_column_if_missing("plan_runs", "paycheck_date", "paycheck_date VARCHAR(10)")
    _add_column_if_missing("plan_runs", "paycheck_amount", "paycheck_amount NUMERIC(12,2)")
    _add_column_if_missing("plan_runs", "checks_summary", "checks_summary TEXT")
    _add_column_if_missing("plan_runs", "plan_json", "plan_json TEXT")


if __name__ == "__main__":
    init_db()
    print("Initialized database schema.")
