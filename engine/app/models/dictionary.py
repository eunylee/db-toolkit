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
