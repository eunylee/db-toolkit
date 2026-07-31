"""F-101/F-106 사전 API. 화면(UI)은 이 엔드포인트만 호출한다."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import get_db
from app.core.dictionary import matcher
from app.core.dictionary.importer import parse_custom_csv, parse_standard_csv
from app.core.dictionary.repository import count_terms, list_terms, lookup_term, replace_terms
from app.models.dictionary import DictionaryImportResult, DictionarySource, DictionaryTerm

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

STANDARD_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "dictionary" / "standard_terms.csv"


@router.post("/import/standard", response_model=DictionaryImportResult)
def import_standard(conn: sqlite3.Connection = Depends(get_db)) -> DictionaryImportResult:
    """번들된 행정안전부 공공데이터 공통표준용어 시드를 SQLite로 (재)적재한다."""
    content = STANDARD_SEED_PATH.read_text(encoding="utf-8-sig")
    terms = parse_standard_csv(content)
    return replace_terms(conn, terms, DictionarySource.STANDARD)


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


@router.get("/segment", response_model=list[matcher.MatchedSegment])
def get_segment(text: str, conn: sqlite3.Connection = Depends(get_db)) -> list[matcher.MatchedSegment]:
    index = matcher.build_term_index(conn)
    return matcher.segment(text, index)
