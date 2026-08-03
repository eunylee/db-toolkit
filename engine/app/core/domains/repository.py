"""도메인 SQLite 리포지토리.

표준 도메인(source=standard)은 /dictionary/import/standard 때 통째로 재생성된다(읽기 전용).
커스텀 도메인(source=custom)만 사용자가 직접 만들고 수정·삭제할 수 있다.
"""

import sqlite3

from app.models.dictionary import DictionaryDataType, DictionarySource
from app.models.domains import Domain


class StandardDomainImmutableError(Exception):
    """표준 도메인은 수정/삭제할 수 없을 때 발생."""


def _row_to_domain(row: sqlite3.Row) -> Domain:
    return Domain(
        id=row["id"],
        name=row["name"],
        data_type=DictionaryDataType(row["data_type"]),
        length=row["length"],
        precision=row["precision"],
        scale=row["scale"],
        source=DictionarySource(row["source"]),
        usage_count=row["usage_count"],
    )


_LIST_SQL = """
SELECT d.id, d.name, d.data_type, d.length, d.precision, d.scale, d.source,
       COALESCE(t.cnt, 0) AS usage_count
FROM domains d
LEFT JOIN (
    SELECT domain_code, COUNT(*) AS cnt FROM dictionary_terms GROUP BY domain_code
) t ON t.domain_code = d.name
"""


def list_domains(conn: sqlite3.Connection, query: str | None = None) -> list[Domain]:
    sql = _LIST_SQL
    params: list[str] = []
    if query:
        sql += " WHERE d.name LIKE ?"
        params.append(f"%{query}%")
    sql += " ORDER BY usage_count DESC, d.name"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_domain(r) for r in rows]


def get_domain(conn: sqlite3.Connection, domain_id: int) -> Domain | None:
    row = conn.execute(_LIST_SQL + " WHERE d.id = ?", (domain_id,)).fetchone()
    return _row_to_domain(row) if row else None


def replace_standard_domains(conn: sqlite3.Connection, domains: list[Domain]) -> None:
    with conn:
        conn.execute("DELETE FROM domains WHERE source = 'standard'")
        conn.executemany(
            "INSERT INTO domains (name, data_type, length, precision, scale, source) "
            "VALUES (?, ?, ?, ?, ?, 'standard')",
            [(d.name, d.data_type.value, d.length, d.precision, d.scale) for d in domains],
        )


def create_domain(conn: sqlite3.Connection, domain: Domain) -> Domain:
    with conn:
        cur = conn.execute(
            "INSERT INTO domains (name, data_type, length, precision, scale, source) "
            "VALUES (?, ?, ?, ?, ?, 'custom')",
            (domain.name, domain.data_type.value, domain.length, domain.precision, domain.scale),
        )
    return get_domain(conn, cur.lastrowid)  # type: ignore[return-value]


def update_domain(conn: sqlite3.Connection, domain_id: int, domain: Domain) -> Domain:
    existing = get_domain(conn, domain_id)
    if existing is None:
        raise ValueError(f"도메인 id={domain_id}를 찾을 수 없습니다.")
    if existing.source == DictionarySource.STANDARD:
        raise StandardDomainImmutableError("표준 도메인은 수정할 수 없습니다.")

    with conn:
        conn.execute(
            "UPDATE domains SET name = ?, data_type = ?, length = ?, precision = ?, scale = ? WHERE id = ?",
            (domain.name, domain.data_type.value, domain.length, domain.precision, domain.scale, domain_id),
        )
    return get_domain(conn, domain_id)  # type: ignore[return-value]


def delete_domain(conn: sqlite3.Connection, domain_id: int) -> None:
    existing = get_domain(conn, domain_id)
    if existing is None:
        return
    if existing.source == DictionarySource.STANDARD:
        raise StandardDomainImmutableError("표준 도메인은 삭제할 수 없습니다.")

    with conn:
        conn.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
