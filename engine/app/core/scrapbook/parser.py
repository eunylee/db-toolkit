"""F-102 엑셀/노션 스크랩북 (Grid Copy & Paste) 파서.

엑셀/구글시트/노션 표에서 영역을 복사하면 클립보드 text/plain에는 보통
탭으로 셀이, 개행으로 행이 구분된 TSV가 담긴다. 셀 안에 탭/개행이 포함된 경우
큰따옴표로 감싸는 관례(RFC4193 CSV 규칙과 동일)를 따르므로, 표준 csv 모듈을
구분자만 탭으로 바꿔 그대로 재사용한다.
"""

import csv
from io import StringIO

from pydantic import BaseModel


class ParsedGrid(BaseModel):
    rows: list[list[str]]
    row_count: int
    column_count: int


def parse_grid_text(raw_text: str) -> ParsedGrid:
    if not raw_text or not raw_text.strip("\r\n"):
        return ParsedGrid(rows=[], row_count=0, column_count=0)

    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.reader(StringIO(normalized), delimiter="\t")
    rows = [row for row in reader]

    # 복사 시 말미에 개행이 남아 생기는 빈 꼬리 행 제거
    while rows and all(cell == "" for cell in rows[-1]):
        rows.pop()

    if not rows:
        return ParsedGrid(rows=[], row_count=0, column_count=0)

    column_count = max(len(row) for row in rows)
    padded_rows = [row + [""] * (column_count - len(row)) for row in rows]

    return ParsedGrid(rows=padded_rows, row_count=len(padded_rows), column_count=column_count)
