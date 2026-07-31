"""F-103 물리명 자동 합성 API."""

import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_db
from app.core.dictionary import matcher
from app.core.naming.suggest import suggest_column
from app.models.naming import ColumnSuggestion

router = APIRouter(prefix="/naming", tags=["naming"])


class SuggestColumnsRequest(BaseModel):
    logical_names: list[str]


@router.post("/suggest", response_model=list[ColumnSuggestion])
def suggest_columns(body: SuggestColumnsRequest, conn: sqlite3.Connection = Depends(get_db)) -> list[ColumnSuggestion]:
    index = matcher.build_term_index(conn)
    return [suggest_column(name, index) for name in body.logical_names]
