import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

from app.api.main import app


def test_plan_persistence_and_history_endpoints() -> None:
    client = TestClient(app)

    seed = client.post('/seed/demo')
    assert seed.status_code == 200

    create = client.post(
        '/plan/payday',
        json={
            'paycheck_amount': 2390.43,
            'paycheck_date': '2026-01-05',
            'next_paycheck_date': '2026-01-12',
            'use_income_schedule': True,
        },
    )
    assert create.status_code == 200
    created_body = create.json()
    plan_id = created_body['plan_id']

    assert 'safe_to_invest' in created_body
    assert 'projected_end_cash' in created_body
    assert 'starting_liquid_cash' in created_body
    assert 'primary_surplus_target' in created_body
    assert created_body['details']['period_end'] == '2026-01-12'

    history = client.get('/plans')
    assert history.status_code == 200
    plans = history.json()['plans']
    assert any(item['plan_id'] == plan_id for item in plans)

    detail = client.get(f'/plans/{plan_id}')
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body['plan_id'] == plan_id
    assert detail_body['plan']['checks']['allocations_sum_ok'] is True
    assert detail_body['plan']['inputs']['paycheck_amount'] == '2390.43'
