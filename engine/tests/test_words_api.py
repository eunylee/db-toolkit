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


def _payload(word="고객", abbreviation="CUST", data_type="VARCHAR", length=50, is_domain_word=True):
    return {
        "word": word,
        "abbreviation": abbreviation,
        "is_domain_word": is_domain_word,
        "domain_name": "",
        "data_type": data_type,
        "length": length,
        "precision": None,
        "scale": None,
    }


def test_create_word_forces_custom_source(client):
    resp = client.post("/words", json={**_payload(), "source": "standard"})

    assert resp.status_code == 200
    assert resp.json()["source"] == "custom"


def test_create_word_upserts_without_wiping_other_words(client):
    client.post("/words", json=_payload(word="고객", abbreviation="CUST"))
    client.post("/words", json=_payload(word="등록번호", abbreviation="REG_NO"))

    resp = client.get("/words")

    assert len(resp.json()) == 2


def test_lookup_word(client):
    client.post("/words", json=_payload())

    resp = client.get("/words/lookup", params={"word": "고객"})

    assert resp.status_code == 200
    assert resp.json()["abbreviation"] == "CUST"


def test_lookup_missing_word_returns_404(client):
    resp = client.get("/words/lookup", params={"word": "없는단어"})
    assert resp.status_code == 404


def test_split_candidates_marks_existing_and_missing_words(client):
    client.post("/words", json=_payload(word="외부", abbreviation="EXT"))

    resp = client.get("/words/split-candidates", params={"text": "외부URL"})

    assert resp.status_code == 200
    body = resp.json()
    assert body[0] == {
        "term": "외부",
        "exists": True,
        "is_domain_word": True,
        "abbreviation": "EXT",
        "data_type": "VARCHAR",
        "length": 50,
        "precision": None,
        "scale": None,
    }
    assert body[1]["term"] == "URL"
    assert body[1]["exists"] is False


def test_non_domain_word_strips_type_on_register(client):
    resp = client.post("/words", json=_payload(word="외부", data_type="VARCHAR", length=100, is_domain_word=False))

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_domain_word"] is False
    assert body["data_type"] == "UNKNOWN"
    assert body["length"] is None


def test_update_word(client):
    client.post("/words", json=_payload())

    resp = client.put("/words/고객", json=_payload(abbreviation="CUSTOMER"))

    assert resp.status_code == 200
    assert resp.json()["abbreviation"] == "CUSTOMER"


def test_update_missing_word_returns_404(client):
    resp = client.put("/words/없는단어", json=_payload(word="없는단어"))
    assert resp.status_code == 404


def test_delete_word(client):
    client.post("/words", json=_payload())

    resp = client.delete("/words/고객")

    assert resp.status_code == 204
    assert client.get("/words").json() == []
