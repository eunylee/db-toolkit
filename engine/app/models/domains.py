from pydantic import BaseModel

from app.models.dictionary import DictionaryDataType, DictionarySource


class Domain(BaseModel):
    id: int | None = None
    name: str
    data_type: DictionaryDataType
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    source: DictionarySource = DictionarySource.CUSTOM
    usage_count: int = 0
