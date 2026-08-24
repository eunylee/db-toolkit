from pydantic import BaseModel

from app.models.dictionary import DictionaryDataType, DictionarySource


class Domain(BaseModel):
    """도메인 이름(name)+source가 자연키다 (surrogate id 없음, tb_domains 참고)."""

    name: str
    data_type: DictionaryDataType
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    source: DictionarySource = DictionarySource.CUSTOM
    usage_count: int = 0
