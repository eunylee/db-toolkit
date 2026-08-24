"""도메인 관리 API. 표준 도메인은 읽기 전용(표준 사전 임포트 시 자동 갱신), 커스텀만 CRUD 가능."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.core.domains.repository import (
    StandardDomainImmutableError,
    create_domain,
    delete_domain,
    list_domains,
    update_domain,
)
from app.models.domains import Domain

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[Domain])
def get_domains(query: str | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[Domain]:
    return list_domains(conn, query=query)


@router.post("", response_model=Domain)
def post_domain(domain: Domain, conn: sqlite3.Connection = Depends(get_db)) -> Domain:
    return create_domain(conn, domain)


@router.put("/{domain_name}", response_model=Domain)
def put_domain(domain_name: str, domain: Domain, conn: sqlite3.Connection = Depends(get_db)) -> Domain:
    try:
        return update_domain(conn, domain_name, domain)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StandardDomainImmutableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{domain_name}", status_code=204)
def delete_domain_endpoint(domain_name: str, conn: sqlite3.Connection = Depends(get_db)) -> None:
    try:
        delete_domain(conn, domain_name)
    except StandardDomainImmutableError as e:
        raise HTTPException(status_code=400, detail=str(e))
