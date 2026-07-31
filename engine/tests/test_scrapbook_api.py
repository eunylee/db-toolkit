import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_parse_endpoint(client):
    resp = client.post("/scrapbook/parse", json={"raw_text": "a\tb\nc\td"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["rows"] == [["a", "b"], ["c", "d"]]
    assert body["row_count"] == 2
    assert body["column_count"] == 2


def test_parse_endpoint_empty_text(client):
    resp = client.post("/scrapbook/parse", json={"raw_text": ""})

    assert resp.status_code == 200
    assert resp.json()["rows"] == []
