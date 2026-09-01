"""XML import and export for the Concordance System.

Exports documents, groups and phrases to XML
and imports them back into the database.
"""

import datetime
import xml.etree.ElementTree as ET

import db
import engine
import loader


# Format used for document load dates in XML.
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _format_date(value):
    """Converts a date to the format stored in XML."""

    return value.strftime(_DATE_FORMAT) if value is not None else ""


def _parse_date(raw):
    """Converts an XML date back to a Python date."""

    raw = (raw or "").strip()

    if not raw:
        return None

    try:
        return datetime.datetime.strptime(raw, _DATE_FORMAT)
    except ValueError:
        return None


# ---------- Export ----------

def _document_element(doc_id, title, author, year, source, load_date=None):
    """Creates the XML element for one document."""

    doc_el = ET.Element("document")

    doc_el.set("title", title or "")
    doc_el.set("author", author or "")
    doc_el.set("year", "" if year is None else str(year))
    doc_el.set("source", source or "")
    doc_el.set("loaded", _format_date(load_date))

    # Get all word occurrences of the document.
    rows = db.run_query(
        """
        SELECT o.ParagraphNum, o.LineNum, o.WordPosition, w.WordText
        FROM Occurrences o
        JOIN Words w ON w.WordID = o.WordID
        WHERE o.DocID = :doc_id
        ORDER BY o.ParagraphNum, o.LineNum, o.WordPosition
        """,
        {"doc_id": int(doc_id)}
    )

    # Store every occurrence with its exact position.
    for row in rows:
        occ = ET.SubElement(doc_el, "occ")
        occ.set("p", str(row["paragraphnum"]))
        occ.set("l", str(row["linenum"]))
        occ.set("w", str(row["wordposition"]))
        occ.set("word", row["wordtext"])

    return doc_el


def _groups_element():
    """Creates the XML element containing all word groups."""

    groups_el = ET.Element("groups")

    rows = db.run_query(
        """
        SELECT g.GroupName, w.WordText
        FROM Groups g
        LEFT JOIN GroupMembers gm ON gm.GroupID = g.GroupID
        LEFT JOIN Words w ON w.WordID = gm.WordID
        ORDER BY g.GroupName, w.WordText
        """
    )

    groups = {}

    # Collect the words of each group.
    for row in rows:
        groups.setdefault(row["groupname"], [])

        if row["wordtext"] is not None:
            groups[row["groupname"]].append(row["wordtext"])

    # Create the XML elements.
    for name in sorted(groups):
        group_el = ET.SubElement(groups_el, "group")
        group_el.set("name", name)

        for word in groups[name]:
            ET.SubElement(group_el, "word").text = word

    return groups_el


def _phrases_element():
    """Creates the XML element containing all phrases."""

    phrases_el = ET.Element("phrases")

    rows = db.run_query(
        """
        SELECT p.PhraseText, pw.SeqNum, w.WordText
        FROM Phrases p
        JOIN PhraseWords pw ON pw.PhraseID = p.PhraseID
        JOIN Words w ON w.WordID = pw.WordID
        ORDER BY p.PhraseText, pw.SeqNum
        """
    )

    phrases = {}

    # Collect the ordered words of each phrase.
    for row in rows:
        phrases.setdefault(row["phrasetext"], []).append(
            (row["seqnum"], row["wordtext"])
        )

    # Create the XML elements.
    for text in sorted(phrases):
        phrase_el = ET.SubElement(phrases_el, "phrase")
        phrase_el.set("text", text)

        for seq, word in phrases[text]:
            word_el = ET.SubElement(phrase_el, "word")
            word_el.set("seq", str(seq))
            word_el.text = word

    return phrases_el


def _write_tree(root, path):
    """Writes an XML tree to a file."""

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def export_document(doc_id, path):
    """Exports one document to an XML file."""

    rows = db.run_query(
        """
        SELECT d.Title, a.AuthorName, d.PubYear, d.Source, d.LoadDate
        FROM Documents d
        JOIN Authors a ON a.AuthorID = d.AuthorID
        WHERE d.DocID = :doc_id
        """,
        {"doc_id": int(doc_id)}
    )

    if not rows:
        raise ValueError(f"No document with id {doc_id}.")

    meta = rows[0]

    root = ET.Element("concordance")
    documents_el = ET.SubElement(root, "documents")

    documents_el.append(
        _document_element(
            doc_id,
            meta["title"],
            meta["authorname"],
            meta["pubyear"],
            meta["source"],
            meta["loaddate"]
        )
    )

    _write_tree(root, path)

    return path


def export_database(path):
    """Exports the whole database to an XML file."""

    root = ET.Element("concordance")
    documents_el = ET.SubElement(root, "documents")

    # Get all documents and their metadata.
    docs = db.run_query(
        """
        SELECT d.DocID, d.Title, a.AuthorName, d.PubYear, d.Source, d.LoadDate
        FROM Documents d
        JOIN Authors a ON a.AuthorID = d.AuthorID
        ORDER BY d.DocID
        """
    )

    # Add every document and its occurrences.
    for doc in docs:
        documents_el.append(
            _document_element(
                doc["docid"],
                doc["title"],
                doc["authorname"],
                doc["pubyear"],
                doc["source"],
                doc["loaddate"]
            )
        )

    # Add groups and phrases.
    root.append(_groups_element())
    root.append(_phrases_element())

    _write_tree(root, path)

    return path


# ---------- Import ----------

def _import_documents(root):
    """Imports documents from XML."""

    imported = 0
    skipped = 0

    for doc_el in root.findall("./documents/document"):
        title = doc_el.get("title", "").strip()
        author = doc_el.get("author", "").strip()
        year_raw = doc_el.get("year", "").strip()
        year = int(year_raw) if year_raw else None
        source = doc_el.get("source", "").strip() or None
        load_date = _parse_date(doc_el.get("loaded"))

        # Do not import the same document twice.
        if loader.document_exists(title, author):
            skipped += 1
            continue

        tokens = []

        # Rebuild the token list from the XML occurrences.
        for occ in doc_el.findall("occ"):
            tokens.append(
                (
                    occ.get("word", "").strip().lower(),
                    int(occ.get("p")),
                    int(occ.get("l")),
                    int(occ.get("w")),
                )
            )

        loader.load_tokens(
            title,
            author,
            year,
            source,
            tokens,
            load_date
        )

        imported += 1

    return imported, skipped


def _import_groups(root):
    """Imports word groups from XML."""

    imported = 0

    for group_el in root.findall("./groups/group"):
        name = group_el.get("name", "").strip()

        if not name:
            continue

        try:
            engine.create_group(name)
        except engine.EngineConflict:
            # If the group already exists, use the existing group.
            pass

        for word_el in group_el.findall("word"):
            word = (word_el.text or "").strip().lower()

            if not word:
                continue

            try:
                engine.add_word_to_group(name, word)
            except engine.EngineConflict:
                # Skip words that do not exist in the corpus.
                pass

        imported += 1

    return imported


def _import_phrases(root):
    """Imports phrases from XML."""

    imported = 0

    for phrase_el in root.findall("./phrases/phrase"):
        text = phrase_el.get("text", "").strip()

        if not text:
            continue

        try:
            engine.create_phrase(text)
            imported += 1

        except engine.EngineConflict:
            # Skip phrases that already exist or contain missing words.
            pass

    return imported


def import_xml(path):
    """Imports documents, groups and phrases from an XML file."""

    root = ET.parse(path).getroot()

    # Import the complete XML file as one transaction.
    with db.transaction():
        documents_imported, documents_skipped = _import_documents(root)
        groups_imported = _import_groups(root)
        phrases_imported = _import_phrases(root)

    # Phrase counts may have changed after the import.
    engine.clear_phrase_cache()

    return {
        "documents_imported": documents_imported,
        "documents_skipped": documents_skipped,
        "groups_imported": groups_imported,
        "phrases_imported": phrases_imported,
    }