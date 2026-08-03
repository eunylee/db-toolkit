"""미등록 구간을 사전 등록용 단어 후보로 분리한다.

형태소 분석기 없이, 문자 종류(한글 덩어리 vs 영문/숫자 덩어리) 경계로만 나눈다.
예: "외부URL" -> ["외부", "URL"]. 이렇게 해야 "외부"와 "URL"이 각각 재사용 가능한
단어로 사전에 남아, 나중에 "관리자URL" 같은 다른 조합에도 "URL"이 매칭된다.
전체를 통짜 복합어 하나로 등록하면 이런 재사용이 불가능해진다.
"""

import re

_WORD_PATTERN = re.compile(r"[가-힣]+|[A-Za-z0-9]+")


def split_into_word_candidates(text: str) -> list[str]:
    return _WORD_PATTERN.findall(text)
