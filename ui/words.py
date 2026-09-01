"""Words screen of the Concordance System.

Allows the user to search words, filter them by document data,
search by exact location, and open word occurrences in context.
"""

import tkinter as tk
from tkinter import messagebox

import engine
from ui.widgets import (
    Screen,
    Table,
    MultiSelect,
    Collapsible,
    Banner,
    Spin,
    frame,
    label,
    button,
    entry,
    checkbox,
    fmt,
)
from ui.popups import OccurrencePopup


# Number of words loaded into the table at one time.
CHUNK = 300


class WordsScreen(Screen):
    # Rows used by the screen layout.
    _HEAD, _BANNER, _SEARCH, _CAPTION, _TABLE, _FOOTER, _HINT = range(7)

    def __init__(self, master, app):
        super().__init__(master, app)

        self._docs = []
        self._title_ids = {}
        self._rows = []
        self._shown = 0

        # Stores the document filters used by the current word list.
        # The same filters are also used when opening word occurrences.
        self._scope = {}

        # ---------- Header ----------

        head = frame(self.body)
        head.grid(row=self._HEAD, column=0, sticky="ew")

        label(
            head,
            "Search by Word",
            size=19,
            weight="bold"
        ).pack(anchor="w")

        label(
            head,
            "Find words across the corpus and browse every occurrence in context.",
            color="muted"
        ).pack(anchor="w")

        # Banner appears when this screen is opened from another screen.
        self.banner = Banner(self.body)
        self.banner.set_slot(
            row=self._BANNER,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        # ---------- Search ----------

        self._build_search()

        # ---------- Results ----------

        self._caption = label(self.body, "", color="muted")
        self._caption.grid(
            row=self._CAPTION,
            column=0,
            sticky="w",
            pady=(12, 4)
        )

        self.table = Table(
            self.body,
            columns=[
                ("word", "Word", 240, "w"),
                ("occ", "Occurrences", 130, "center"),
                ("docs", "Documents", 120, "center"),
                ("groups", "Groups", 260, "w"),
            ],
            height=5
        )

        self.table.grid(row=self._TABLE, column=0, sticky="nsew")
        self.table.bind_cell_click(self._on_cell)

        # The table grows when the window size changes.
        self.body.grid_rowconfigure(self._TABLE, weight=1)

        # ---------- Footer ----------

        self._build_footer()

        label(
            self.body,
            "Click Word or Occurrences for context. "
            "Click Documents for its documents, Groups for its groups.",
            color="muted"
        ).grid(
            row=self._HINT,
            column=0,
            sticky="w",
            pady=(6, 0)
        )

    # ---------- Search area ----------

    def _build_search(self):
        """Builds the word search panel."""

        panel = Collapsible(self.body, "Search words")
        panel.grid(
            row=self._SEARCH,
            column=0,
            sticky="ew",
            pady=(12, 0)
        )

        grid = panel.body

        # ---------- Word ----------

        word_column = frame(grid)
        word_column.grid(row=0, column=0, sticky="nw", padx=(0, 14))

        label(
            word_column,
            "Word",
            color="muted"
        ).pack(anchor="w", pady=(0, 3))

        self._word = entry(word_column, width=150)
        self._word.pack(anchor="w")

        # Pressing Enter runs the search.
        self._word.bind("<Return>", lambda event: self._run_search())

        # ---------- Document filters ----------

        self._authors = MultiSelect(
            grid,
            "Authors",
            placeholder="All authors",
            on_change=self._sync_filters
        )
        self._authors.grid(row=0, column=1, sticky="new", padx=6)

        self._years = MultiSelect(
            grid,
            "Year published",
            placeholder="All years",
            on_change=self._sync_filters
        )
        self._years.grid(row=0, column=2, sticky="new", padx=6)

        self._titles = MultiSelect(
            grid,
            "Title (document)",
            placeholder="All documents",
            on_change=self._sync_location
        )
        self._titles.grid(row=0, column=3, sticky="new", padx=6)

        # ---------- Location search ----------

        location = frame(grid)
        location.grid(row=0, column=4, sticky="nw", padx=(14, 0))

        self._loc_hint = label(
            location,
            "By location (pick one document first)",
            color="muted",
            wraplength=180,
            justify="left"
        )
        self._loc_hint.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 3)
        )

        self._loc = {}

        # Location can be limited by paragraph, line and word position.
        for index, (key, text) in enumerate([
            ("p", "Paragraph"),
            ("l", "Line"),
            ("w", "Word #"),
        ]):
            checked = tk.BooleanVar()

            check = checkbox(location, text, checked, self._sync_location)
            check.grid(row=index + 1, column=0, sticky="w")

            spin = Spin(location, from_=1, to=99999)
            spin.grid(
                row=index + 1,
                column=1,
                sticky="w",
                padx=(6, 0)
            )

            self._loc[key] = {
                "checked": checked,
                "check": check,
                "spin": spin
            }

        # Give the document filter columns equal width.
        for column in range(1, 4):
            grid.grid_columnconfigure(column, weight=1, uniform="filter")

        # ---------- Search actions ----------

        actions = frame(grid)
        actions.grid(
            row=1,
            column=0,
            columnspan=5,
            sticky="w",
            pady=(10, 0)
        )

        button(
            actions,
            "Search",
            self._run_search,
            accent=True,
            width=100
        ).pack(side="left")

        button(
            actions,
            "Clear",
            self._clear,
            width=90
        ).pack(side="left", padx=8)

        self._sync_location()

    def _build_footer(self):
        """Builds the paging area under the results table."""

        bar = frame(self.body)
        bar.grid(
            row=self._FOOTER,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        # Loads the next group of words into the table.
        self._load_more = button(
            bar,
            "Load more",
            self._load_next,
            width=110
        )
        self._load_more.pack(side="left")

        # Shows how many words are currently visible.
        self._status = label(bar, "", color="muted")
        self._status.pack(side="left", padx=12)

    def _sync_location(self):
        """Enables location search only when one document is selected."""

        selected_titles = self._titles.values()
        single = len(selected_titles) == 1

        if single:
            self._loc_hint.configure(
                text=f"By location ({selected_titles[0]})"
            )
        else:
            self._loc_hint.configure(
                text="By location (pick one document first)"
            )

        # Location controls only make sense inside one document.
        for key, widget in self._loc.items():
            widget["check"].configure(
                state="normal" if single else "disabled"
            )

            if not single:
                widget["checked"].set(False)

            spin_on = single and widget["checked"].get()
            widget["spin"].set_state(
                "normal" if spin_on else "disabled"
            )

    def _sync_filters(self):
        """Updates years and titles according to the selected filters."""

        authors = set(self._authors.values())

        # Show only years that belong to the selected authors.
        years_for_authors = sorted({
            str(document["year"])
            for document in self._docs
            if (not authors or document["author"] in authors)
            and document["year"]
        })

        self._years.set_options(years_for_authors)

        chosen_years = set(self._years.values())

        # Show only titles that match the selected authors and years.
        titles = sorted({
            document["title"]
            for document in self._docs
            if (not authors or document["author"] in authors)
            and (
                not chosen_years
                or str(document["year"]) in chosen_years
            )
        })

        self._titles.set_options(titles)
        self._sync_location()

    # ---------- Data ----------

    def refresh(self):
        """Loads the word index and document filter options."""

        self._docs = engine.documents()

        self._authors.set_options(engine.list_authors())
        self._years.set_options(engine.list_years())
        self._titles.set_options(engine.list_document_titles())

        # Connect document titles to their IDs for location searches.
        self._title_ids = {
            document["title"]: document["doc_id"]
            for document in self._docs
        }

        self._scope = {}
        rows = engine.search_words()

        self.banner.hide()
        self._show(rows, "Showing the full word index, sorted by frequency.")

    def _scope_note(self):
        """Returns a note when counts are limited by document filters."""

        if not self._scope:
            return ""

        return (
            " Occurrences and Documents are counted "
            "within the current filter."
        )

    def _row_tuple(self, row):
        """Converts one engine result to the format used by the table."""

        return (
            (
                row["word"],
                fmt(row["occurrences"]),
                row["documents"],
                row["groups"] or "-"
            ),
            row
        )

    def _show(self, rows, caption):
        """Shows a new list of words."""

        self._rows = rows
        self._shown = 0
        self._caption.configure(text=caption)

        # Clear old results before loading the first chunk.
        self.table.set_rows([])
        self._load_next()

    def _load_next(self):
        """Loads the next chunk of words into the table."""

        start = self._shown
        end = min(start + CHUNK, len(self._rows))

        self.table.add_rows([
            self._row_tuple(row)
            for row in self._rows[start:end]
        ])

        self._shown = end
        self._refresh_footer()

    def _refresh_footer(self):
        """Updates the paging message and Load more button."""

        total = len(self._rows)

        if total == 0:
            self._status.configure(text="No matching words.")
        else:
            self._status.configure(
                text=f"Showing {fmt(self._shown)} of {fmt(total)} word(s)."
            )

        self._load_more.configure(
            state="normal" if self._shown < total else "disabled"
        )

    # ---------- Search actions ----------

    def _run_search(self):
        """Searches words using the selected filters."""

        titles = self._titles.values()

        # If a location filter is selected, use location search instead.
        if (
            len(titles) == 1
            and any(
                self._loc[key]["checked"].get()
                for key in self._loc
            )
        ):
            return self._run_location(titles[0])

        # Store only filters that have values.
        self._scope = {
            key: value
            for key, value in [
                ("authors", self._authors.values()),
                ("years", self._years.values()),
                ("titles", titles),
            ]
            if value
        }

        rows = engine.search_words(
            word=self._word.get().strip() or None,
            **self._scope
        )

        self._show(
            rows,
            f"Showing {fmt(len(rows))} word(s), sorted by frequency."
            f"{self._scope_note()}"
        )

    def _run_location(self, title):
        """Searches for words at a selected document location."""

        doc_id = self._title_ids.get(title)

        use_paragraph = self._loc["p"]["checked"].get()
        use_line = self._loc["l"]["checked"].get()
        use_word = self._loc["w"]["checked"].get()

        # Word position only has meaning inside a line.
        if use_word and not use_line:
            return messagebox.showwarning(
                "Location",
                "To locate by word position, also select line."
            )

        paragraph = self._loc["p"]["spin"].value() if use_paragraph else None
        line = self._loc["l"]["spin"].value() if use_line else None
        position = self._loc["w"]["spin"].value() if use_word else None

        # Find the words stored at the selected location.
        found = engine.locate_by_position(
            doc_id,
            paragraph,
            line,
            position
        )

        # A location search is always limited to one document.
        self._scope = {"doc_ids": [doc_id]}

        # Get word statistics only for this document.
        word_index = {
            row["word"]: row
            for row in engine.search_words(**self._scope)
        }

        rows = [
            word_index.get(
                item["word"],
                {
                    "word": item["word"],
                    "occurrences": 0,
                    "documents": 0,
                    "groups": None
                }
            )
            for item in found
        ]

        # Build a readable description of the selected location.
        where = " · ".join(
            part
            for part in [
                f"paragraph {paragraph}" if paragraph else None,
                f"line {line}" if line else None,
                f"word {position}" if position else None,
            ]
            if part
        )

        self._show(
            rows,
            f'{fmt(len(rows))} word(s) at {where} in "{title}".'
            f"{self._scope_note()}"
        )

    def _clear(self):
        """Clears all filters and restores the full word index."""

        self._word.delete(0, "end")

        # Restore all filter options.
        self._authors.set_options(engine.list_authors())
        self._years.set_options(engine.list_years())
        self._titles.set_options(engine.list_document_titles())

        self._authors.clear()
        self._years.clear()
        self._titles.clear()

        # Clear location filters.
        for widget in self._loc.values():
            widget["checked"].set(False)

        self._sync_location()
        self.banner.hide()

        self._scope = {}
        rows = engine.search_words()

        self._show(rows, "Showing the full word index, sorted by frequency.")

    # ---------- Navigation from other screens ----------

    def show_for_documents(self, doc_ids, label_text):
        """Shows words only from selected documents."""

        self._scope = {"doc_ids": list(doc_ids)} if doc_ids else {}
        rows = engine.search_words(**self._scope)

        self.banner.show(label_text, self._clear)

        self._show(
            rows,
            f"Showing {fmt(len(rows))} word(s) from the selected document(s)."
            f"{self._scope_note()}"
        )

    def show_for_group(self, name):
        """Shows words that belong to one selected group."""

        # A group does not limit the results to specific documents.
        self._scope = {}

        rows = engine.search_words(group=name)

        self.banner.show(
            f"Words in group: {name}",
            self._clear
        )

        self._show(
            rows,
            f'Showing {fmt(len(rows))} word(s) in group "{name}".'
        )

    # ---------- Table actions ----------

    def _on_cell(self, meta, key):
        """Handles clicks on cells in the word results table."""

        word = meta["word"]

        # Clicking Word or Occurrences opens the KWIC viewer.
        if key in ("word", "occ"):
            # Use the same scope as the current table.
            occurrences = engine.kwic(word, **self._scope)

            OccurrencePopup(
                self.app.root,
                self.app,
                f'Occurrences of "{word}"',
                occurrences,
                span=1
            )

        # Clicking Documents opens the matching documents.
        elif key == "docs":
            self.app.show_documents_for_word(word)

        # Clicking Groups opens the matching groups.
        elif key == "groups":
            self.app.show_groups_for_word(word)