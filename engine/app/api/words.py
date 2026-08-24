"""단어(word) 관리 API. tb_words 참고 — 용어(dictionary_terms)와 분리된 최소 재사용 단위.

미등록 단어 등록(F-103 보완) 흐름이 이 라우터를 사용한다.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.core.dictionary.tokenize import split_into_word_candidates
from app.core.words.repository import (
    StandardWordImmutableError,
    create_word,
    delete_word,
    list_words,
    lookup_word,
    update_word,
)
from app.models.dictionary import DictionarySource
from app.models.words import SplitCandidate, Word

router = APIRouter(prefix="/words", tags=["words"])


@router.get("", response_model=list[Word])
def get_words(query: str | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[Word]:
    return list_words(conn, query=query)


@router.post("", response_model=Word)
def post_word(word: Word, conn: sqlite3.Connection = Depends(get_db)) -> Word:
    """미등록 단어를 등록/수정한다. 표준 단어는 API로 건드릴 수 없으므로 source는 항상 custom으로 강제한다."""
    word = word.model_copy(update={"source": DictionarySource.CUSTOM})
    return create_word(conn, word)


@router.put("/{word_name}", response_model=Word)
def put_word(word_name: str, word: Word, conn: sqlite3.Connection = Depends(get_db)) -> Word:
    try:
        return update_word(conn, word_name, word)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StandardWordImmutableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{word_name}", status_code=204)
def delete_word_endpoint(word_name: str, conn: sqlite3.Connection = Depends(get_db)) -> None:
    try:
        delete_word(conn, word_name)
    except StandardWordImmutableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lookup", response_model=Word)
def get_lookup(word: str, conn: sqlite3.Connection = Depends(get_db)) -> Word:
    result = lookup_word(conn, word)
    if result is None:
        raise HTTPException(status_code=404, detail=f"'{word}'에 대한 단어를 찾을 수 없습니다.")
    return result


@router.get("/split-candidates", response_model=list[SplitCandidate])
def get_split_candidates(text: str, conn: sqlite3.Connection = Depends(get_db)) -> list[SplitCandidate]:
    """미등록 구간을 단어 후보로 쪼개고, 각 후보가 이미 tb_words에 있는지 확인한다.

    통짜 복합어 하나로 등록하면 재사용이 안 되므로, 이미 있는 단어는 건너뛰고
    없는 단어만 순서대로 등록하도록 유도하는 화면(F-103 보완)의 기반 데이터다.
    """
    candidates: list[SplitCandidate] = []
    for token in split_into_word_candidates(text):
        found = lookup_word(conn, token)
        if found:
            candidates.append(
                SplitCandidate(
                    term=token,
                    exists=True,
                    is_domain_word=found.is_domain_word,
                    abbreviation=found.abbreviation,
                    data_type=found.data_type,
                    length=found.length,
                    precision=found.precision,
                    scale=found.scale,
                )
            )
        else:
            candidates.append(SplitCandidate(term=token, exists=False))
    return candidates
