from app.core.scrapbook.parser import parse_grid_text


def test_parse_simple_tsv():
    text = "논리명\t물리명\t타입\n고객명\tCUST_NM\tVARCHAR"

    grid = parse_grid_text(text)

    assert grid.rows == [
        ["논리명", "물리명", "타입"],
        ["고객명", "CUST_NM", "VARCHAR"],
    ]
    assert grid.row_count == 2
    assert grid.column_count == 3


def test_parse_handles_crlf_line_endings():
    text = "a\tb\r\nc\td"

    grid = parse_grid_text(text)

    assert grid.rows == [["a", "b"], ["c", "d"]]


def test_parse_pads_ragged_rows():
    text = "a\tb\tc\nd\te"

    grid = parse_grid_text(text)

    assert grid.rows == [["a", "b", "c"], ["d", "e", ""]]
    assert grid.column_count == 3


def test_parse_strips_trailing_blank_row_from_trailing_newline():
    text = "a\tb\nc\td\n"

    grid = parse_grid_text(text)

    assert grid.row_count == 2
    assert grid.rows[-1] == ["c", "d"]


def test_parse_quoted_cell_with_embedded_tab_and_newline():
    # Excel/Notion은 셀 안에 탭/개행이 있으면 큰따옴표로 감싼다
    text = 'a\t"line1\nline2"\tc'

    grid = parse_grid_text(text)

    assert grid.rows == [["a", "line1\nline2", "c"]]


def test_parse_empty_string_returns_empty_grid():
    grid = parse_grid_text("")

    assert grid.rows == []
    assert grid.row_count == 0
    assert grid.column_count == 0


def test_parse_whitespace_only_returns_empty_grid():
    grid = parse_grid_text("\n\n\r\n")

    assert grid.rows == []


def test_parse_single_cell():
    grid = parse_grid_text("고객명")

    assert grid.rows == [["고객명"]]
    assert grid.row_count == 1
    assert grid.column_count == 1


def test_parse_preserves_intentional_blank_cells_in_middle():
    text = "a\t\tc\nd\te\tf"

    grid = parse_grid_text(text)

    assert grid.rows[0] == ["a", "", "c"]
