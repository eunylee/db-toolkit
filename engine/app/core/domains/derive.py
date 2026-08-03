"""표준 사전 임포트 시, 용어 데이터에서 재사용 가능한 도메인 목록을 뽑아낸다.

행안부 실데이터 기준 13,176개 용어가 단 123개 도메인코드만 공유하므로,
용어마다 도메인을 새로 만드는 대신 domain_code로 중복 제거해 재사용 가능한
도메인 레지스트리를 만든다.
"""

from app.models.dictionary import DictionarySource, DictionaryTerm
from app.models.domains import Domain


def derive_domains_from_terms(terms: list[DictionaryTerm]) -> list[Domain]:
    seen: dict[str, Domain] = {}
    for term in terms:
        if not term.domain_code or term.domain_code in seen:
            continue
        seen[term.domain_code] = Domain(
            name=term.domain_code,
            data_type=term.data_type,
            length=term.length,
            precision=term.precision,
            scale=term.scale,
            source=DictionarySource.STANDARD,
        )
    return list(seen.values())
