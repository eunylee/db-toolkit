"""테이블 설계 모델 API (F-103 확정 결과 저장, 이후 ERD/F-104a의 기반 데이터)."""

from fastapi import APIRouter, HTTPException

from app.core.tables.repository import get_table, load_tables, save_table
from app.models.tables import Table

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=list[Table])
def list_tables() -> list[Table]:
    return load_tables()


@router.post("", response_model=Table)
def create_or_update_table(table: Table) -> Table:
    return save_table(table)


@router.get("/{logical_name}", response_model=Table)
def get_table_by_name(logical_name: str) -> Table:
    table = get_table(logical_name)
    if table is None:
        raise HTTPException(status_code=404, detail=f"테이블 '{logical_name}'을(를) 찾을 수 없습니다.")
    return table
