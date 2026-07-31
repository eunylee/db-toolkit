"""행정정보표준 도메인 코드 파서.

도메인 코드는 "{한글 분류}{타입기호}{길이 또는 정밀도,스케일}" 형태다.
예: "명V100" -> 분류=명, VARCHAR(100)
    "여부C1" -> 분류=여부, CHAR(1)
    "수N15,4" -> 분류=수, NUMBER(15,4)
    "연월일시분초D" -> 분류=연월일시분초, DATE (길이 없음)
"""

import re

from app.models.dictionary import DictionaryDataType

_PATTERN = re.compile(r"^(?P<domain_class>.+?)(?P<type>[VCND])(?P<num>\d+(?:,\d+)?)?$")

_TYPE_MAP = {
    "V": DictionaryDataType.VARCHAR,
    "C": DictionaryDataType.CHAR,
    "N": DictionaryDataType.NUMBER,
    "D": DictionaryDataType.DATE,
}


class ParsedDomainCode:
    __slots__ = ("domain_class", "data_type", "length", "precision", "scale")

    def __init__(
        self,
        domain_class: str,
        data_type: DictionaryDataType,
        length: int | None = None,
        precision: int | None = None,
        scale: int | None = None,
    ):
        self.domain_class = domain_class
        self.data_type = data_type
        self.length = length
        self.precision = precision
        self.scale = scale


def parse_domain_code(domain_code: str) -> ParsedDomainCode:
    domain_code = (domain_code or "").strip()
    match = _PATTERN.match(domain_code)
    if not match:
        return ParsedDomainCode(domain_class=domain_code, data_type=DictionaryDataType.UNKNOWN)

    data_type = _TYPE_MAP[match.group("type")]
    num = match.group("num")

    length: int | None = None
    precision: int | None = None
    scale: int | None = None

    if num and "," in num:
        precision_str, scale_str = num.split(",", 1)
        precision, scale = int(precision_str), int(scale_str)
    elif num:
        length = int(num)

    return ParsedDomainCode(
        domain_class=match.group("domain_class"),
        data_type=data_type,
        length=length,
        precision=precision,
        scale=scale,
    )
