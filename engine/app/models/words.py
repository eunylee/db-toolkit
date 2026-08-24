from pydantic import BaseModel

from app.models.dictionary import DictionaryDataType, DictionarySource


class Word(BaseModel):
    """단어(word)+용어(term) 분리: word는 더 쪼갤 수 없는 최소 재사용 단위다.

    tb_words가 저장소. name(word)+source가 자연키다 (surrogate id 없음).

    is_domain_word: 이 단어가 타입을 결정하는 "도메인 단어"인지(예: 명/번호/여부/코드) 여부.
    완성된 용어(term)는 항상 도메인 단어로 끝나야 하며(F-103 물리명 조합의 마지막 매칭
    구간에서 타입을 가져오므로), 도메인 단어가 아닌 단어(예: 고객/외부 등 수식어)는
    타입이 실제로 쓰이지 않으므로 도메인 지정이 필요 없다.
    """

    word: str
    abbreviation: str
    is_domain_word: bool = False
    domain_name: str = ""
    data_type: DictionaryDataType = DictionaryDataType.UNKNOWN
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    source: DictionarySource = DictionarySource.CUSTOM


class SplitCandidate(BaseModel):
    """미등록 구간을 문자종류 경계로 쪼갠 단어 후보 하나. 이미 tb_words에 있으면 그 정보를 담는다."""

    term: str
    exists: bool
    is_domain_word: bool = False
    abbreviation: str | None = None
    data_type: DictionaryDataType | None = None
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
