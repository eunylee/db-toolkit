"""단어 하나의 약어를 사전 전체의 사용 패턴에서 통계적으로 추천한다.

형태소 분석이나 번역이 아니라, 이미 등록된 용어 중 이 단어가 접두/접미로 들어간
용어들의 약어에서 대응하는 토큰(언더스코어 구분)의 빈도를 세는 것뿐이다.
예: "참조내용"->RFRNC_CN, "참조번호"->RFRNC_NO 처럼 "참조"가 접두인 용어들은
약어 첫 토큰이 대부분 RFRNC이므로, "참조"의 약어로 RFRNC를 추천할 수 있다.
"""

from collections import Counter

from pydantic import BaseModel

from app.models.dictionary import DictionaryTerm


class AbbreviationSuggestion(BaseModel):
    token: str
    count: int


def suggest_abbreviations(word: str, matches: list[DictionaryTerm], limit: int = 3) -> list[AbbreviationSuggestion]:
    counter: Counter[str] = Counter()

    for m in matches:
        if not m.abbreviation:
            continue
        tokens = m.abbreviation.split("_")
        if not tokens:
            continue
        if m.term.startswith(word):
            counter[tokens[0]] += 1
        if m.term.endswith(word):
            counter[tokens[-1]] += 1

    return [AbbreviationSuggestion(token=token, count=count) for token, count in counter.most_common(limit)]
