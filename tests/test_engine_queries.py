"""Tests the SQL created by the engine without using Oracle.

The tests replace the real database call with a fake function.
This lets us check the SQL and parameters without connecting to Oracle.
"""

import re

import db
import engine


def _squeeze(sql):
    """Collapses runs of whitespace into one space.

    The SQL is written over several lines and its columns are aligned for
    reading, so the exact spacing is a formatting choice and not something a
    test should depend on. Comparing the squeezed text checks what the query
    asks for, and keeps the test working if the SQL is re-indented later.
    """

    return re.sub(r"\s+", " ", sql)


def _recorder(monkeypatch):
    """Records SQL queries instead of running them."""

    calls = []

    def fake_run_query(sql, params=None):
        calls.append((sql, params or {}))
        return []

    # Replace the real database query with the fake one.
    monkeypatch.setattr(db, "run_query", fake_run_query)

    return calls


def test_search_words_without_filters(monkeypatch):
    # Checks a word search with no filters.
    calls = _recorder(monkeypatch)

    engine.search_words()

    sql, params = calls[-1]

    assert "FROM v_word_index" in sql
    assert "1 = 1" in sql
    assert params == {}


def test_search_words_with_all_filters(monkeypatch):
    # Checks that all search filters are added to the SQL correctly.
    calls = _recorder(monkeypatch)

    engine.search_words(
        word="Sis",
        authors=["Lewis Carroll"],
        years=[1865],
        titles=["Alice"]
    )

    sql, params = calls[-1]

    # The searched word is converted to lower case.
    assert params["word"] == "sis"

    # Check the filter values.
    assert params["au0"] == "Lewis Carroll"
    assert params["yr0"] == 1865
    assert params["ti0"] == "Alice"

    # Check that the filters were added to the SQL.
    assert "LIKE '%' || :word || '%'" in sql
    assert "AuthorName IN (:au0)" in sql


def test_unfiltered_counts_come_from_the_index_view(monkeypatch):
    # Without document filters, the view already contains the word counts.
    calls = _recorder(monkeypatch)

    engine.search_words(word="love")

    sql, _params = calls[-1]

    assert "FROM v_word_index" in sql
    assert "COUNT(o.OccID)" not in sql


def test_scoped_counts_are_aggregated_over_the_scope(monkeypatch):
    # With document filters, counts must be calculated only for those documents.
    calls = _recorder(monkeypatch)

    engine.search_words(doc_ids=[3, 4])

    sql, params = calls[-1]

    # In this case the query calculates the counts directly.
    assert "FROM v_word_index" not in sql
    assert "COUNT(o.OccID) AS Occurrences" in _squeeze(sql)
    assert "COUNT(DISTINCT o.DocID) AS Documents" in _squeeze(sql)
    assert "GROUP BY w.WordID, w.WordText" in sql

    # Check that both document IDs are passed as bind variables.
    assert "o.DocID IN (:di0, :di1)" in sql
    assert params == {"di0": 3, "di1": 4}


def test_words_in_documents_delegates_to_the_scoped_search(monkeypatch):
    # Checks that searching words in documents adds the document filter.
    calls = _recorder(monkeypatch)

    engine.words_in_documents([2])

    sql, params = calls[-1]

    assert "o.DocID IN (:di0)" in sql
    assert params == {"di0": 2}


def test_kwic_joins_and_lowercases(monkeypatch):
    # Checks the KWIC search and its word normalization.
    calls = _recorder(monkeypatch)

    engine.kwic("Love")

    sql, params = calls[-1]

    assert "JOIN Words" in sql
    assert "ORDER BY d.Title" in sql
    assert params["word"] == "love"


def test_kwic_accepts_the_same_scope_as_search_words(monkeypatch):
    # KWIC must use the same filters as the normal word search.
    calls = _recorder(monkeypatch)

    engine.kwic(
        "love",
        doc_ids=[5],
        authors=["Beatrix Potter"]
    )

    sql, params = calls[-1]

    assert "o.DocID IN (:di0)" in sql
    assert "a.AuthorName IN (:au0)" in sql

    assert params == {
        "word": "love",
        "au0": "Beatrix Potter",
        "di0": 5
    }


def test_locate_by_position_binds(monkeypatch):
    # Checks a search by exact word position in a document.
    calls = _recorder(monkeypatch)

    engine.locate_by_position(
        1,
        paragraph=3,
        line=12,
        position=5
    )

    sql, params = calls[-1]

    # Check that all position values are passed safely as bind variables.
    assert params == {
        "doc_id": 1,
        "p": 3,
        "l": 12,
        "pos": 5
    }

    assert "o.ParagraphNum = :p" in sql


def test_documents_containing_lowercases_word(monkeypatch):
    # Checks document search by word.
    calls = _recorder(monkeypatch)

    engine.documents_containing("Rabbit")

    sql, params = calls[-1]

    assert params["word"] == "rabbit"
    assert "SELECT DISTINCT" in sql


def test_documents_search_filters_in_sql(monkeypatch):
    # Checks title, author and year filters in document search.
    calls = _recorder(monkeypatch)

    engine.documents(
        title="Prin",
        authors=["Frances Hodgson Burnett"],
        years=[1905]
    )

    sql, params = calls[-1]

    # Title uses partial search.
    assert "LOWER(d.Title) LIKE '%' || :title || '%'" in sql
    assert params["title"] == "prin"

    # Author uses an exact list filter.
    assert "AuthorName IN (:au0)" in sql
    assert params["au0"] == "Frances Hodgson Burnett"

    # Year also uses an exact list filter.
    assert "PubYear IN (:yr0)" in sql
    assert params["yr0"] == 1905


def test_documents_without_filters_lists_all(monkeypatch):
    # Checks that all documents can be returned when no filters are given.
    calls = _recorder(monkeypatch)

    engine.documents()

    sql, params = calls[-1]

    assert "1 = 1" in sql
    assert params == {}