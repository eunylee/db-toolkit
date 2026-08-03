from app.core.domains.derive import derive_domains_from_terms
from app.models.dictionary import DictionaryDataType, DictionarySource, DictionaryTerm


def _term(term, domain_code, data_type=DictionaryDataType.VARCHAR, length=100):
    return DictionaryTerm(
        term=term,
        abbreviation=term.upper(),
        domain_code=domain_code,
        data_type=data_type,
        length=length,
        source=DictionarySource.STANDARD,
    )


def test_derive_domains_dedupes_by_domain_code():
    terms = [
        _term("고객명", "명V100"),
        _term("API명", "명V100"),
        _term("고객번호", "번호V20", length=20),
    ]

    domains = derive_domains_from_terms(terms)

    assert len(domains) == 2
    names = {d.name for d in domains}
    assert names == {"명V100", "번호V20"}


def test_derive_domains_skips_terms_without_domain_code():
    terms = [_term("이상한값", "")]

    domains = derive_domains_from_terms(terms)

    assert domains == []


def test_derive_domains_marked_as_standard_source():
    domains = derive_domains_from_terms([_term("고객명", "명V100")])

    assert domains[0].source == DictionarySource.STANDARD
