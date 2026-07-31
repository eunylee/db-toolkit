from app.core.dictionary import matcher, repository
from app.models.dictionary import DictionaryDataType, DictionarySource, DictionaryTerm
from app.storage.db import get_connection, init_db


def _seeded_conn(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    repository.replace_terms(
        conn,
        [
            DictionaryTerm(term="고객", abbreviation="CUST", data_type=DictionaryDataType.VARCHAR),
            DictionaryTerm(term="주문", abbreviation="ORD", data_type=DictionaryDataType.VARCHAR),
            DictionaryTerm(term="번호", abbreviation="NO", data_type=DictionaryDataType.VARCHAR),
            DictionaryTerm(
                term="등록번호", abbreviation="REG_NO", data_type=DictionaryDataType.VARCHAR
            ),
        ],
        DictionarySource.STANDARD,
    )
    return conn


def test_segment_prefers_longest_match(tmp_path):
    conn = _seeded_conn(tmp_path)
    index = matcher.build_term_index(conn)

    segments = matcher.segment("고객등록번호", index)

    # '번호'가 아니라 더 긴 '등록번호'가 우선 매칭되어야 한다
    texts = [(s.text, s.matched) for s in segments]
    assert texts == [("고객", True), ("등록번호", True)]


def test_segment_marks_unregistered_gap(tmp_path):
    conn = _seeded_conn(tmp_path)
    index = matcher.build_term_index(conn)

    segments = matcher.segment("고객XX번호", index)

    texts = [(s.text, s.matched) for s in segments]
    assert texts == [("고객", True), ("XX", False), ("번호", True)]


def test_segment_returns_abbreviations_for_matched_segments(tmp_path):
    conn = _seeded_conn(tmp_path)
    index = matcher.build_term_index(conn)

    segments = matcher.segment("고객주문", index)

    assert [s.term.abbreviation for s in segments if s.matched] == ["CUST", "ORD"]


def test_segment_custom_overrides_standard_in_index(tmp_path):
    conn = _seeded_conn(tmp_path)
    repository.replace_terms(
        conn,
        [DictionaryTerm(term="고객", abbreviation="CLIENT", data_type=DictionaryDataType.VARCHAR)],
        DictionarySource.CUSTOM,
    )
    index = matcher.build_term_index(conn)

    segments = matcher.segment("고객", index)

    assert segments[0].term.abbreviation == "CLIENT"


def test_segment_empty_string_returns_no_segments(tmp_path):
    conn = _seeded_conn(tmp_path)
    index = matcher.build_term_index(conn)

    assert matcher.segment("", index) == []
