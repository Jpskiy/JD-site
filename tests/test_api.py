import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

from app.api.main import app


def test_seed_and_plan_endpoint_round_trip() -> None:
    client = TestClient(app)

    seed = client.post('/seed/demo')
    assert seed.status_code == 200

    resp = client.post(
        '/plan/payday',
        json={
            'paycheck_amount': '2390.43',
            'paycheck_date': '2026-01-05',
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 'plan_id' in body
    assert len(body['allocations']) == 4
    assert body['checks']['allocations_sum_ok'] is True
