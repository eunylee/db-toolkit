"""사전 CSV 임포터.

- 표준 사전(F-101): 행정안전부 공공데이터 공통표준용어 CSV의 고정 컬럼 형식을 그대로 파싱한다.
- 커스텀 사전(F-106): 고객사마다 컬럼명이 다르므로, 자주 쓰이는 한글/영문 별칭을 매핑해 유연하게 받는다.
"""

import csv
from io import StringIO
from typing import Iterable

from app.core.dictionary.domain_code import parse_domain_code
from app.models.dictionary import DictionarySource, DictionaryTerm

STANDARD_COLUMNS = {
    "term": "공통표준용어명",
    "description": "공통표준용어설명",
    "abbreviation": "공통표준용어영문약어명",
    "domain_code": "공통표준도메인명",
    "storage_format": "저장 형식",
    "allowed_values": "허용값",
    "synonyms": "용어 이음동의어 목록",
}

# 커스텀 사전은 회사마다 헤더명이 제각각이므로 자주 쓰는 별칭을 허용한다.
CUSTOM_COLUMN_ALIASES: dict[str, list[str]] = {
    "term": ["term", "용어", "논리명", "용어명"],
    "abbreviation": ["abbreviation", "약어", "영문약어", "물리명", "영문명"],
    "domain_code": ["domain_code", "도메인", "타입", "데이터타입"],
    "description": ["description", "설명", "정의"],
    "allowed_values": ["allowed_values", "허용값"],
    "storage_format": ["storage_format", "저장형식", "저장 형식"],
    "synonyms": ["synonyms", "동의어", "이음동의어"],
}


def _split_synonyms(raw: str) -> list[str]:
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def _read_csv_rows(content: str) -> Iterable[dict[str, str]]:
    yield from csv.DictReader(StringIO(content))


def parse_standard_csv(content: str) -> list[DictionaryTerm]:
    """행정안전부 공공데이터 공통표준용어 CSV(UTF-8, BOM 포함 가능)를 파싱한다."""
    if content.startswith("﻿"):
        content = content.lstrip("﻿")

    terms: list[DictionaryTerm] = []
    for row in _read_csv_rows(content):
        term = (row.get(STANDARD_COLUMNS["term"]) or "").strip()
        abbreviation = (row.get(STANDARD_COLUMNS["abbreviation"]) or "").strip()
        if not term or not abbreviation:
            continue

        domain_code = (row.get(STANDARD_COLUMNS["domain_code"]) or "").strip()
        parsed = parse_domain_code(domain_code)

        terms.append(
            DictionaryTerm(
                term=term,
                description=(row.get(STANDARD_COLUMNS["description"]) or "").strip(),
                abbreviation=abbreviation,
                domain_code=domain_code,
                domain_class=parsed.domain_class,
                data_type=parsed.data_type,
                length=parsed.length,
                precision=parsed.precision,
                scale=parsed.scale,
                storage_format=(row.get(STANDARD_COLUMNS["storage_format"]) or "").strip(),
                allowed_values=(row.get(STANDARD_COLUMNS["allowed_values"]) or "").strip(),
                synonyms=_split_synonyms(row.get(STANDARD_COLUMNS["synonyms"]) or ""),
                source=DictionarySource.STANDARD,
            )
        )
    return terms


def _resolve_custom_header_map(fieldnames: list[str]) -> dict[str, str]:
    """CSV 실제 헤더 -> 표준 필드명 매핑을 만든다. 인식 못한 헤더는 무시한다."""
    lower_fieldnames = {name.strip().lower(): name for name in fieldnames if name}
    resolved: dict[str, str] = {}
    for field, aliases in CUSTOM_COLUMN_ALIASES.items():
        for alias in aliases:
            actual = lower_fieldnames.get(alias.lower())
            if actual:
                resolved[field] = actual
                break
    return resolved


def parse_custom_csv(content: str) -> list[DictionaryTerm]:
    """고객사별 커스텀 전사 사전 CSV를 파싱한다.

    최소 term/abbreviation 컬럼(별칭 포함)이 있어야 하며, 없으면 ValueError.
    """
    if content.startswith("﻿"):
        content = content.lstrip("﻿")

    reader = csv.DictReader(StringIO(content))
    fieldnames = reader.fieldnames or []
    header_map = _resolve_custom_header_map(fieldnames)

    if "term" not in header_map or "abbreviation" not in header_map:
        raise ValueError(
            "커스텀 사전 CSV에 용어/약어 컬럼을 찾을 수 없습니다. "
            f"허용 헤더: term={CUSTOM_COLUMN_ALIASES['term']}, "
            f"abbreviation={CUSTOM_COLUMN_ALIASES['abbreviation']}"
        )

    terms: list[DictionaryTerm] = []
    for row in reader:
        term = (row.get(header_map["term"]) or "").strip()
        abbreviation = (row.get(header_map["abbreviation"]) or "").strip()
        if not term or not abbreviation:
            continue

        domain_code = (row.get(header_map.get("domain_code", "")) or "").strip()
        parsed = parse_domain_code(domain_code) if domain_code else None

        terms.append(
            DictionaryTerm(
                term=term,
                description=(row.get(header_map.get("description", "")) or "").strip(),
                abbreviation=abbreviation,
                domain_code=domain_code,
                domain_class=parsed.domain_class if parsed else "",
                data_type=parsed.data_type if parsed else "UNKNOWN",
                length=parsed.length if parsed else None,
                precision=parsed.precision if parsed else None,
                scale=parsed.scale if parsed else None,
                storage_format=(row.get(header_map.get("storage_format", "")) or "").strip(),
                allowed_values=(row.get(header_map.get("allowed_values", "")) or "").strip(),
                synonyms=_split_synonyms(row.get(header_map.get("synonyms", "")) or ""),
                source=DictionarySource.CUSTOM,
            )
        )
    return terms
