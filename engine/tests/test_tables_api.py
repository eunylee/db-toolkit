import pytest
from fastapi.testclient import TestClient

from app.core.tables import repository
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "DEFAULT_WORKSPACE_MODEL_PATH", tmp_path / "model.yaml")
    with TestClient(app) as c:
        yield c


def _table_payload(name="고객", physical="CUST"):
    return {
        "logical_name": name,
        "physical_name": physical,
        "columns": [
            {
                "logical_name": "고객번호",
                "physical_name": "CUST_NO",
                "data_type": "VARCHAR",
                "length": 50,
                "is_pk": True,
                "note": "",
            }
        ],
    }


def test_create_table(client):
    resp = client.post("/tables", json=_table_payload())

    assert resp.status_code == 200
    assert resp.json()["logical_name"] == "고객"


def test_list_tables_after_create(client):
    client.post("/tables", json=_table_payload())

    resp = client.get("/tables")

    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_table_by_name(client):
    client.post("/tables", json=_table_payload())

    resp = client.get("/tables/고객")

    assert resp.status_code == 200
    assert resp.json()["columns"][0]["is_pk"] is True


def test_get_missing_table_returns_404(client):
    resp = client.get("/tables/없는테이블")

    assert resp.status_code == 404


def test_create_table_twice_overwrites(client):
    client.post("/tables", json=_table_payload(physical="CUST"))
    client.post("/tables", json=_table_payload(physical="CUST_V2"))

    resp = client.get("/tables/고객")

    assert resp.json()["physical_name"] == "CUST_V2"
