from app.core.dictionary import repository
from app.models.dictionary import DictionaryDataType, DictionarySource, DictionaryTerm
from app.storage.db import get_connection, init_db


def _conn(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    return conn


def _term(term, abbr, source=DictionarySource.STANDARD, synonyms=None):
    return DictionaryTerm(
        term=term,
        abbreviation=abbr,
        data_type=DictionaryDataType.VARCHAR,
        length=100,
        synonyms=synonyms or [],
        source=source,
    )


def test_replace_terms_inserts_and_counts(tmp_path):
    conn = _conn(tmp_path)
    result = repository.replace_terms(conn, [_term("고객명", "CUST_NM")], DictionarySource.STANDARD)

    assert result.imported == 1
    assert repository.count_terms(conn, DictionarySource.STANDARD) == 1


def test_replace_terms_dedupes_within_same_source(tmp_path):
    conn = _conn(tmp_path)
    result = repository.replace_terms(
        conn,
        [_term("고객명", "CUST_NM"), _term("고객명", "CUST_NM_DUP")],
        DictionarySource.STANDARD,
    )

    assert result.imported == 1
    assert result.skipped == 1


def test_replace_terms_is_a_full_reimport(tmp_path):
    """같은 source로 다시 replace하면 이전 데이터는 사라진다 (증분이 아닌 전체 교체)."""
    conn = _conn(tmp_path)
    repository.replace_terms(conn, [_term("A", "A_CODE")], DictionarySource.STANDARD)
    repository.replace_terms(conn, [_term("B", "B_CODE")], DictionarySource.STANDARD)

    assert repository.count_terms(conn, DictionarySource.STANDARD) == 1
    assert repository.lookup_term(conn, "A") is None
    assert repository.lookup_term(conn, "B") is not None


def test_lookup_term_prefers_custom_over_standard(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_terms(conn, [_term("고객명", "CUST_NM")], DictionarySource.STANDARD)
    repository.replace_terms(conn, [_term("고객명", "CLIENT_NAME")], DictionarySource.CUSTOM)

    found = repository.lookup_term(conn, "고객명")

    assert found.abbreviation == "CLIENT_NAME"
    assert found.source == DictionarySource.CUSTOM


def test_lookup_term_matches_synonym(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_terms(
        conn, [_term("고객명", "CUST_NM", synonyms=["거래처명"])], DictionarySource.STANDARD
    )

    found = repository.lookup_term(conn, "거래처명")

    assert found is not None
    assert found.abbreviation == "CUST_NM"


def test_lookup_term_not_found_returns_none(tmp_path):
    conn = _conn(tmp_path)

    assert repository.lookup_term(conn, "없는용어") is None


def test_list_terms_filters_by_query_and_source(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_terms(
        conn, [_term("고객명", "CUST_NM"), _term("고객번호", "CUST_NO")], DictionarySource.STANDARD
    )

    results = repository.list_terms(conn, query="고객명")

    assert len(results) == 1
    assert results[0].term == "고객명"
