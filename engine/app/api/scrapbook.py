"""F-102 스크랩북 API. 화면(UI)은 클립보드 원문을 그대로 보내고, 파싱은 여기서만 한다."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.scrapbook.parser import ParsedGrid, parse_grid_text

router = APIRouter(prefix="/scrapbook", tags=["scrapbook"])


class ParseGridRequest(BaseModel):
    raw_text: str


@router.post("/parse", response_model=ParsedGrid)
def parse_grid(body: ParseGridRequest) -> ParsedGrid:
    return parse_grid_text(body.raw_text)
