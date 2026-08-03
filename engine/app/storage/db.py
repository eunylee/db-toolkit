"""SQLite 연결 및 스키마 초기화.

SQLite는 사전 등 로컬 조회용 캐시/인덱스로 사용한다 (재생성 가능, git 비대상).
버전 관리 대상인 설계 모델의 원본은 yaml_store가 다루는 YAML 파일이다.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "runtime" / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dictionary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    abbreviation TEXT NOT NULL,
    domain_code TEXT NOT NULL DEFAULT '',
    domain_class TEXT NOT NULL DEFAULT '',
    data_type TEXT NOT NULL DEFAULT 'UNKNOWN',
    length INTEGER,
    precision INTEGER,
    scale INTEGER,
    storage_format TEXT NOT NULL DEFAULT '',
    allowed_values TEXT NOT NULL DEFAULT '',
    synonyms TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL CHECK (source IN ('standard', 'custom')),
    UNIQUE(term, source)
);
CREATE INDEX IF NOT EXISTS idx_dictionary_terms_term ON dictionary_terms(term);
CREATE INDEX IF NOT EXISTS idx_dictionary_terms_source ON dictionary_terms(source);

CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    length INTEGER,
    precision INTEGER,
    scale INTEGER,
    source TEXT NOT NULL CHECK (source IN ('standard', 'custom')),
    UNIQUE(name, source)
);
CREATE INDEX IF NOT EXISTS idx_domains_name ON domains(name);
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
