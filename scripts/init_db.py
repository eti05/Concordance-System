"""Creates the database schema from the SQL files.

Use --no-reset to create the schema without deleting existing objects.
"""

import os
import sys


# Add the project folder so we can import project files.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

import db
import sqlscript


# Folder that contains the SQL files.
SQL_DIR = os.path.join(PROJECT_DIR, "sql")


# SQL files are executed in this order.
CREATE_FILES = [
    "create_tables.sql",
    "indexes.sql",
    "triggers.sql",
    "create_views.sql"
]


def run_file(filename):
    """Runs one SQL file."""

    path = os.path.join(SQL_DIR, filename)

    # Read the SQL file.
    with open(path, "r", encoding="utf-8") as file:
        sql_text = file.read()

    # Split the file into SQL statements.
    statements = sqlscript.split_statements(sql_text)

    # Run every statement.
    for statement in statements:
        db.run_command(statement)

    db.commit()

    print(f"  {filename:<20} {len(statements)} statement(s)")


def main():
    """Creates the database schema."""

    reset_database = "--no-reset" not in sys.argv

    print("Connecting to the database...")
    db.get_connection()

    # Delete the old schema unless --no-reset was used.
    if reset_database:
        print("Resetting the schema...")
        run_file("drop_all.sql")

    print("Creating the schema...")

    # Run all SQL files in the correct order.
    for filename in CREATE_FILES:
        run_file(filename)

    print("Done. The schema is ready.")
    db.close()


if __name__ == "__main__":
    main()