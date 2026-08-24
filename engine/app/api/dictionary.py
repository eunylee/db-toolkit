"""F-101/F-106 사전(용어=복합 업무용어) API. 화면(UI)은 이 엔드포인트만 호출한다.

단어(word) 등록/조회는 app/api/words.py로 분리되어 있다 (tb_words 참고).
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import get_db
from app.core.dictionary import matcher
from app.core.dictionary.importer import parse_custom_csv, parse_standard_csv
from app.core.dictionary.repository import count_terms, find_terms_containing, list_terms, lookup_term, replace_terms
from app.core.dictionary.suggest_abbreviation import AbbreviationSuggestion, suggest_abbreviations
from app.core.domains.derive import derive_domains_from_terms
from app.core.domains.repository import replace_standard_domains
from app.models.dictionary import DictionaryImportResult, DictionarySource, DictionaryTerm

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

STANDARD_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "dictionary" / "standard_terms.csv"


@router.post("/import/standard", response_model=DictionaryImportResult)
def import_standard(conn: sqlite3.Connection = Depends(get_db)) -> DictionaryImportResult:
    """번들된 행정안전부 공공데이터 공통표준용어 시드를 SQLite로 (재)적재한다.

    같은 시드에서 재사용 가능한 도메인 목록(표준 도메인)도 함께 갱신한다.
    """
    content = STANDARD_SEED_PATH.read_text(encoding="utf-8-sig")
    terms = parse_standard_csv(content)
    result = replace_terms(conn, terms, DictionarySource.STANDARD)
    replace_standard_domains(conn, derive_domains_from_terms(terms))
    return result


@router.post("/import/custom", response_model=DictionaryImportResult)
async def import_custom(file: UploadFile, conn: sqlite3.Connection = Depends(get_db)) -> DictionaryImportResult:
    """고객사별 커스텀 전사 사전 CSV를 업로드해 표준 사전보다 우선하는 매핑으로 등록한다."""
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV는 UTF-8 인코딩이어야 합니다.")

    try:
        terms = parse_custom_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return replace_terms(conn, terms, DictionarySource.CUSTOM)


@router.get("/terms")
def get_terms(
    query: str | None = None,
    source: DictionarySource | None = None,
    limit: int = 50,
    offset: int = 0,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    items = list_terms(conn, query=query, source=source, limit=limit, offset=offset)
    total = count_terms(conn, source=source)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/lookup", response_model=DictionaryTerm)
def get_lookup(term: str, conn: sqlite3.Connection = Depends(get_db)) -> DictionaryTerm:
    result = lookup_term(conn, term)
    if result is None:
        raise HTTPException(status_code=404, detail=f"'{term}'에 대한 사전 매핑을 찾을 수 없습니다.")
    return result


@router.get("/abbreviation-suggestions", response_model=list[AbbreviationSuggestion])
def get_abbreviation_suggestions(word: str, conn: sqlite3.Connection = Depends(get_db)) -> list[AbbreviationSuggestion]:
    """이 단어가 접두/접미로 들어간 기존 용어들의 약어 패턴에서 통계적으로 추천안을 뽑는다.

    번역이나 형태소 분석이 아니라 단순 빈도 집계다 (예: "참조내용"->RFRNC_CN,
    "참조번호"->RFRNC_NO 처럼 "참조"가 접두인 용어들의 약어 첫 토큰이 대부분 RFRNC).
    """
    matches = find_terms_containing(conn, word)
    return suggest_abbreviations(word, matches)


@router.get("/segment", response_model=list[matcher.MatchedSegment])
def get_segment(text: str, conn: sqlite3.Connection = Depends(get_db)) -> list[matcher.MatchedSegment]:
    index = matcher.build_term_index(conn)
    return matcher.segment(text, index)
