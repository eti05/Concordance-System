"""Tests how the loader splits and normalizes text."""

import loader


def test_paragraph_line_and_position_numbering():
    # Checks paragraph, line and word position numbers.
    text = "Hello world\nsecond line\n\nNew paragraph here\n"

    tokens = loader.tokenize(text)

    assert ("hello", 1, 1, 1) in tokens
    assert ("world", 1, 1, 2) in tokens

    # Word position starts again on each new line.
    assert ("second", 1, 2, 1) in tokens
    assert ("line", 1, 2, 2) in tokens

    # A blank line starts a new paragraph.
    assert ("new", 2, 3, 1) in tokens
    assert ("paragraph", 2, 3, 2) in tokens
    assert ("here", 2, 3, 3) in tokens


def test_line_numbers_are_global_across_paragraphs():
    # Line numbers continue even when a new paragraph starts.
    tokens = loader.tokenize("one\ntwo\n\nthree\nfour\n")

    assert [(token[0], token[2]) for token in tokens] == [
        ("one", 1),
        ("two", 2),
        ("three", 3),
        ("four", 4)
    ]


def test_blank_lines_collapse_into_one_break():
    # Several blank lines still create only one new paragraph.
    tokens = loader.tokenize("a\n\n\n\nb\n")

    assert ("a", 1, 1, 1) in tokens
    assert ("b", 2, 2, 1) in tokens
    assert {token[1] for token in tokens} == {1, 2}


def test_wordless_leading_line_creates_no_phantom_paragraph():
    # A line without words should not create a paragraph.
    tokens = loader.tokenize("1\n\nSara\n\nOnce upon a time\n")

    assert ("sara", 1, 1, 1) in tokens
    assert ("once", 2, 2, 1) in tokens
    assert min(token[1] for token in tokens) == 1
    assert min(token[2] for token in tokens) == 1


def test_case_folding_and_punctuation():
    # Words are changed to lower case and punctuation is removed.
    assert loader.extract_words("Hello, WORLD!") == ["hello", "world"]
    assert loader.extract_words("She said: 'stop.'") == ["she", "said", "stop"]


def test_contractions_and_hyphens():
    # Apostrophes stay inside words, while hyphens split words.
    assert loader.extract_words("don't stop") == ["don't", "stop"]
    assert loader.extract_words("cotton-tail") == ["cotton", "tail"]


def test_typographic_apostrophe_folds_to_plain():
    # A curved apostrophe is changed to a normal apostrophe.
    assert loader.extract_words("don’t") == ["don't"]


def test_underscores_and_digits_are_separators():
    # Underscores and numbers are not stored as words.
    assert loader.extract_words("_italic_ 1234 word") == ["italic", "word"]


def test_wordless_line_is_skipped_not_numbered():
    # A line without words should not get a line number.
    tokens = loader.tokenize("start\n* * *\nend\n")

    assert ("start", 1, 1, 1) in tokens
    assert ("end", 1, 2, 1) in tokens