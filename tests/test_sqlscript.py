"""Tests the SQL statement splitter and the project SQL files."""

import os

import sqlscript


# Folder that contains the project SQL files.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(PROJECT_DIR, "sql")


def test_regular_statements_split_on_semicolon():
    # Regular SQL statements should be split at semicolons.
    text = "CREATE TABLE a (x NUMBER);\nCREATE TABLE b (y NUMBER);\n"

    statements = sqlscript.split_statements(text)

    assert len(statements) == 2
    assert statements[0].startswith("CREATE TABLE a")
    assert ";" not in statements[0]


def test_plsql_block_kept_whole():
    # A PL/SQL block should stay as one statement.
    text = (
        "CREATE OR REPLACE TRIGGER t\nBEFORE INSERT ON x\nFOR EACH ROW\n"
        "BEGIN\n  :NEW.y := 1;\nEND;\n/\n"
    )

    statements = sqlscript.split_statements(text)

    assert len(statements) == 1
    assert "END;" in statements[0]


def test_comment_only_pieces_are_dropped():
    # Comments by themselves should not become SQL statements.
    text = "-- header\nCREATE TABLE a (x NUMBER);\n-- trailing comment\n"

    statements = sqlscript.split_statements(text)

    assert len(statements) == 1


def test_comment_marker_inside_a_literal_is_kept():
    # Comment symbols inside text are part of the value, not real comments.
    text = (
        "INSERT INTO t (msg) VALUES ('a -- b');\n"
        "INSERT INTO t (msg) VALUES ('c /* d');\n"
    )

    statements = sqlscript.split_statements(text)

    assert statements == [
        "INSERT INTO t (msg) VALUES ('a -- b')",
        "INSERT INTO t (msg) VALUES ('c /* d')",
    ]


def test_semicolon_inside_a_literal_does_not_split():
    # A semicolon inside text should not split the SQL statement.
    text = "INSERT INTO t (msg) VALUES ('one; two');\n"

    statements = sqlscript.split_statements(text)

    assert statements == [
        "INSERT INTO t (msg) VALUES ('one; two')"
    ]


def test_escaped_quote_keeps_the_literal_open():
    # Two single quotes represent one quote inside Oracle text.
    text = (
        "INSERT INTO t (msg) VALUES ('it''s; fine');\n"
        "CREATE TABLE a (x NUMBER);\n"
    )

    statements = sqlscript.split_statements(text)

    assert statements == [
        "INSERT INTO t (msg) VALUES ('it''s; fine')",
        "CREATE TABLE a (x NUMBER)",
    ]


def test_quote_inside_a_comment_does_not_open_a_literal():
    # A quote inside a comment should not affect the rest of the SQL file.
    text = (
        "-- don't be fooled\n"
        "CREATE TABLE a (x NUMBER);\n"
        "CREATE TABLE b (y NUMBER);\n"
    )

    statements = sqlscript.split_statements(text)

    assert len(statements) == 2


def test_block_comment_spanning_lines_is_removed():
    # A block comment can continue across several lines.
    text = "/* one\n   two */\nCREATE TABLE a (x NUMBER);\n"

    statements = sqlscript.split_statements(text)

    assert statements == [
        "CREATE TABLE a (x NUMBER)"
    ]


def test_project_sql_files_parse_to_expected_counts():
    # Check that every project SQL file is split into the expected number of statements.
    expected = {
        "create_tables.sql": 8,
        "indexes.sql": 6,
        "triggers.sql": 1,
        "create_views.sql": 3,
        "drop_all.sql": 1,
    }

    for filename, expected_count in expected.items():
        path = os.path.join(SQL_DIR, filename)

        with open(path, encoding="utf-8") as file:
            sql_text = file.read()

        statements = sqlscript.split_statements(sql_text)

        assert len(statements) == expected_count, (
            f"{filename} produced {len(statements)} statements"
        )