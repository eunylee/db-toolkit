import pytest

from app.core.dictionary.domain_code import parse_domain_code
from app.models.dictionary import DictionaryDataType


@pytest.mark.parametrize(
    "domain_code, expected_class, expected_type, expected_length, expected_precision, expected_scale",
    [
        ("명V100", "명", DictionaryDataType.VARCHAR, 100, None, None),
        ("여부C1", "여부", DictionaryDataType.CHAR, 1, None, None),
        ("수N15,4", "수", DictionaryDataType.NUMBER, None, 15, 4),
        ("연월일시분초D", "연월일시분초", DictionaryDataType.DATE, None, None, None),
        ("율N5,2", "율", DictionaryDataType.NUMBER, None, 5, 2),
    ],
)
def test_parse_domain_code(domain_code, expected_class, expected_type, expected_length, expected_precision, expected_scale):
    parsed = parse_domain_code(domain_code)

    assert parsed.domain_class == expected_class
    assert parsed.data_type == expected_type
    assert parsed.length == expected_length
    assert parsed.precision == expected_precision
    assert parsed.scale == expected_scale


def test_parse_domain_code_unrecognized_format_falls_back_to_unknown():
    parsed = parse_domain_code("이상한형식_123")

    assert parsed.data_type == DictionaryDataType.UNKNOWN


def test_parse_domain_code_empty_string():
    parsed = parse_domain_code("")

    assert parsed.data_type == DictionaryDataType.UNKNOWN
    assert parsed.domain_class == ""
