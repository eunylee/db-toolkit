import pytest

from app.core.words import repository
from app.models.dictionary import DictionaryDataType, DictionarySource
from app.models.words import Word
from app.storage.db import get_connection, init_db


def _conn(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    return conn


def _word(word="고객", abbreviation="CUST", data_type=DictionaryDataType.VARCHAR, length=50, is_domain_word=True):
    return Word(
        word=word,
        abbreviation=abbreviation,
        is_domain_word=is_domain_word,
        data_type=data_type,
        length=length,
        source=DictionarySource.CUSTOM,
    )


def test_create_and_list_word(tmp_path):
    conn = _conn(tmp_path)
    created = repository.create_word(conn, _word())

    words = repository.list_words(conn)

    assert created.source == DictionarySource.CUSTOM
    assert len(words) == 1
    assert words[0].word == "고객"


def test_create_word_upserts_on_conflict(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word(abbreviation="CUST"))
    updated = repository.create_word(conn, _word(abbreviation="CUSTOMER"))

    assert updated.abbreviation == "CUSTOMER"
    assert len(repository.list_words(conn)) == 1


def test_lookup_word_prefers_custom(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word())

    found = repository.lookup_word(conn, "고객")

    assert found is not None
    assert found.abbreviation == "CUST"


def test_lookup_word_not_found_returns_none(tmp_path):
    conn = _conn(tmp_path)

    assert repository.lookup_word(conn, "없는단어") is None


def test_list_words_filters_by_query(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word(word="고객"))
    repository.create_word(conn, _word(word="주문", abbreviation="ORD"))

    results = repository.list_words(conn, query="고객")

    assert len(results) == 1
    assert results[0].word == "고객"


def test_update_custom_word(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word(abbreviation="CUST"))

    updated = repository.update_word(conn, "고객", _word(abbreviation="CUSTOMER"))

    assert updated.abbreviation == "CUSTOMER"


def test_update_missing_word_raises_value_error(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        repository.update_word(conn, "없는단어", _word())


def test_delete_custom_word(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word())

    repository.delete_word(conn, "고객")

    assert repository.list_words(conn) == []


def test_delete_missing_word_is_noop(tmp_path):
    conn = _conn(tmp_path)

    repository.delete_word(conn, "없는단어")


def test_non_domain_word_strips_type_info_on_create(tmp_path):
    """도메인 단어가 아니면 타입이 실제로 안 쓰이므로 저장 시 비워둔다."""
    conn = _conn(tmp_path)
    created = repository.create_word(conn, _word(word="외부", data_type=DictionaryDataType.VARCHAR, length=100, is_domain_word=False))

    assert created.is_domain_word is False
    assert created.data_type == DictionaryDataType.UNKNOWN
    assert created.length is None


def test_domain_word_keeps_type_info(tmp_path):
    conn = _conn(tmp_path)
    created = repository.create_word(conn, _word(word="번호", data_type=DictionaryDataType.VARCHAR, length=20, is_domain_word=True))

    assert created.is_domain_word is True
    assert created.data_type == DictionaryDataType.VARCHAR
    assert created.length == 20


def test_can_toggle_word_to_domain_word_via_update(tmp_path):
    conn = _conn(tmp_path)
    repository.create_word(conn, _word(word="번호", is_domain_word=False, data_type=DictionaryDataType.UNKNOWN, length=None))

    updated = repository.update_word(
        conn, "번호", _word(word="번호", data_type=DictionaryDataType.VARCHAR, length=20, is_domain_word=True)
    )

    assert updated.is_domain_word is True
    assert updated.length == 20
