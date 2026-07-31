"""F-103 물리명 자동 합성.

검토보고서 권고에 따라 "완전 자동 합성"이 아니라 "자동 추천 + 사용자 확정" 구조다.
사전에 등록된 구간만 이어붙여 물리명을 제안하고, 미등록 구간이 하나라도 있으면
완전한 제안을 만들지 않는다(뜻을 모르는 한글을 임의로 로마자화하지 않음).

데이터타입은 마지막으로 매칭된 구간에서 가져온다. 한글 복합명사는 보통 끝 단어가
핵심(예: "고객등록번호"의 핵심은 "번호")이라, 앞부분이 미등록이어도 끝 단어가 매칭되면
데이터타입은 추천할 수 있다.
"""

from app.core.dictionary.matcher import MatchedSegment, segment
from app.models.dictionary import DictionaryDataType, DictionaryTerm
from app.models.naming import ColumnSuggestion, NameSuggestion


def suggest_name(logical_name: str, index: dict[str, DictionaryTerm]) -> NameSuggestion:
    segments = segment(logical_name, index)
    fully_matched = len(segments) > 0 and all(s.matched for s in segments)
    physical_name_suggestion = "_".join(s.term.abbreviation for s in segments) if fully_matched else None

    return NameSuggestion(
        logical_name=logical_name,
        physical_name_suggestion=physical_name_suggestion,
        fully_matched=fully_matched,
        segments=segments,
    )


def suggest_column(logical_name: str, index: dict[str, DictionaryTerm]) -> ColumnSuggestion:
    name_suggestion = suggest_name(logical_name, index)
    last_matched = _last_matched_segment(name_suggestion.segments)
    term = last_matched.term if last_matched else None

    return ColumnSuggestion(
        **name_suggestion.model_dump(),
        data_type=term.data_type if term else DictionaryDataType.UNKNOWN,
        length=term.length if term else None,
        precision=term.precision if term else None,
        scale=term.scale if term else None,
    )


def _last_matched_segment(segments: list[MatchedSegment]) -> MatchedSegment | None:
    matched = [s for s in segments if s.matched]
    return matched[-1] if matched else None
