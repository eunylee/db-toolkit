"""API 라우터 간에 공유하는 FastAPI 의존성.

라우터마다 개별적으로 커넥션 의존성을 정의하면 테스트에서
`app.dependency_overrides`로 하나만 오버라이드했을 때 다른 라우터에는
적용되지 않는 문제가 생긴다. 반드시 이 모듈의 `get_db`를 공유해서 쓴다.
"""

import sqlite3
from typing import Iterator

from app.storage.db import get_connection, init_db


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()
