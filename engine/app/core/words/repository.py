"""단어(word) SQLite 리포지토리. 테이블: tb_words.

용어(terms, tb_terms)와 분리된 최소 재사용 단위. 표준 단어 시드가 없어(행안부 CSV는
이미 완성된 복합용어만 제공) source='standard' 행은 현재 비어 있고, 전부 사용자가
"미등록 단어를 사전에 추가" 흐름에서 custom으로 등록한다. 그래도 향후 표준 단어
시드가 추가될 경우를 대비해 도메인(domains.py)과 동일하게 표준/커스텀 구분과
불변성 규칙을 그대로 둔다.
"""

import sqlite3

from app.models.dictionary import DictionaryDataType, DictionarySource
from app.models.words import Word


class StandardWordImmutableError(Exception):
    """표준 단어는 수정/삭제할 수 없을 때 발생."""


def _row_to_word(row: sqlite3.Row) -> Word:
    return Word(
        word=row["word_nm"],
        abbreviation=row["abbreviation_cd"],
        is_domain_word=row["domain_word_yn"] == "Y",
        domain_name=row["domain_nm"],
        data_type=DictionaryDataType(row["data_type_cd"]),
        length=row["length_no"],
        precision=row["precision_no"],
        scale=row["scale_no"],
        source=DictionarySource(row["source_cd"]),
    )


def _normalize(word: Word) -> Word:
    """도메인 단어가 아니면 타입 정보를 실제로 안 쓰므로 저장 시점에 비워둔다."""
    if word.is_domain_word:
        return word
    return word.model_copy(
        update={"domain_name": "", "data_type": DictionaryDataType.UNKNOWN, "length": None, "precision": None, "scale": None}
    )


def list_words(
    conn: sqlite3.Connection,
    query: str | None = None,
    source: DictionarySource | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Word]:
    sql = "SELECT * FROM tb_words WHERE 1=1"
    params: list[str | int] = []

    if query:
        sql += " AND (word_nm LIKE ? OR abbreviation_cd LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if source:
        sql += " AND source_cd = ?"
        params.append(source.value)

    sql += " ORDER BY word_nm LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_word(r) for r in rows]


def lookup_word(conn: sqlite3.Connection, word: str) -> Word | None:
    """정확 일치 조회. custom이 standard보다 우선한다."""
    for source in (DictionarySource.CUSTOM, DictionarySource.STANDARD):
        row = conn.execute(
            "SELECT * FROM tb_words WHERE source_cd = ? AND word_nm = ?", (source.value, word)
        ).fetchone()
        if row:
            return _row_to_word(row)
    return None


def get_word_by_name(conn: sqlite3.Connection, name: str, source: DictionarySource | None = None) -> Word | None:
    sources = (source,) if source else (DictionarySource.CUSTOM, DictionarySource.STANDARD)
    for s in sources:
        row = conn.execute(
            "SELECT * FROM tb_words WHERE word_nm = ? AND source_cd = ?", (name, s.value)
        ).fetchone()
        if row:
            return _row_to_word(row)
    return None


def create_word(conn: sqlite3.Connection, word: Word) -> Word:
    word = _normalize(word)
    with conn:
        conn.execute(
            """
            INSERT INTO tb_words (word_nm, abbreviation_cd, domain_word_yn, domain_nm, data_type_cd, length_no, precision_no, scale_no, source_cd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'custom')
            ON CONFLICT(word_nm, source_cd) DO UPDATE SET
                abbreviation_cd = excluded.abbreviation_cd,
                domain_word_yn = excluded.domain_word_yn,
                domain_nm = excluded.domain_nm,
                data_type_cd = excluded.data_type_cd,
                length_no = excluded.length_no,
                precision_no = excluded.precision_no,
                scale_no = excluded.scale_no
            """,
            (
                word.word,
                word.abbreviation,
                "Y" if word.is_domain_word else "N",
                word.domain_name,
                word.data_type.value,
                word.length,
                word.precision,
                word.scale,
            ),
        )
    return get_word_by_name(conn, word.word, DictionarySource.CUSTOM)  # type: ignore[return-value]


def update_word(conn: sqlite3.Connection, name: str, word: Word) -> Word:
    existing = get_word_by_name(conn, name, DictionarySource.CUSTOM)
    if existing is None:
        if get_word_by_name(conn, name, DictionarySource.STANDARD) is not None:
            raise StandardWordImmutableError("표준 단어는 수정할 수 없습니다.")
        raise ValueError(f"커스텀 단어 '{name}'을(를) 찾을 수 없습니다.")

    word = _normalize(word)
    with conn:
        conn.execute(
            "UPDATE tb_words SET word_nm = ?, abbreviation_cd = ?, domain_word_yn = ?, domain_nm = ?, "
            "data_type_cd = ?, length_no = ?, precision_no = ?, scale_no = ? WHERE word_nm = ? AND source_cd = 'custom'",
            (
                word.word,
                word.abbreviation,
                "Y" if word.is_domain_word else "N",
                word.domain_name,
                word.data_type.value,
                word.length,
                word.precision,
                word.scale,
                name,
            ),
        )
    return get_word_by_name(conn, word.word, DictionarySource.CUSTOM)  # type: ignore[return-value]


def delete_word(conn: sqlite3.Connection, name: str) -> None:
    existing = get_word_by_name(conn, name, DictionarySource.CUSTOM)
    if existing is None:
        if get_word_by_name(conn, name, DictionarySource.STANDARD) is not None:
            raise StandardWordImmutableError("표준 단어는 삭제할 수 없습니다.")
        return

    with conn:
        conn.execute("DELETE FROM tb_words WHERE word_nm = ? AND source_cd = 'custom'", (name,))
