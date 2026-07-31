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


def test_suggest_endpoint_uses_custom_dictionary(client):
    client.post(
        "/dictionary/import/custom",
        files={"file": ("d.csv", "term,abbreviation\n고객,CUST\n등록번호,REG_NO\n", "text/csv")},
    )

    resp = client.post("/naming/suggest", json={"logical_names": ["고객등록번호", "모르는단어"]})

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["physical_name_suggestion"] == "CUST_REG_NO"
    assert body[0]["fully_matched"] is True
    assert body[1]["physical_name_suggestion"] is None
    assert body[1]["fully_matched"] is False
