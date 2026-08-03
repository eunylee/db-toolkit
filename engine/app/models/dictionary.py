from enum import Enum

from pydantic import BaseModel


class DictionaryDataType(str, Enum):
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    NUMBER = "NUMBER"
    DATE = "DATE"
    UNKNOWN = "UNKNOWN"


class DictionarySource(str, Enum):
    STANDARD = "standard"
    CUSTOM = "custom"


class DictionaryTerm(BaseModel):
    term: str
    description: str = ""
    abbreviation: str
    domain_code: str = ""
    domain_class: str = ""
    data_type: DictionaryDataType = DictionaryDataType.UNKNOWN
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    storage_format: str = ""
    allowed_values: str = ""
    synonyms: list[str] = []
    source: DictionarySource = DictionarySource.STANDARD


class DictionaryImportResult(BaseModel):
    source: DictionarySource
    imported: int
    skipped: int
    errors: list[str] = []


class SplitCandidate(BaseModel):
    """미등록 구간을 문자종류 경계로 쪼갠 단어 후보 하나. 이미 사전에 있으면 그 정보를 함께 담는다."""

    term: str
    exists: bool
    abbreviation: str | None = None
    data_type: DictionaryDataType | None = None
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
