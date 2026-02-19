# AGENTS Guardrails

- Money calculations must be deterministic in `/app/calculators`.
- The agent orchestrator in `/app/agent` must not invent numbers.
- Use `Decimal` internally; only accept floats at API boundary, then convert to `Decimal` immediately.
- All allocation outputs must sum to paycheck within 1 cent.
- Any changes to budgeting rules must include/adjust tests.
- Do not log sensitive financial data.
