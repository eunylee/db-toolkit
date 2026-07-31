import csv
import io

import pytest

from app.core.dictionary.importer import parse_custom_csv, parse_standard_csv
from app.models.dictionary import DictionaryDataType, DictionarySource
from app.storage.db import DEFAULT_DB_PATH

STANDARD_HEADER = (
    "공통표준용어명,공통표준용어설명,공통표준용어영문약어명,공통표준도메인명,허용값,"
    "저장 형식,표현 형식,행정표준코드명,소관기관명,용어 이음동의어 목록,제정차수,"
    "개정구분명(폐기 또는 변경),개정항목,개정사유"
)


def _standard_row(term, desc, abbr, domain, storage_format="", synonyms=""):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="")
    writer.writerow([term, desc, abbr, domain, "", storage_format, "", "", "", synonyms, "1차", "", "", ""])
    return buf.getvalue()


def test_parse_standard_csv_basic():
    content = STANDARD_HEADER + "\n" + _standard_row("고객명", "고객의 이름", "CUST_NM", "명V100") + "\n"

    terms = parse_standard_csv(content)

    assert len(terms) == 1
    t = terms[0]
    assert t.term == "고객명"
    assert t.abbreviation == "CUST_NM"
    assert t.data_type == DictionaryDataType.VARCHAR
    assert t.length == 100
    assert t.source == DictionarySource.STANDARD


def test_parse_standard_csv_skips_rows_without_term_or_abbreviation():
    content = STANDARD_HEADER + "\n" + _standard_row("", "설명만 있음", "", "명V100") + "\n"

    terms = parse_standard_csv(content)

    assert terms == []


def test_parse_standard_csv_parses_synonyms():
    content = (
        STANDARD_HEADER
        + "\n"
        + _standard_row("고객명", "설명", "CUST_NM", "명V100", synonyms="거래처명, 고객성명")
        + "\n"
    )

    terms = parse_standard_csv(content)

    assert terms[0].synonyms == ["거래처명", "고객성명"]


def test_parse_standard_csv_handles_bom():
    content = "﻿" + STANDARD_HEADER + "\n" + _standard_row("고객명", "설명", "CUST_NM", "명V100") + "\n"

    terms = parse_standard_csv(content)

    assert len(terms) == 1


def test_parse_custom_csv_with_korean_headers():
    content = "논리명,물리명,도메인\n주문일자,ORD_DT,연월일C8\n"

    terms = parse_custom_csv(content)

    assert len(terms) == 1
    assert terms[0].term == "주문일자"
    assert terms[0].abbreviation == "ORD_DT"
    assert terms[0].source == DictionarySource.CUSTOM
    assert terms[0].data_type == DictionaryDataType.CHAR


def test_parse_custom_csv_with_english_headers():
    content = "term,abbreviation\ncustom term,CUST_TERM\n"

    terms = parse_custom_csv(content)

    assert terms[0].term == "custom term"
    assert terms[0].abbreviation == "CUST_TERM"


def test_parse_custom_csv_missing_required_columns_raises():
    content = "foo,bar\n1,2\n"

    with pytest.raises(ValueError):
        parse_custom_csv(content)


def test_bundled_standard_seed_parses_successfully():
    """실제 번들 시드 CSV(행안부 공통표준용어)가 깨지지 않고 다량 파싱되는지 확인."""
    seed_path = DEFAULT_DB_PATH.parent.parent / "dictionary" / "standard_terms.csv"
    content = seed_path.read_text(encoding="utf-8-sig")

    terms = parse_standard_csv(content)

    assert len(terms) > 10000
    sample = next(t for t in terms if t.term == "API명")
    assert sample.abbreviation == "API_NM"
    assert sample.data_type == DictionaryDataType.VARCHAR
    assert sample.length == 300
