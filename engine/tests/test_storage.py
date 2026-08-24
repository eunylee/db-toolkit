from app.storage import db, yaml_store


def test_init_db_creates_expected_tables(tmp_path):
    conn = db.get_connection(tmp_path / "test.db")
    db.init_db(conn)

    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }

    assert {"tb_terms", "tb_words", "tb_domains"} <= tables
    conn.close()


def test_init_db_is_idempotent(tmp_path):
    conn = db.get_connection(tmp_path / "test.db")
    db.init_db(conn)
    db.init_db(conn)  # 재실행해도 에러 없어야 함

    conn.execute("INSERT INTO tb_terms (term_nm, abbreviation_cd, source_cd) VALUES ('x', 'X', 'standard')")
    conn.commit()
    row = conn.execute("SELECT term_nm FROM tb_terms").fetchone()

    assert row["term_nm"] == "x"
    conn.close()


def test_yaml_round_trip(tmp_path):
    path = tmp_path / "model.yaml"
    data = {"tables": [{"name": "customer", "columns": [{"name": "customer_id", "pk": True}]}]}

    yaml_store.write_yaml(path, data)
    loaded = yaml_store.read_yaml(path)

    assert loaded == data


def test_yaml_read_missing_file_returns_empty_dict(tmp_path):
    assert yaml_store.read_yaml(tmp_path / "missing.yaml") == {}
