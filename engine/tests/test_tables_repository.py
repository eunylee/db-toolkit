from app.core.tables.repository import get_table, load_tables, save_table
from app.models.tables import Column, Table


def _table(name="고객", physical="CUST", pk_col="고객번호"):
    return Table(
        logical_name=name,
        physical_name=physical,
        columns=[Column(logical_name=pk_col, physical_name="CUST_NO", is_pk=True)],
    )


def test_save_and_load_table(tmp_path):
    path = tmp_path / "model.yaml"
    save_table(_table(), path)

    tables = load_tables(path)

    assert len(tables) == 1
    assert tables[0].logical_name == "고객"
    assert tables[0].columns[0].is_pk is True


def test_save_table_overwrites_existing_by_logical_name(tmp_path):
    path = tmp_path / "model.yaml"
    save_table(_table(physical="CUST"), path)
    save_table(_table(physical="CUSTOMER_V2"), path)

    tables = load_tables(path)

    assert len(tables) == 1
    assert tables[0].physical_name == "CUSTOMER_V2"


def test_save_table_keeps_other_tables(tmp_path):
    path = tmp_path / "model.yaml"
    save_table(_table(name="고객", physical="CUST"), path)
    save_table(_table(name="주문", physical="ORDER"), path)

    tables = load_tables(path)

    assert {t.logical_name for t in tables} == {"고객", "주문"}


def test_get_table_returns_none_when_missing(tmp_path):
    path = tmp_path / "model.yaml"

    assert get_table("없는테이블", path) is None


def test_get_table_returns_match(tmp_path):
    path = tmp_path / "model.yaml"
    save_table(_table(), path)

    found = get_table("고객", path)

    assert found is not None
    assert found.physical_name == "CUST"


def test_load_tables_missing_file_returns_empty_list(tmp_path):
    assert load_tables(tmp_path / "missing.yaml") == []
