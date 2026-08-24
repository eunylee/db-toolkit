"""도메인 SQLite 리포지토리. 테이블: tb_domains.

표준 도메인(source=standard)은 /dictionary/import/standard 때 통째로 재생성된다(읽기 전용).
커스텀 도메인(source=custom)만 사용자가 직접 만들고 수정·삭제할 수 있다.

PK는 surrogate id가 아니라 (domain_nm, source_cd) 자연키다. 수정/삭제는 항상 custom
네임스페이스 안에서만 이뤄지므로 도메인 이름을 식별자로 쓴다 (표준 도메인과 이름이
겹치더라도 mutation 쿼리는 source_cd='custom' 조건으로 자동 격리된다).
"""

import sqlite3

from app.models.dictionary import DictionaryDataType, DictionarySource
from app.models.domains import Domain


class StandardDomainImmutableError(Exception):
    """표준 도메인은 수정/삭제할 수 없을 때 발생."""


def _row_to_domain(row: sqlite3.Row) -> Domain:
    return Domain(
        name=row["domain_nm"],
        data_type=DictionaryDataType(row["data_type_cd"]),
        length=row["length_no"],
        precision=row["precision_no"],
        scale=row["scale_no"],
        source=DictionarySource(row["source_cd"]),
        usage_count=row["usage_count"],
    )


_LIST_SQL = """
SELECT d.domain_nm, d.data_type_cd, d.length_no, d.precision_no, d.scale_no, d.source_cd,
       COALESCE(t.cnt, 0) AS usage_count
FROM tb_domains d
LEFT JOIN (
    SELECT domain_cd, COUNT(*) AS cnt FROM tb_terms GROUP BY domain_cd
) t ON t.domain_cd = d.domain_nm
"""


def list_domains(conn: sqlite3.Connection, query: str | None = None) -> list[Domain]:
    sql = _LIST_SQL
    params: list[str] = []
    if query:
        sql += " WHERE d.domain_nm LIKE ?"
        params.append(f"%{query}%")
    sql += " ORDER BY usage_count DESC, d.domain_nm"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_domain(r) for r in rows]


def get_domain_by_name(conn: sqlite3.Connection, name: str, source: DictionarySource | None = None) -> Domain | None:
    """이름으로 도메인을 조회한다. source를 안 주면 custom을 standard보다 우선한다."""
    sources = (source,) if source else (DictionarySource.CUSTOM, DictionarySource.STANDARD)
    for s in sources:
        row = conn.execute(_LIST_SQL + " WHERE d.domain_nm = ? AND d.source_cd = ?", (name, s.value)).fetchone()
        if row:
            return _row_to_domain(row)
    return None


def replace_standard_domains(conn: sqlite3.Connection, domains: list[Domain]) -> None:
    with conn:
        conn.execute("DELETE FROM tb_domains WHERE source_cd = 'standard'")
        conn.executemany(
            "INSERT INTO tb_domains (domain_nm, data_type_cd, length_no, precision_no, scale_no, source_cd) "
            "VALUES (?, ?, ?, ?, ?, 'standard')",
            [(d.name, d.data_type.value, d.length, d.precision, d.scale) for d in domains],
        )


def create_domain(conn: sqlite3.Connection, domain: Domain) -> Domain:
    with conn:
        conn.execute(
            "INSERT INTO tb_domains (domain_nm, data_type_cd, length_no, precision_no, scale_no, source_cd) "
            "VALUES (?, ?, ?, ?, ?, 'custom')",
            (domain.name, domain.data_type.value, domain.length, domain.precision, domain.scale),
        )
    return get_domain_by_name(conn, domain.name, DictionarySource.CUSTOM)  # type: ignore[return-value]


def update_domain(conn: sqlite3.Connection, name: str, domain: Domain) -> Domain:
    existing = get_domain_by_name(conn, name, DictionarySource.CUSTOM)
    if existing is None:
        if get_domain_by_name(conn, name, DictionarySource.STANDARD) is not None:
            raise StandardDomainImmutableError("표준 도메인은 수정할 수 없습니다.")
        raise ValueError(f"커스텀 도메인 '{name}'을(를) 찾을 수 없습니다.")

    with conn:
        conn.execute(
            "UPDATE tb_domains SET domain_nm = ?, data_type_cd = ?, length_no = ?, precision_no = ?, scale_no = ? "
            "WHERE domain_nm = ? AND source_cd = 'custom'",
            (domain.name, domain.data_type.value, domain.length, domain.precision, domain.scale, name),
        )
    return get_domain_by_name(conn, domain.name, DictionarySource.CUSTOM)  # type: ignore[return-value]


def delete_domain(conn: sqlite3.Connection, name: str) -> None:
    existing = get_domain_by_name(conn, name, DictionarySource.CUSTOM)
    if existing is None:
        if get_domain_by_name(conn, name, DictionarySource.STANDARD) is not None:
            raise StandardDomainImmutableError("표준 도메인은 삭제할 수 없습니다.")
        return

    with conn:
        conn.execute("DELETE FROM tb_domains WHERE domain_nm = ? AND source_cd = 'custom'", (name,))
