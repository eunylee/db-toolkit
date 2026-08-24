import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app
from app.storage.db import get_connection, init_db


@pytest.fixture()
def client(tmp_path):
    def _override_db():
        conn = get_connection(tmp_path / "test.db")
        init_db(conn)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _payload(name="이메일주소", data_type="VARCHAR", length=255):
    return {"name": name, "data_type": data_type, "length": length, "precision": None, "scale": None}


def test_create_and_list_domain(client):
    resp = client.post("/domains", json=_payload())
    assert resp.status_code == 200
    assert resp.json()["source"] == "custom"

    resp = client.get("/domains")
    assert len(resp.json()) == 1


def test_search_domains_by_query(client):
    client.post("/domains", json=_payload(name="이메일주소"))
    client.post("/domains", json=_payload(name="전화번호"))

    resp = client.get("/domains", params={"query": "이메일"})

    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "이메일주소"


def test_update_domain(client):
    client.post("/domains", json=_payload(length=255))

    resp = client.put("/domains/이메일주소", json=_payload(length=320))

    assert resp.status_code == 200
    assert resp.json()["length"] == 320


def test_update_missing_domain_returns_404(client):
    resp = client.put("/domains/없는도메인", json=_payload(name="없는도메인"))
    assert resp.status_code == 404


def test_update_standard_domain_returns_400(client):
    client.post("/dictionary/import/standard")
    standard_domain = client.get("/domains").json()[0]
    assert standard_domain["source"] == "standard"

    resp = client.put(f"/domains/{standard_domain['name']}", json=_payload(name=standard_domain["name"]))

    assert resp.status_code == 400


def test_delete_domain(client):
    client.post("/domains", json=_payload())

    resp = client.delete("/domains/이메일주소")

    assert resp.status_code == 204
    assert client.get("/domains").json() == []


def test_delete_standard_domain_returns_400(client):
    client.post("/dictionary/import/standard")
    standard_domain = client.get("/domains").json()[0]

    resp = client.delete(f"/domains/{standard_domain['name']}")

    assert resp.status_code == 400


def test_importing_standard_dictionary_bootstraps_domains(client):
    resp = client.post("/dictionary/import/standard")
    assert resp.status_code == 200

    domains = client.get("/domains").json()

    assert len(domains) == 123
    assert all(d["source"] == "standard" for d in domains)
