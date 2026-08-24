"""SQLite 연결 및 스키마 초기화.

SQLite는 사전 등 로컬 조회용 캐시/인덱스로 사용한다 (재생성 가능, git 비대상).
버전 관리 대상인 설계 모델의 원본은 yaml_store가 다루는 YAML 파일이다.

테이블/컬럼 명명 규칙: 우리 서비스가 사용자에게 강제하는 "단어+단어+...+도메인" 규칙을
우리 자신의 스키마에도 그대로 적용한다. 테이블명은 tb_ 접두사, 컬럼명은 도메인 접미사
(_nm=명, _cd=코드/enum, _no=번호·길이, _cn=내용) 규칙을 따른다. 단일 단어 컬럼명
(name, source, word 등)은 예약어 충돌 및 확장성 문제가 있어 지양한다.

PK는 무조건 surrogate AUTOINCREMENT를 쓰지 않는다. tb_words/tb_terms/tb_domains는
전부 (이름, source_cd) 조합이 이미 UNIQUE라 그 자체가 자연키이므로, 별도 대리키 없이
복합 PK로 바로 쓴다.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "runtime" / "app.db"

_DATA_TYPE_CHECK = "CHECK (data_type_cd IN ('VARCHAR', 'CHAR', 'NUMBER', 'DATE', 'UNKNOWN'))"
_SOURCE_CHECK = "CHECK (source_cd IN ('standard', 'custom'))"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS tb_terms (
    term_nm TEXT NOT NULL,
    term_cn TEXT NOT NULL DEFAULT '',
    abbreviation_cd TEXT NOT NULL,
    domain_cd TEXT NOT NULL DEFAULT '',
    domain_class_nm TEXT NOT NULL DEFAULT '',
    data_type_cd TEXT NOT NULL DEFAULT 'UNKNOWN' {_DATA_TYPE_CHECK},
    length_no INTEGER,
    precision_no INTEGER,
    scale_no INTEGER,
    storage_format_cn TEXT NOT NULL DEFAULT '',
    allowed_value_cn TEXT NOT NULL DEFAULT '',
    synonym_list_cn TEXT NOT NULL DEFAULT '[]',
    source_cd TEXT NOT NULL {_SOURCE_CHECK},
    PRIMARY KEY (term_nm, source_cd)
);
CREATE INDEX IF NOT EXISTS idx_tb_terms_term_nm ON tb_terms(term_nm);
CREATE INDEX IF NOT EXISTS idx_tb_terms_source_cd ON tb_terms(source_cd);

CREATE TABLE IF NOT EXISTS tb_words (
    word_nm TEXT NOT NULL,
    abbreviation_cd TEXT NOT NULL,
    domain_word_yn TEXT NOT NULL DEFAULT 'N' CHECK (domain_word_yn IN ('Y', 'N')),
    domain_nm TEXT NOT NULL DEFAULT '',
    data_type_cd TEXT NOT NULL DEFAULT 'UNKNOWN' {_DATA_TYPE_CHECK},
    length_no INTEGER,
    precision_no INTEGER,
    scale_no INTEGER,
    source_cd TEXT NOT NULL {_SOURCE_CHECK},
    PRIMARY KEY (word_nm, source_cd)
);
CREATE INDEX IF NOT EXISTS idx_tb_words_word_nm ON tb_words(word_nm);

CREATE TABLE IF NOT EXISTS tb_domains (
    domain_nm TEXT NOT NULL,
    data_type_cd TEXT NOT NULL {_DATA_TYPE_CHECK},
    length_no INTEGER,
    precision_no INTEGER,
    scale_no INTEGER,
    source_cd TEXT NOT NULL {_SOURCE_CHECK},
    PRIMARY KEY (domain_nm, source_cd)
);
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI는 sync 의존성/async 엔드포인트를 서로 다른 스레드에서 실행할 수 있다.
    # 로컬 1인용 툴이라 동시 쓰기 경합이 없으므로 check_same_thread=False로 완화한다.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
