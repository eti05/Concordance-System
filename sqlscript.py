"""Splits a SQL file into separate executable statements.

Regular SQL statements are split by semicolons.
PL/SQL blocks end with a line that contains only '/'.
"""


def _remove_comments(text):
    """Removes SQL comments without changing text inside quotes."""

    result = []
    index = 0
    length = len(text)
    in_literal = False

    while index < length:
        char = text[index]

        if in_literal:
            result.append(char)

            if char == "'":
                # Two single quotes represent one quote inside Oracle text.
                if index + 1 < length and text[index + 1] == "'":
                    result.append("'")
                    index += 2
                    continue

                in_literal = False

            index += 1

        elif char == "'":
            in_literal = True
            result.append(char)
            index += 1

        elif text.startswith("--", index):
            # Skip a line comment.
            while index < length and text[index] != "\n":
                index += 1

        elif text.startswith("/*", index):
            # Skip a block comment.
            end = text.find("*/", index + 2)
            index = length if end == -1 else end + 2

        else:
            result.append(char)
            index += 1

    return "".join(result)


def _split_outside_literals(text, separator):
    """Splits text only when the separator is outside quotes."""

    parts = []
    current = []
    in_literal = False
    index = 0

    while index < len(text):
        char = text[index]

        if in_literal:
            current.append(char)

            if char == "'":
                # Keep escaped quotes inside the text.
                if index + 1 < len(text) and text[index + 1] == "'":
                    current.append("'")
                    index += 2
                    continue

                in_literal = False

        elif char == "'":
            in_literal = True
            current.append(char)

        elif char == separator:
            parts.append("".join(current))
            current = []

        else:
            current.append(char)

        index += 1

    parts.append("".join(current))
    return parts


def split_statements(text):
    """Returns the executable SQL statements from a SQL file."""

    text = _remove_comments(text)

    statements = []
    buffer = []

    def flush_regular():
        """Adds regular SQL statements from the current buffer."""

        chunk = "\n".join(buffer)

        for part in _split_outside_literals(chunk, ";"):
            part = part.strip()

            if part:
                statements.append(part)

        buffer.clear()

    for line in text.splitlines():
        # A line containing only "/" ends a PL/SQL block.
        if line.strip() == "/":
            block = "\n".join(buffer).strip()

            if block:
                statements.append(block)

            buffer.clear()

        else:
            buffer.append(line)

    # Add any regular SQL left at the end of the file.
    flush_regular()

    return statements