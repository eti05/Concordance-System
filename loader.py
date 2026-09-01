"""Loads text documents into the Concordance System.

Reads a text file, splits it into normalized words with positions,
and stores the document, words and occurrences in Oracle.
"""

import re

import db


# Finds words made from letters and keeps apostrophes inside words.
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)

# Number of occurrences inserted in one batch.
_OCC_BATCH = 5000


class LoaderError(Exception):
    """Raised when a document cannot be loaded."""


def normalize(token):
    """Converts a word to the format stored in the database."""

    return token.replace("’", "'").lower().strip()


def extract_words(line):
    """Returns the normalized words found in one line."""

    return [normalize(match.group(0)) for match in _WORD_RE.finditer(line)]


def tokenize(text):
    """Splits text into words together with their positions.

    Each result contains:
    word, paragraph number, line number and word position.
    """

    tokens = []
    paragraph = 0
    line = 0

    # The next line with words will start a new paragraph.
    start_paragraph = True

    for raw_line in text.split("\n"):

        # A blank line starts a new paragraph.
        if raw_line.strip() == "":
            start_paragraph = True
            continue

        words = extract_words(raw_line)

        # Lines without real words are ignored.
        if not words:
            continue

        if start_paragraph:
            paragraph += 1
            start_paragraph = False

        # Line numbers are global inside the document.
        line += 1

        # Word position starts again from 1 on every line.
        for position, word in enumerate(words, start=1):
            tokens.append((word, paragraph, line, position))

    return tokens


def _read_text(path):
    """Reads a UTF-8 text file."""

    with open(path, "r", encoding="utf-8-sig") as file:
        return file.read()


def _ensure_author(author_name):
    """Creates the author if needed and returns the author ID."""

    # MERGE prevents creating the same author twice.
    db.run_command(
        """
        MERGE INTO Authors a
        USING (SELECT :name AS nm FROM dual) s
        ON (a.AuthorName = s.nm)
        WHEN NOT MATCHED THEN
            INSERT (AuthorName)
            VALUES (s.nm)
        """,
        {"name": author_name}
    )

    rows = db.run_query(
        """
        SELECT AuthorID
        FROM Authors
        WHERE AuthorName = :name
        """,
        {"name": author_name}
    )

    return rows[0]["authorid"]


def _document_exists(title, author_id):
    """Checks whether a document already exists."""

    rows = db.run_query(
        """
        SELECT 1 AS present
        FROM Documents
        WHERE Title = :title
          AND AuthorID = :author_id
        """,
        {"title": title, "author_id": author_id}
    )

    return bool(rows)


def document_exists(title, author):
    """Checks for an existing document by title and author name."""

    rows = db.run_query(
        """
        SELECT 1 AS present
        FROM Documents d
        JOIN Authors a
          ON a.AuthorID = d.AuthorID
        WHERE d.Title = :title
          AND a.AuthorName = :author
        """,
        {"title": title, "author": author}
    )

    return bool(rows)


def _insert_document(title, author_id, year, source, load_date=None):
    """Inserts one document and returns its new ID."""

    binds = {
        "title": title,
        "author_id": author_id,
        "year": year,
        "source": source
    }

    columns = "Title, AuthorID, PubYear, Source"
    values = ":title, :author_id, :year, :source"

    # During XML import we can restore the original load date.
    if load_date is not None:
        binds["load_date"] = load_date
        columns += ", LoadDate"
        values += ", :load_date"

    sql = (
        f"INSERT INTO Documents ({columns}) "
        f"VALUES ({values}) "
        f"RETURNING DocID INTO :new_id"
    )

    return db.insert_returning_id(sql, binds)


def _ensure_words(unique_words):
    """Inserts words that do not already exist."""

    db.executemany(
        """
        MERGE INTO Words w
        USING (SELECT :word AS word FROM dual) s
        ON (w.WordText = s.word)
        WHEN NOT MATCHED THEN
            INSERT (WordText)
            VALUES (s.word)
        """,
        [{"word": word} for word in unique_words]
    )


def _fetch_word_ids(unique_words):
    """Returns a dictionary that connects each word to its WordID."""

    word_ids = {}

    # Oracle allows up to 1000 values in an IN list.
    chunk = 1000

    for start in range(0, len(unique_words), chunk):
        batch = unique_words[start:start + chunk]

        binds = {
            f"word{index}": word
            for index, word in enumerate(batch)
        }

        placeholders = ", ".join(
            f":word{index}"
            for index in range(len(batch))
        )

        rows = db.run_query(
            "SELECT WordID, WordText "
            "FROM Words "
            f"WHERE WordText IN ({placeholders})",
            binds
        )

        for row in rows:
            word_ids[row["wordtext"]] = row["wordid"]

    return word_ids


def _insert_occurrences(doc_id, tokens, word_ids):
    """Inserts all word occurrences for one document."""

    rows = [
        {
            "doc_id": doc_id,
            "word_id": word_ids[word],
            "paragraph": paragraph,
            "line": line,
            "position": position
        }
        for word, paragraph, line, position in tokens
    ]

    sql = """
        INSERT INTO Occurrences
            (DocID, WordID, ParagraphNum, LineNum, WordPosition)
        VALUES
            (:doc_id, :word_id, :paragraph, :line, :position)
    """

    # Insert large documents in smaller batches.
    for start in range(0, len(rows), _OCC_BATCH):
        db.executemany(sql, rows[start:start + _OCC_BATCH])


def load_tokens(title, author, year, source, tokens, load_date=None):
    """Stores an already tokenized document in the database.

    Returns the document ID, total word count
    and number of unique words.
    """

    if not tokens:
        raise LoaderError(f"The document '{title}' contains no words.")

    try:
        # Make sure the author exists.
        author_id = _ensure_author(author)

        # Do not load the same document twice.
        if _document_exists(title, author_id):
            raise LoaderError(
                f"The document '{title}' by {author} is already loaded."
            )

        # Insert the main document row.
        doc_id = _insert_document(title, author_id, year, source, load_date)

        # Create a sorted list of unique words.
        unique_words = sorted({word for word, _, _, _ in tokens})

        # Make sure all words exist in the Words table.
        _ensure_words(unique_words)

        # Get each word's database ID.
        word_ids = _fetch_word_ids(unique_words)

        # Insert all word occurrences.
        _insert_occurrences(doc_id, tokens, word_ids)

        db.commit()

    except LoaderError:
        # Undo the load when a known loader problem happens.
        db.rollback()
        raise

    except Exception as error:
        # Undo the whole load if any database or file operation fails.
        db.rollback()
        raise LoaderError(
            f"Load failed and was rolled back: {error}"
        ) from error

    return {
        "doc_id": doc_id,
        "words_loaded": len(tokens),
        "unique_words": len(unique_words)
    }


def refresh_statistics():
    """Updates Oracle statistics after loading many rows."""

    db.run_command(
        """
        BEGIN
            DBMS_STATS.GATHER_SCHEMA_STATS(
                USER,
                cascade => TRUE
            );
        END;
        """
    )

    db.commit()


def load_document(path, title, author, year=None, source=None):
    """Reads, tokenizes and loads one text document."""

    # Read the source file.
    text = _read_text(path)

    # Split it into normalized words and positions.
    tokens = tokenize(text)

    if not tokens:
        raise LoaderError(f"No words were found in '{path}'.")

    # Store the tokenized document in Oracle.
    return load_tokens(title, author, year, source, tokens)