from pydantic import BaseModel

from app.core.dictionary.matcher import MatchedSegment
from app.models.dictionary import DictionaryDataType


class NameSuggestion(BaseModel):
    logical_name: str
    physical_name_suggestion: str | None
    fully_matched: bool
    segments: list[MatchedSegment]


class ColumnSuggestion(NameSuggestion):
    domain_name: str = ""
    data_type: DictionaryDataType = DictionaryDataType.UNKNOWN
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
