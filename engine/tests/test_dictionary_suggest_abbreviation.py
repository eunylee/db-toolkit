from app.core.dictionary.suggest_abbreviation import suggest_abbreviations
from app.models.dictionary import DictionaryTerm


def _term(term, abbreviation):
    return DictionaryTerm(term=term, abbreviation=abbreviation)


def test_suggests_most_common_prefix_token():
    matches = [
        _term("참조내용", "RFRNC_CN"),
        _term("참조번호", "RFRNC_NO"),
        _term("참조여부", "RFRNC_YN"),
        _term("참조자명", "RFPR_NM"),
    ]

    suggestions = suggest_abbreviations("참조", matches)

    assert suggestions[0].token == "RFRNC"
    assert suggestions[0].count == 3


def test_suggests_most_common_suffix_token():
    matches = [
        _term("검색키워드명", "SRCH_KYWD_NM"),
        _term("영문키워드명", "ENG_KYWD_NM"),
        _term("키워드명", "KYWD_NM"),
    ]

    suggestions = suggest_abbreviations("키워드", matches)

    # 접두(첫 토큰) 집계에서는 "키워드명"만 KYWD로 매칭되고, 나머지는 접두가 아니므로 집계 안 됨
    assert any(s.token == "KYWD" for s in suggestions)


def test_returns_empty_list_when_no_matches():
    assert suggest_abbreviations("없는단어", []) == []


def test_ignores_terms_without_abbreviation():
    matches = [_term("참조내용", "")]

    assert suggest_abbreviations("참조", matches) == []


def test_limits_results():
    matches = [
        _term("참조A", "AAA_X"),
        _term("참조B", "BBB_X"),
        _term("참조C", "CCC_X"),
        _term("참조D", "DDD_X"),
    ]

    suggestions = suggest_abbreviations("참조", matches, limit=2)

    assert len(suggestions) == 2
