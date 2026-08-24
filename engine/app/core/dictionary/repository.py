"""사전(용어=복합 업무용어) SQLite 리포지토리. 테이블: tb_terms.

커스텀 사전(F-106)은 표준 사전(F-101)보다 항상 우선순위가 높다 (조회 시 custom 먼저 조회).

DB 컬럼명(term_nm, abbreviation_cd 등)과 API/Pydantic 필드명(term, abbreviation 등)은
의도적으로 분리되어 있다 — DB 스키마는 우리 자신의 명명 규칙(단어+도메인 접미사, 예약어
회피)을 따르고, API 계약은 프런트엔드 변경 없이 안정적으로 유지하기 위함이다.
"""

import json
import sqlite3

from app.models.dictionary import DictionaryDataType, DictionaryImportResult, DictionarySource, DictionaryTerm


def _row_to_term(row: sqlite3.Row) -> DictionaryTerm:
    return DictionaryTerm(
        term=row["term_nm"],
        description=row["term_cn"],
        abbreviation=row["abbreviation_cd"],
        domain_code=row["domain_cd"],
        domain_class=row["domain_class_nm"],
        data_type=DictionaryDataType(row["data_type_cd"]),
        length=row["length_no"],
        precision=row["precision_no"],
        scale=row["scale_no"],
        storage_format=row["storage_format_cn"],
        allowed_values=row["allowed_value_cn"],
        synonyms=json.loads(row["synonym_list_cn"]),
        source=DictionarySource(row["source_cd"]),
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
        conn.execute("DELETE FROM tb_terms WHERE source_cd = ?", (source.value,))
        conn.executemany(
            """
            INSERT INTO tb_terms (
                term_nm, term_cn, abbreviation_cd, domain_cd, domain_class_nm,
                data_type_cd, length_no, precision_no, scale_no, storage_format_cn,
                allowed_value_cn, synonym_list_cn, source_cd
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


def upsert_term(conn: sqlite3.Connection, term: DictionaryTerm) -> DictionaryTerm:
    """용어 하나만 등록/수정한다. replace_terms와 달리 같은 source의 다른 기존 용어를 지우지 않는다."""
    with conn:
        conn.execute(
            """
            INSERT INTO tb_terms (
                term_nm, term_cn, abbreviation_cd, domain_cd, domain_class_nm,
                data_type_cd, length_no, precision_no, scale_no, storage_format_cn,
                allowed_value_cn, synonym_list_cn, source_cd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(term_nm, source_cd) DO UPDATE SET
                term_cn = excluded.term_cn,
                abbreviation_cd = excluded.abbreviation_cd,
                domain_cd = excluded.domain_cd,
                domain_class_nm = excluded.domain_class_nm,
                data_type_cd = excluded.data_type_cd,
                length_no = excluded.length_no,
                precision_no = excluded.precision_no,
                scale_no = excluded.scale_no,
                storage_format_cn = excluded.storage_format_cn,
                allowed_value_cn = excluded.allowed_value_cn,
                synonym_list_cn = excluded.synonym_list_cn
            """,
            (
                term.term,
                term.description,
                term.abbreviation,
                term.domain_code,
                term.domain_class,
                term.data_type.value,
                term.length,
                term.precision,
                term.scale,
                term.storage_format,
                term.allowed_values,
                json.dumps(term.synonyms, ensure_ascii=False),
                term.source.value,
            ),
        )
    return term


def lookup_term(conn: sqlite3.Connection, term: str) -> DictionaryTerm | None:
    """정확 일치(용어명 또는 동의어) 조회. custom 사전이 standard보다 우선한다."""
    for source in (DictionarySource.CUSTOM, DictionarySource.STANDARD):
        row = conn.execute(
            "SELECT * FROM tb_terms WHERE source_cd = ? AND term_nm = ?",
            (source.value, term),
        ).fetchone()
        if row:
            return _row_to_term(row)

    # 동의어 매칭은 전체 스캔이 필요 (사전 규모상 로컬 1인 사용에는 충분히 빠름)
    for source in (DictionarySource.CUSTOM, DictionarySource.STANDARD):
        rows = conn.execute("SELECT * FROM tb_terms WHERE source_cd = ?", (source.value,)).fetchall()
        for row in rows:
            if term in json.loads(row["synonym_list_cn"]):
                return _row_to_term(row)

    return None


def list_terms(
    conn: sqlite3.Connection,
    query: str | None = None,
    source: DictionarySource | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DictionaryTerm]:
    sql = "SELECT * FROM tb_terms WHERE 1=1"
    params: list[str | int] = []

    if query:
        sql += " AND (term_nm LIKE ? OR abbreviation_cd LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if source:
        sql += " AND source_cd = ?"
        params.append(source.value)

    sql += " ORDER BY term_nm LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_term(r) for r in rows]


def find_terms_containing(conn: sqlite3.Connection, substring: str) -> list[DictionaryTerm]:
    """용어명에 substring이 포함된 모든 레코드(표준+커스텀). 약어 추천 통계용."""
    rows = conn.execute("SELECT * FROM tb_terms WHERE term_nm LIKE ?", (f"%{substring}%",)).fetchall()
    return [_row_to_term(r) for r in rows]


def count_terms(conn: sqlite3.Connection, source: DictionarySource | None = None) -> int:
    if source:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM tb_terms WHERE source_cd = ?", (source.value,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as c FROM tb_terms").fetchone()
    return row["c"]
