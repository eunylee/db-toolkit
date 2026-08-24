from app.core.naming.suggest import suggest_column, suggest_name
from app.models.dictionary import DictionaryDataType, DictionaryTerm

INDEX = {
    "고객": DictionaryTerm(term="고객", abbreviation="CUST", data_type=DictionaryDataType.VARCHAR, length=50),
    "등록번호": DictionaryTerm(
        term="등록번호", abbreviation="REG_NO", data_type=DictionaryDataType.VARCHAR, length=50, domain_code="번호V50"
    ),
    "주문일자": DictionaryTerm(
        term="주문일자", abbreviation="ORD_DT", data_type=DictionaryDataType.DATE, length=8
    ),
}


def test_suggest_name_fully_matched_joins_abbreviations():
    result = suggest_name("고객등록번호", INDEX)

    assert result.fully_matched is True
    assert result.physical_name_suggestion == "CUST_REG_NO"


def test_suggest_name_partial_match_has_no_full_suggestion():
    result = suggest_name("VIP고객등록번호", INDEX)

    assert result.fully_matched is False
    assert result.physical_name_suggestion is None
    assert any(not s.matched for s in result.segments)


def test_suggest_name_no_match_at_all():
    result = suggest_name("완전히모르는단어", INDEX)

    assert result.fully_matched is False
    assert result.physical_name_suggestion is None


def test_suggest_column_takes_data_type_from_last_matched_segment():
    # '고객'은 미등록 접두어 뒤에 오지만 '주문일자'가 마지막에 매칭되어 그 타입을 따른다
    result = suggest_column("VIP주문일자", INDEX)

    assert result.data_type == DictionaryDataType.DATE
    assert result.length == 8


def test_suggest_column_no_matched_segment_returns_unknown_type():
    result = suggest_column("완전히모르는단어", INDEX)

    assert result.data_type == DictionaryDataType.UNKNOWN
    assert result.length is None


def test_suggest_column_fully_matched_carries_length_from_last_segment():
    result = suggest_column("고객등록번호", INDEX)

    assert result.physical_name_suggestion == "CUST_REG_NO"
    assert result.data_type == DictionaryDataType.VARCHAR
    assert result.length == 50


def test_suggest_column_carries_domain_name_from_last_matched_segment():
    result = suggest_column("고객등록번호", INDEX)

    assert result.domain_name == "번호V50"


def test_suggest_column_no_matched_segment_has_empty_domain_name():
    result = suggest_column("완전히모르는단어", INDEX)

    assert result.domain_name == ""
