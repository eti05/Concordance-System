"""Engine layer of the Concordance System.

Handles word searches, document searches, KWIC context,
word groups, phrases and statistics.
All database access is done through the db module.
"""

import db


# Default number of words shown in frequency lists.
TOP_WORDS = 10


class EngineError(Exception):
    """Raised when an engine operation cannot be completed."""


class EngineConflict(EngineError):
    """Raised when requested data conflicts with existing database data."""


# ---------- Helpers ----------

def _where(conditions):
    """Joins SQL conditions with AND."""

    conditions = [condition for condition in conditions if condition]
    return " AND ".join(conditions) if conditions else "1 = 1"


# ---------- Lookup lists ----------

def list_authors():
    """Returns all author names."""

    rows = db.run_query("SELECT AuthorName FROM Authors ORDER BY AuthorName")
    return [row["authorname"] for row in rows]


def list_years():
    """Returns all publication years."""

    rows = db.run_query(
        "SELECT DISTINCT PubYear FROM Documents "
        "WHERE PubYear IS NOT NULL ORDER BY PubYear"
    )
    return [row["pubyear"] for row in rows]


def list_document_titles():
    """Returns all document titles."""

    rows = db.run_query("SELECT Title FROM Documents ORDER BY Title")
    return [row["title"] for row in rows]


def list_group_names():
    """Returns all group names."""

    rows = db.run_query("SELECT GroupName FROM Groups ORDER BY GroupName")
    return [row["groupname"] for row in rows]


# ---------- Word search ----------

def _in_clause(column, values, binds, prefix):
    """Builds an SQL IN condition and its bind variables."""

    names = []

    for index, value in enumerate(values):
        name = f"{prefix}{index}"
        binds[name] = value
        names.append(":" + name)

    return f"{column} IN ({', '.join(names)})"


def _as_list(value):
    """Converts one value or several values to a list."""

    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return list(value)

    return [value]


def _scope_conditions(
    binds,
    authors=None,
    years=None,
    titles=None,
    doc_id=None,
    doc_ids=None
):
    """Builds the document filters used by word searches."""

    conditions = []

    authors = _as_list(authors)
    if authors:
        conditions.append(_in_clause("a.AuthorName", authors, binds, "au"))

    years = [int(year) for year in _as_list(years)]
    if years:
        conditions.append(_in_clause("d.PubYear", years, binds, "yr"))

    titles = _as_list(titles)
    if titles:
        conditions.append(_in_clause("d.Title", titles, binds, "ti"))

    ids = [int(item) for item in _as_list(doc_ids)]

    if doc_id is not None:
        ids.append(int(doc_id))

    if ids:
        conditions.append(_in_clause("o.DocID", ids, binds, "di"))

    return conditions


# Adds the names of the groups that contain each word.
_GROUPS_COLUMN = """(SELECT LISTAGG(g2.GroupName, ', ') WITHIN GROUP (ORDER BY g2.GroupName)
                  FROM GroupMembers gm2
                  JOIN Groups g2 ON g2.GroupID = gm2.GroupID
                 WHERE gm2.WordID = %s) AS Groups"""


def search_words(
    word=None,
    authors=None,
    years=None,
    titles=None,
    group=None,
    doc_id=None,
    doc_ids=None
):
    """Returns words that match the selected filters."""

    binds = {}

    scope = _scope_conditions(
        binds,
        authors,
        years,
        titles,
        doc_id,
        doc_ids
    )

    conditions = list(scope)

    # Different queries use different table aliases.
    word_id = "w.WordID" if scope else "vi.WordID"
    word_text = "w.WordText" if scope else "vi.WordText"

    if word:
        binds["word"] = word.strip().lower()
        conditions.append(
            "LOWER(%s) LIKE '%%' || :word || '%%'" % word_text
        )

    if group:
        binds["grp"] = group

        conditions.append(
            """EXISTS (
                   SELECT 1
                   FROM GroupMembers gm
                   JOIN Groups g ON g.GroupID = gm.GroupID
                   WHERE gm.WordID = %s
                     AND g.GroupName = :grp
               )""" % word_id
        )

    if scope:
        # When filters are used, counts are calculated only inside that scope.
        sql = """
            SELECT w.WordID,
                   w.WordText,
                   COUNT(o.OccID) AS Occurrences,
                   COUNT(DISTINCT o.DocID) AS Documents,
                   LENGTH(w.WordText) AS CharCount,
                   %s
            FROM Occurrences o
            JOIN Documents d ON d.DocID = o.DocID
            JOIN Authors a ON a.AuthorID = d.AuthorID
            JOIN Words w ON w.WordID = o.WordID
            WHERE %s
            GROUP BY w.WordID, w.WordText
            ORDER BY COUNT(o.OccID) DESC, w.WordText
        """ % (_GROUPS_COLUMN % word_id, _where(conditions))

    else:
        # Without document filters, use the word index view.
        sql = """
            SELECT vi.WordID,
                   vi.WordText,
                   vi.Occurrences,
                   vi.Documents,
                   vi.CharCount,
                   %s
            FROM v_word_index vi
            WHERE %s
            ORDER BY vi.Occurrences DESC, vi.WordText
        """ % (_GROUPS_COLUMN % word_id, _where(conditions))

    rows = db.run_query(sql, binds)

    return [
        {
            "word_id": row["wordid"],
            "word": row["wordtext"],
            "occurrences": row["occurrences"],
            "documents": row["documents"],
            "char_count": row["charcount"],
            "groups": row["groups"],
        }
        for row in rows
    ]


def word_index(doc_id=None, group=None):
    """Returns the full word index."""

    return search_words(doc_id=doc_id, group=group)


def words_in_documents(doc_ids):
    """Returns the words that appear in selected documents."""

    return search_words(doc_ids=doc_ids)


def groups_of_word(word):
    """Returns the groups that contain a word."""

    rows = db.run_query(
        """
        SELECT g.GroupName
        FROM GroupMembers gm
        JOIN Groups g ON g.GroupID = gm.GroupID
        JOIN Words w ON w.WordID = gm.WordID
        WHERE w.WordText = :w
        ORDER BY g.GroupName
        """,
        {"w": word.strip().lower()}
    )

    return [row["groupname"] for row in rows]


# ---------- KWIC and text reconstruction ----------

def kwic(word, doc_id=None, authors=None, years=None, titles=None, doc_ids=None):
    """Returns every occurrence of a word with its position."""

    binds = {"word": word.strip().lower()}
    conditions = ["w.WordText = :word"]

    conditions += _scope_conditions(
        binds,
        authors,
        years,
        titles,
        doc_id,
        doc_ids
    )

    sql = """
        SELECT d.DocID,
               d.Title,
               o.ParagraphNum,
               o.LineNum,
               o.WordPosition
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        JOIN Documents d ON d.DocID = o.DocID
        JOIN Authors a ON a.AuthorID = d.AuthorID
        WHERE %s
        ORDER BY d.Title, o.ParagraphNum, o.LineNum, o.WordPosition
    """ % _where(conditions)

    rows = db.run_query(sql, binds)

    return [
        {
            "doc_id": row["docid"],
            "title": row["title"],
            "paragraph": row["paragraphnum"],
            "line": row["linenum"],
            "position": row["wordposition"],
        }
        for row in rows
    ]


def reconstruct_line(doc_id, line):
    """Rebuilds one line from its stored words."""

    if line is None or line < 1:
        return None

    rows = db.run_query(
        """
        SELECT w.WordText
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        WHERE o.DocID = :doc_id
          AND o.LineNum = :l
        ORDER BY o.WordPosition
        """,
        {"doc_id": int(doc_id), "l": int(line)}
    )

    if not rows:
        return None

    return " ".join(row["wordtext"] for row in rows)


def context(doc_id, line):
    """Returns the line before, current line and line after."""

    return {
        "before": reconstruct_line(doc_id, line - 1),
        "line": reconstruct_line(doc_id, line),
        "after": reconstruct_line(doc_id, line + 1),
    }


def full_text(doc_id):
    """Rebuilds a document from its stored word occurrences."""

    rows = db.run_query(
        """
        SELECT o.ParagraphNum,
               o.LineNum,
               o.WordPosition,
               w.WordText
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        WHERE o.DocID = :doc_id
        ORDER BY o.ParagraphNum, o.LineNum, o.WordPosition
        """,
        {"doc_id": int(doc_id)}
    )

    lines = []
    current = None
    words = []
    last_paragraph = None

    for row in rows:
        key = (row["paragraphnum"], row["linenum"])

        if key != current:
            if words:
                lines.append(" ".join(words))
                words = []

            # Add an empty line between paragraphs.
            if (
                last_paragraph is not None
                and row["paragraphnum"] != last_paragraph
            ):
                lines.append("")

            current = key
            last_paragraph = row["paragraphnum"]

        words.append(row["wordtext"])

    if words:
        lines.append(" ".join(words))

    return "\n".join(lines)


# ---------- Locate by position ----------

def locate_by_position(doc_id, paragraph=None, line=None, position=None):
    """Returns the words at a selected document position."""

    binds = {"doc_id": int(doc_id)}
    conditions = ["o.DocID = :doc_id"]

    if paragraph is not None:
        binds["p"] = int(paragraph)
        conditions.append("o.ParagraphNum = :p")

    if line is not None:
        binds["l"] = int(line)
        conditions.append("o.LineNum = :l")

    if position is not None:
        binds["pos"] = int(position)
        conditions.append("o.WordPosition = :pos")

    sql = """
        SELECT w.WordText,
               o.ParagraphNum,
               o.LineNum,
               o.WordPosition
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        WHERE %s
        ORDER BY o.ParagraphNum, o.LineNum, o.WordPosition
    """ % _where(conditions)

    rows = db.run_query(sql, binds)

    return [
        {
            "word": row["wordtext"],
            "paragraph": row["paragraphnum"],
            "line": row["linenum"],
            "position": row["wordposition"],
        }
        for row in rows
    ]


# ---------- Documents ----------

def documents(title=None, authors=None, years=None):
    """Searches documents by title, author and year."""

    binds = {}
    conditions = []

    if title:
        binds["title"] = title.strip().lower()
        conditions.append("LOWER(d.Title) LIKE '%' || :title || '%'")

    authors = _as_list(authors)
    if authors:
        conditions.append(_in_clause("a.AuthorName", authors, binds, "au"))

    years = [int(year) for year in _as_list(years)]
    if years:
        conditions.append(_in_clause("d.PubYear", years, binds, "yr"))

    sql = """
        SELECT d.DocID,
               d.Title,
               a.AuthorName,
               d.PubYear,
               d.Source,
               d.LoadDate
        FROM Documents d
        JOIN Authors a ON a.AuthorID = d.AuthorID
        WHERE %s
        ORDER BY d.Title
    """ % _where(conditions)

    rows = db.run_query(sql, binds)

    return [
        {
            "doc_id": row["docid"],
            "title": row["title"],
            "author": row["authorname"],
            "year": row["pubyear"],
            "source": row["source"],
            "load_date": row["loaddate"],
        }
        for row in rows
    ]


def documents_containing(word):
    """Returns the documents that contain a word."""

    rows = db.run_query(
        """
        SELECT DISTINCT d.DocID,
                        d.Title,
                        a.AuthorName,
                        d.PubYear
        FROM Occurrences o
        JOIN Documents d ON d.DocID = o.DocID
        JOIN Authors a ON a.AuthorID = d.AuthorID
        JOIN Words w ON w.WordID = o.WordID
        WHERE w.WordText = :word
        ORDER BY d.Title
        """,
        {"word": word.strip().lower()}
    )

    return [
        {
            "doc_id": row["docid"],
            "title": row["title"],
            "author": row["authorname"],
            "year": row["pubyear"],
        }
        for row in rows
    ]


# ---------- Groups ----------

def list_groups():
    """Returns all groups with their statistics."""

    rows = db.run_query(
        """
        SELECT GroupID,
               GroupName,
               WordCount,
               TotalOccurrences,
               Documents
        FROM v_group_stats
        ORDER BY GroupName
        """
    )

    return [
        {
            "group_id": row["groupid"],
            "name": row["groupname"],
            "word_count": row["wordcount"],
            "occurrences": row["totaloccurrences"],
            "documents": row["documents"],
        }
        for row in rows
    ]


def create_group(name):
    """Creates a new word group."""

    name = name.strip()

    if not name:
        raise EngineError("A group name is required.")

    existing = db.run_query(
        "SELECT 1 AS present FROM Groups WHERE GroupName = :name",
        {"name": name}
    )

    if existing:
        raise EngineConflict(f"Group '{name}' already exists.")

    db.run_command(
        "INSERT INTO Groups (GroupName) VALUES (:name)",
        {"name": name}
    )

    db.commit()


def delete_group(name):
    """Deletes a group."""

    db.run_command(
        "DELETE FROM Groups WHERE GroupName = :name",
        {"name": name}
    )

    db.commit()


def add_word_to_group(group_name, word):
    """Adds an existing word to a group."""

    word = word.strip().lower()

    group_rows = db.run_query(
        "SELECT GroupID FROM Groups WHERE GroupName = :g",
        {"g": group_name}
    )

    if not group_rows:
        raise EngineError(f"Group '{group_name}' does not exist.")

    group_id = group_rows[0]["groupid"]

    word_rows = db.run_query(
        "SELECT WordID FROM Words WHERE WordText = :w",
        {"w": word}
    )

    if not word_rows:
        raise EngineConflict(
            f"Cannot add '{word}': the word is not in the corpus."
        )

    word_id = word_rows[0]["wordid"]

    # MERGE prevents the same word from being added twice to one group.
    db.run_command(
        """
        MERGE INTO GroupMembers gm
        USING (SELECT :gid AS gid, :wid AS wid FROM dual) s
           ON (gm.GroupID = s.gid AND gm.WordID = s.wid)
        WHEN NOT MATCHED THEN
            INSERT (GroupID, WordID)
            VALUES (s.gid, s.wid)
        """,
        {"gid": group_id, "wid": word_id}
    )

    db.commit()


def remove_word_from_group(group_name, word):
    """Removes a word from a group."""

    db.run_command(
        """
        DELETE FROM GroupMembers
        WHERE GroupID = (
            SELECT GroupID
            FROM Groups
            WHERE GroupName = :g
        )
        AND WordID = (
            SELECT WordID
            FROM Words
            WHERE WordText = :w
        )
        """,
        {"g": group_name, "w": word.strip().lower()}
    )

    db.commit()


def group_words(group_name):
    """Returns the words of a group with their statistics."""

    rows = db.run_query(
        """
        SELECT w.WordText,
               COUNT(o.OccID) AS Occurrences,
               COUNT(DISTINCT o.DocID) AS Documents,
               LENGTH(w.WordText) AS CharCount
        FROM GroupMembers gm
        JOIN Words w ON w.WordID = gm.WordID
        JOIN Groups g ON g.GroupID = gm.GroupID
        LEFT JOIN Occurrences o ON o.WordID = w.WordID
        WHERE g.GroupName = :g
        GROUP BY w.WordText
        ORDER BY Occurrences DESC, w.WordText
        """,
        {"g": group_name}
    )

    return [
        {
            "word": row["wordtext"],
            "occurrences": row["occurrences"],
            "documents": row["documents"],
            "char_count": row["charcount"],
        }
        for row in rows
    ]


def group_stats(group_name):
    """Returns statistics for one group."""

    rows = db.run_query(
        """
        SELECT GroupName,
               WordCount,
               TotalOccurrences,
               Documents
        FROM v_group_stats
        WHERE GroupName = :g
        """,
        {"g": group_name}
    )

    if not rows:
        return None

    row = rows[0]

    return {
        "name": row["groupname"],
        "word_count": row["wordcount"],
        "occurrences": row["totaloccurrences"],
        "documents": row["documents"],
    }


# ---------- Phrases ----------

# Stores calculated phrase counts so they do not need to be recalculated
# every time the phrase list is refreshed.
_phrase_counts = {}

# Identifies the corpus state used by the current phrase cache.
_phrase_cache_tag = None


def _corpus_fingerprint():
    """Returns values that change when occurrences change."""

    row = db.run_query(
        "SELECT COUNT(*) AS n, NVL(MAX(OccID), 0) AS m FROM Occurrences"
    )[0]

    return (row["n"], row["m"])


def clear_phrase_cache():
    """Clears the saved phrase counts."""

    global _phrase_cache_tag

    _phrase_counts.clear()
    _phrase_cache_tag = None


def list_phrases():
    """Returns all phrases with their occurrence and document counts."""

    global _phrase_cache_tag

    tag = _corpus_fingerprint()

    # Clear old counts when the corpus has changed.
    if tag != _phrase_cache_tag:
        _phrase_counts.clear()
        _phrase_cache_tag = tag

    rows = db.run_query(
        "SELECT PhraseID, PhraseText FROM Phrases ORDER BY PhraseText"
    )

    result = []

    for row in rows:
        phrase_id = row["phraseid"]
        counts = _phrase_counts.get(phrase_id)

        # Calculate the count only when it is not already cached.
        if counts is None:
            matches = phrase_occurrences(row["phrasetext"])

            counts = (
                len(matches),
                len({match["doc_id"] for match in matches})
            )

            _phrase_counts[phrase_id] = counts

        result.append({
            "phrase_id": phrase_id,
            "phrase": row["phrasetext"],
            "occurrences": counts[0],
            "documents": counts[1],
        })

    return result


def create_phrase(phrase_text):
    """Stores a phrase as an ordered sequence of words."""

    from loader import extract_words

    phrase_text = phrase_text.strip()

    if not phrase_text:
        raise EngineError("A phrase is required.")

    words = extract_words(phrase_text)

    if not words:
        raise EngineError("The phrase contains no words.")

    existing = db.run_query(
        "SELECT 1 AS present FROM Phrases WHERE PhraseText = :t",
        {"t": phrase_text}
    )

    if existing:
        raise EngineConflict(
            f"The phrase '{phrase_text}' already exists."
        )

    word_ids = {}
    missing = []

    # Every phrase word must already exist in the corpus.
    for word in words:
        rows = db.run_query(
            "SELECT WordID FROM Words WHERE WordText = :w",
            {"w": word}
        )

        if rows:
            word_ids[word] = rows[0]["wordid"]
        else:
            missing.append(word)

    if missing:
        raise EngineConflict(
            "Cannot store the phrase; these words are not in the corpus: "
            + ", ".join(missing)
        )

    try:
        phrase_id = db.insert_returning_id(
            "INSERT INTO Phrases (PhraseText) VALUES (:t) "
            "RETURNING PhraseID INTO :new_id",
            {"t": phrase_text}
        )

        db.executemany(
            "INSERT INTO PhraseWords "
            "(PhraseID, SeqNum, WordID) VALUES (:pid, :seq, :wid)",
            [
                {
                    "pid": phrase_id,
                    "seq": index,
                    "wid": word_ids[word]
                }
                for index, word in enumerate(words, start=1)
            ]
        )

        db.commit()

    except Exception as error:
        db.rollback()
        raise EngineError(
            f"Could not store the phrase: {error}"
        ) from error

    return phrase_id


def delete_phrase(phrase_text):
    """Deletes a phrase."""

    db.run_command(
        "DELETE FROM Phrases WHERE PhraseText = :t",
        {"t": phrase_text.strip()}
    )

    db.commit()


def phrase_occurrences(phrase_text):
    """Finds occurrences of a phrase as consecutive words."""

    phrase_rows = db.run_query(
        "SELECT PhraseID FROM Phrases WHERE PhraseText = :t",
        {"t": phrase_text.strip()}
    )

    if not phrase_rows:
        return []

    phrase_id = phrase_rows[0]["phraseid"]

    word_rows = db.run_query(
        "SELECT WordID FROM PhraseWords "
        "WHERE PhraseID = :pid ORDER BY SeqNum",
        {"pid": phrase_id}
    )

    if not word_rows:
        return []

    word_ids = [row["wordid"] for row in word_rows]

    # The first phrase word starts the match.
    binds = {"w0": word_ids[0]}
    joins = []

    # Each next phrase word must appear directly after the previous words.
    for index in range(1, len(word_ids)):
        binds[f"w{index}"] = word_ids[index]

        joins.append(
            "JOIN seq s%d ON s%d.DocID = s0.DocID "
            "AND s%d.rn = s0.rn + %d "
            "AND s%d.WordID = :w%d"
            % (index, index, index, index, index, index)
        )

    sql = """
        WITH seq AS (
            SELECT /*+ MATERIALIZE */
                   o.DocID,
                   o.WordID,
                   o.ParagraphNum,
                   o.LineNum,
                   o.WordPosition,
                   ROW_NUMBER() OVER (
                       PARTITION BY o.DocID
                       ORDER BY o.ParagraphNum, o.LineNum, o.WordPosition
                   ) AS rn
            FROM Occurrences o
        )
        SELECT s0.DocID,
               d.Title,
               s0.ParagraphNum,
               s0.LineNum,
               s0.WordPosition
        FROM seq s0
        %s
        JOIN Documents d ON d.DocID = s0.DocID
        WHERE s0.WordID = :w0
        ORDER BY s0.DocID,
                 s0.ParagraphNum,
                 s0.LineNum,
                 s0.WordPosition
    """ % "\n        ".join(joins)

    rows = db.run_query(sql, binds)

    return [
        {
            "doc_id": row["docid"],
            "title": row["title"],
            "paragraph": row["paragraphnum"],
            "line": row["linenum"],
            "position": row["wordposition"],
        }
        for row in rows
    ]


# ---------- Statistics ----------

def most_frequent_words(doc_id=None, limit=TOP_WORDS):
    """Returns the most frequent words."""

    binds = {"lim": int(limit)}
    doc_clause = ""

    if doc_id:
        binds["doc_id"] = int(doc_id)
        doc_clause = "WHERE o.DocID = :doc_id"

    sql = """
        SELECT w.WordText,
               COUNT(*) AS Occurrences
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        %s
        GROUP BY w.WordText
        ORDER BY COUNT(*) DESC, w.WordText
        FETCH FIRST :lim ROWS ONLY
    """ % doc_clause

    rows = db.run_query(sql, binds)

    return [
        {
            "word": row["wordtext"],
            "occurrences": row["occurrences"]
        }
        for row in rows
    ]


def document_stats(doc_id):
    """Returns statistics for one document."""

    rows = db.run_query(
        """
        SELECT DocID,
               Title,
               TotalWords,
               UniqueWords,
               Paragraphs,
               AvgWordLength
        FROM v_document_stats
        WHERE DocID = :doc_id
        """,
        {"doc_id": int(doc_id)}
    )

    if not rows:
        return None

    row = rows[0]

    return {
        "doc_id": row["docid"],
        "title": row["title"],
        "total_words": row["totalwords"],
        "unique_words": row["uniquewords"],
        "paragraphs": row["paragraphs"],
        "avg_word_length": row["avgwordlength"],
    }


def document_word_list(doc_id):
    """Returns the words of one document with their counts."""

    rows = db.run_query(
        """
        SELECT w.WordText,
               COUNT(*) AS Occurrences,
               LENGTH(w.WordText) AS CharCount
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        WHERE o.DocID = :doc_id
        GROUP BY w.WordText
        ORDER BY Occurrences DESC, w.WordText
        """,
        {"doc_id": int(doc_id)}
    )

    return [
        {
            "word": row["wordtext"],
            "occurrences": row["occurrences"],
            "char_count": row["charcount"],
        }
        for row in rows
    ]


def corpus_overview():
    """Returns the main statistics shown on the Home screen."""

    totals = db.run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM Documents) AS doc_count,
            (SELECT COUNT(*) FROM Authors) AS author_count,
            (SELECT COUNT(*) FROM Words) AS unique_words,
            (SELECT COUNT(*) FROM Occurrences) AS occ_count,
            (SELECT COUNT(*) FROM Groups) AS group_count,
            (SELECT COUNT(*) FROM Phrases) AS phrase_count,
            (
                SELECT COUNT(*)
                FROM (
                    SELECT o.WordID
                    FROM Occurrences o
                    GROUP BY o.WordID
                    HAVING COUNT(*) = 1
                )
            ) AS hapax_count,
            (
                SELECT NVL(ROUND(AVG(LENGTH(w.WordText)), 2), 0)
                FROM Occurrences o
                JOIN Words w ON w.WordID = o.WordID
            ) AS avg_word_length
        FROM dual
        """
    )[0]

    return {
        "documents": totals["doc_count"],
        "authors": totals["author_count"],
        "unique_words": totals["unique_words"],
        "occurrences": totals["occ_count"],
        "hapax": totals["hapax_count"],
        "groups": totals["group_count"],
        "phrases": totals["phrase_count"],
        "avg_word_length": totals["avg_word_length"],
    }


def documents_per_author():
    """Returns the number of documents for each author."""

    rows = db.run_query(
        """
        SELECT a.AuthorName,
               COUNT(d.DocID) AS Documents
        FROM Authors a
        LEFT JOIN Documents d ON d.AuthorID = a.AuthorID
        GROUP BY a.AuthorName
        ORDER BY Documents DESC, a.AuthorName
        """
    )

    return [
        {
            "author": row["authorname"],
            "documents": row["documents"]
        }
        for row in rows
    ]