"""사전 매칭 기반 경량 용어 세그먼터.

형태소 분석기 없이, 입력 문자열을 사전에 등록된 용어(및 동의어) 중 가장 긴 것부터
매칭해 나가는 최대 일치(maximum matching) 방식이다. F-103(물리명 자동 합성)의 기반이 되며,
사전에 없는 구간은 "미등록"으로 표시해 사용자가 직접 확정하도록 한다
(검토보고서 권고: "완전 자동 합성" 대신 "자동 추천 + 사용자 확정").
"""

import sqlite3

from pydantic import BaseModel

from app.core.dictionary.repository import list_terms
from app.models.dictionary import DictionarySource, DictionaryTerm


class MatchedSegment(BaseModel):
    text: str
    matched: bool
    term: DictionaryTerm | None = None


def build_term_index(conn: sqlite3.Connection) -> dict[str, DictionaryTerm]:
    """term/동의어 -> DictionaryTerm 매핑. custom이 standard보다 우선한다."""
    index: dict[str, DictionaryTerm] = {}

    for source in (DictionarySource.STANDARD, DictionarySource.CUSTOM):
        offset = 0
        while True:
            batch = list_terms(conn, source=source, limit=5000, offset=offset)
            if not batch:
                break
            for term in batch:
                index[term.term] = term
                for synonym in term.synonyms:
                    index[synonym] = term
            offset += len(batch)

    return index


def segment(text: str, index: dict[str, DictionaryTerm]) -> list[MatchedSegment]:
    """전방 최대 일치(forward maximum matching)로 문자열을 분해한다."""
    raw_segments: list[MatchedSegment] = []
    i = 0
    n = len(text)

    while i < n:
        matched_term: DictionaryTerm | None = None
        matched_text = ""

        for j in range(n, i, -1):
            candidate = text[i:j]
            if candidate in index:
                matched_term = index[candidate]
                matched_text = candidate
                break

        if matched_term:
            raw_segments.append(MatchedSegment(text=matched_text, matched=True, term=matched_term))
            i += len(matched_text)
        else:
            raw_segments.append(MatchedSegment(text=text[i], matched=False, term=None))
            i += 1

    return _merge_unmatched(raw_segments)


def _merge_unmatched(segments: list[MatchedSegment]) -> list[MatchedSegment]:
    """연속된 미등록 글자를 하나의 세그먼트로 합친다."""
    merged: list[MatchedSegment] = []
    for seg in segments:
        if not seg.matched and merged and not merged[-1].matched:
            merged[-1] = MatchedSegment(text=merged[-1].text + seg.text, matched=False, term=None)
        else:
            merged.append(seg)
    return merged
