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


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_import_standard_loads_bundled_seed(client):
    resp = client.post("/dictionary/import/standard")

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "standard"
    assert body["imported"] > 10000


def test_import_custom_csv(client):
    csv_content = "term,abbreviation\n주문상태,ORD_STAT\n"
    resp = client.post(
        "/dictionary/import/custom",
        files={"file": ("custom.csv", csv_content, "text/csv")},
    )

    assert resp.status_code == 200
    assert resp.json()["imported"] == 1


def test_import_custom_csv_invalid_columns_returns_422(client):
    csv_content = "foo,bar\n1,2\n"
    resp = client.post(
        "/dictionary/import/custom",
        files={"file": ("bad.csv", csv_content, "text/csv")},
    )

    assert resp.status_code == 422


def test_lookup_after_import(client):
    csv_content = "term,abbreviation\n주문상태,ORD_STAT\n"
    client.post("/dictionary/import/custom", files={"file": ("custom.csv", csv_content, "text/csv")})

    resp = client.get("/dictionary/lookup", params={"term": "주문상태"})

    assert resp.status_code == 200
    assert resp.json()["abbreviation"] == "ORD_STAT"


def test_lookup_missing_term_returns_404(client):
    resp = client.get("/dictionary/lookup", params={"term": "없는용어"})
    assert resp.status_code == 404


def test_terms_listing_pagination(client):
    csv_content = "term,abbreviation\n용어1,T1\n용어2,T2\n"
    client.post("/dictionary/import/custom", files={"file": ("custom.csv", csv_content, "text/csv")})

    resp = client.get("/dictionary/terms", params={"source": "custom", "limit": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1


def test_abbreviation_suggestions_from_bundled_standard_seed(client):
    """실제 행안부 표준 데이터에서 "참조"가 접두인 용어들은 대부분 RFRNC로 시작한다."""
    client.post("/dictionary/import/standard")

    resp = client.get("/dictionary/abbreviation-suggestions", params={"word": "참조"})

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["token"] == "RFRNC"
    assert body[0]["count"] >= 5


def test_abbreviation_suggestions_empty_for_unknown_word(client):
    resp = client.get("/dictionary/abbreviation-suggestions", params={"word": "완전히새로운단어"})

    assert resp.status_code == 200
    assert resp.json() == []


def test_segment_endpoint(client):
    csv_content = "term,abbreviation\n고객,CUST\n주문,ORD\n"
    client.post("/dictionary/import/custom", files={"file": ("custom.csv", csv_content, "text/csv")})

    resp = client.get("/dictionary/segment", params={"text": "고객주문"})

    assert resp.status_code == 200
    segments = resp.json()
    assert [s["text"] for s in segments] == ["고객", "주문"]
