import pytest

from app.core.domains import repository
from app.models.dictionary import DictionaryDataType, DictionarySource
from app.models.domains import Domain
from app.storage.db import get_connection, init_db


def _conn(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    init_db(conn)
    return conn


def _domain(name="이메일주소", data_type=DictionaryDataType.VARCHAR, length=255):
    return Domain(name=name, data_type=data_type, length=length, source=DictionarySource.CUSTOM)


def test_create_and_list_domain(tmp_path):
    conn = _conn(tmp_path)
    created = repository.create_domain(conn, _domain())

    domains = repository.list_domains(conn)

    assert created.source == DictionarySource.CUSTOM
    assert len(domains) == 1
    assert domains[0].name == "이메일주소"


def test_replace_standard_domains_is_a_full_reimport(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_standard_domains(conn, [Domain(name="A", data_type=DictionaryDataType.VARCHAR, source=DictionarySource.STANDARD)])
    repository.replace_standard_domains(conn, [Domain(name="B", data_type=DictionaryDataType.VARCHAR, source=DictionarySource.STANDARD)])

    domains = repository.list_domains(conn)

    assert [d.name for d in domains] == ["B"]


def test_standard_and_custom_domains_coexist(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_standard_domains(conn, [Domain(name="명V100", data_type=DictionaryDataType.VARCHAR, length=100, source=DictionarySource.STANDARD)])
    repository.create_domain(conn, _domain())

    domains = repository.list_domains(conn)

    assert {d.name for d in domains} == {"명V100", "이메일주소"}


def test_list_domains_filters_by_query(tmp_path):
    conn = _conn(tmp_path)
    repository.create_domain(conn, _domain(name="이메일주소"))
    repository.create_domain(conn, _domain(name="전화번호"))

    results = repository.list_domains(conn, query="이메일")

    assert len(results) == 1
    assert results[0].name == "이메일주소"


def test_usage_count_reflects_matching_dictionary_terms(tmp_path):
    conn = _conn(tmp_path)
    repository.create_domain(conn, _domain(name="명V100"))
    conn.execute(
        "INSERT INTO dictionary_terms (term, abbreviation, domain_code, source) VALUES (?, ?, ?, 'custom')",
        ("고객명", "CUST_NM", "명V100"),
    )
    conn.execute(
        "INSERT INTO dictionary_terms (term, abbreviation, domain_code, source) VALUES (?, ?, ?, 'custom')",
        ("상품명", "PROD_NM", "명V100"),
    )
    conn.commit()

    domains = repository.list_domains(conn)

    assert domains[0].usage_count == 2


def test_update_custom_domain(tmp_path):
    conn = _conn(tmp_path)
    created = repository.create_domain(conn, _domain(length=255))

    updated = repository.update_domain(conn, created.id, _domain(name="이메일주소", length=320))

    assert updated.length == 320


def test_update_standard_domain_raises(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_standard_domains(conn, [Domain(name="명V100", data_type=DictionaryDataType.VARCHAR, source=DictionarySource.STANDARD)])
    standard_domain = repository.list_domains(conn)[0]

    with pytest.raises(repository.StandardDomainImmutableError):
        repository.update_domain(conn, standard_domain.id, _domain())


def test_update_missing_domain_raises_value_error(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        repository.update_domain(conn, 999, _domain())


def test_delete_custom_domain(tmp_path):
    conn = _conn(tmp_path)
    created = repository.create_domain(conn, _domain())

    repository.delete_domain(conn, created.id)

    assert repository.list_domains(conn) == []


def test_delete_standard_domain_raises(tmp_path):
    conn = _conn(tmp_path)
    repository.replace_standard_domains(conn, [Domain(name="명V100", data_type=DictionaryDataType.VARCHAR, source=DictionarySource.STANDARD)])
    standard_domain = repository.list_domains(conn)[0]

    with pytest.raises(repository.StandardDomainImmutableError):
        repository.delete_domain(conn, standard_domain.id)


def test_delete_missing_domain_is_noop(tmp_path):
    conn = _conn(tmp_path)

    repository.delete_domain(conn, 999)
