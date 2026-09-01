"""Loads all text files listed in data/corpus.csv into the database."""

import csv
import os
import sys


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

import db
import loader


DATA_DIR = os.path.join(PROJECT_DIR, "data")
MANIFEST = os.path.join(DATA_DIR, "corpus.csv")


def main():
    # Check that corpus.csv exists.
    if not os.path.exists(MANIFEST):
        print(f"No manifest found at {MANIFEST}")
        return

    db.get_connection()

    total_words = 0
    loaded = 0

    # Read the documents from the CSV file.
    with open(MANIFEST, "r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            path = os.path.join(DATA_DIR, row["filename"])
            title = row["title"]
            author = row["author"]
            year = int(row["year"]) if row.get("year") else None
            source = row.get("source") or None

            try:
                # Load one document into the database.
                summary = loader.load_document(path, title, author, year, source)

                total_words += summary["words_loaded"]
                loaded += 1

                print(
                    f"  loaded  {title:<35} "
                    f"{summary['words_loaded']:7d} words, "
                    f"{summary['unique_words']:5d} unique"
                )

            except loader.LoaderError as error:
                # If a document cannot be loaded, skip it.
                print(f"  skip    {title:<35} {error}")

    print(f"Loaded {loaded} document(s), {total_words} words in total.")

    # Update the database statistics after loading.
    if loaded:
        print("Refreshing optimizer statistics...")
        loader.refresh_statistics()

    db.close()


if __name__ == "__main__":
    main()