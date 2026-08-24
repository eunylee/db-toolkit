from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dictionary, domains, naming, scrapbook, tables, words
from app.storage.db import get_connection, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn = get_connection()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="da-toolkit engine", version="0.1.0", lifespan=lifespan)

# 로컬 전용 툴: UI 개발 서버(Vite 기본 5173)에서의 호출만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dictionary.router)
app.include_router(scrapbook.router)
app.include_router(naming.router)
app.include_router(tables.router)
app.include_router(domains.router)
app.include_router(words.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
