from pydantic import BaseModel

from app.models.dictionary import DictionaryDataType


class Column(BaseModel):
    logical_name: str
    physical_name: str
    data_type: DictionaryDataType = DictionaryDataType.UNKNOWN
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    is_pk: bool = False
    note: str = ""


class Table(BaseModel):
    logical_name: str
    physical_name: str
    columns: list[Column] = []
