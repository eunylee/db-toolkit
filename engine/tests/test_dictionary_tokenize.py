from app.core.dictionary.tokenize import split_into_word_candidates


def test_splits_hangul_and_latin_runs():
    assert split_into_word_candidates("외부URL") == ["외부", "URL"]


def test_single_hangul_word_stays_whole():
    assert split_into_word_candidates("고객명") == ["고객명"]


def test_single_latin_word_stays_whole():
    assert split_into_word_candidates("URL") == ["URL"]


def test_latin_and_digits_stay_in_one_run():
    assert split_into_word_candidates("URL2") == ["URL2"]


def test_multiple_alternating_runs():
    assert split_into_word_candidates("고객URL이력") == ["고객", "URL", "이력"]


def test_ignores_separators():
    assert split_into_word_candidates("외부_URL-이력") == ["외부", "URL", "이력"]


def test_empty_string_returns_empty_list():
    assert split_into_word_candidates("") == []
