"""사전 SQLite 리포지토리.

커스텀 사전(F-106)은 표준 사전(F-101)보다 항상 우선순위가 높다 (조회 시 custom 먼저 조회).
"""

import json
import sqlite3

from app.models.dictionary import DictionaryDataType, DictionaryImportResult, DictionarySource, DictionaryTerm


def _row_to_term(row: sqlite3.Row) -> DictionaryTerm:
    return DictionaryTerm(
        term=row["term"],
        description=row["description"],
        abbreviation=row["abbreviation"],
        domain_code=row["domain_code"],
        domain_class=row["domain_class"],
        data_type=DictionaryDataType(row["data_type"]),
        length=row["length"],
        precision=row["precision"],
        scale=row["scale"],
        storage_format=row["storage_format"],
        allowed_values=row["allowed_values"],
        synonyms=json.loads(row["synonyms"]),
        source=DictionarySource(row["source"]),
    )


def replace_terms(
    conn: sqlite3.Connection, terms: list[DictionaryTerm], source: DictionarySource
) -> DictionaryImportResult:
    """해당 source의 기존 사전을 통째로 새 데이터로 교체한다 (전체 재수입 방식)."""
    errors: list[str] = []
    seen_terms: set[str] = set()
    deduped: list[DictionaryTerm] = []
    skipped = 0

    for term in terms:
        if term.term in seen_terms:
            skipped += 1
            continue
        seen_terms.add(term.term)
        deduped.append(term)

    with conn:
        conn.execute("DELETE FROM dictionary_terms WHERE source = ?", (source.value,))
        conn.executemany(
            """
            INSERT INTO dictionary_terms (
                term, description, abbreviation, domain_code, domain_class,
                data_type, length, precision, scale, storage_format,
                allowed_values, synonyms, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    t.term,
                    t.description,
                    t.abbreviation,
                    t.domain_code,
                    t.domain_class,
                    t.data_type.value,
                    t.length,
                    t.precision,
                    t.scale,
                    t.storage_format,
                    t.allowed_values,
                    json.dumps(t.synonyms, ensure_ascii=False),
                    source.value,
                )
                for t in deduped
            ],
        )

    return DictionaryImportResult(source=source, imported=len(deduped), skipped=skipped, errors=errors)


def lookup_term(conn: sqlite3.Connection, term: str) -> DictionaryTerm | None:
    """정확 일치(용어명 또는 동의어) 조회. custom 사전이 standard보다 우선한다."""
    for source in (DictionarySource.CUSTOM, DictionarySource.STANDARD):
        row = conn.execute(
            "SELECT * FROM dictionary_terms WHERE source = ? AND term = ?",
            (source.value, term),
        ).fetchone()
        if row:
            return _row_to_term(row)

    # 동의어 매칭은 전체 스캔이 필요 (사전 규모상 로컬 1인 사용에는 충분히 빠름)
    for source in (DictionarySource.CUSTOM, DictionarySource.STANDARD):
        rows = conn.execute("SELECT * FROM dictionary_terms WHERE source = ?", (source.value,)).fetchall()
        for row in rows:
            if term in json.loads(row["synonyms"]):
                return _row_to_term(row)

    return None


def list_terms(
    conn: sqlite3.Connection,
    query: str | None = None,
    source: DictionarySource | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DictionaryTerm]:
    sql = "SELECT * FROM dictionary_terms WHERE 1=1"
    params: list[str | int] = []

    if query:
        sql += " AND (term LIKE ? OR abbreviation LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if source:
        sql += " AND source = ?"
        params.append(source.value)

    sql += " ORDER BY term LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_term(r) for r in rows]


def count_terms(conn: sqlite3.Connection, source: DictionarySource | None = None) -> int:
    if source:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM dictionary_terms WHERE source = ?", (source.value,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as c FROM dictionary_terms").fetchone()
    return row["c"]
