"""Documents screen of the Concordance System.

Allows the user to search documents, select them,
view statistics, move to their words, or export one document.
"""

from tkinter import messagebox

import engine
from ui.widgets import (
    Screen,
    Table,
    MultiSelect,
    Collapsible,
    Banner,
    ActionBar,
    frame,
    label,
    button,
    entry,
)
from ui.popups import export_document_dialog


class DocumentsScreen(Screen):
    # Rows used by the screen layout.
    _HEAD, _BANNER, _SEARCH, _CAPTION, _TABLE, _BAR, _HINT = range(7)

    def __init__(self, master, app):
        super().__init__(master, app, pad=16)

        # Keeps all documents so filters can be reset later.
        self._all_docs = []

        # ---------- Header ----------

        head = frame(self.body)
        head.grid(row=self._HEAD, column=0, sticky="ew")

        label(
            head,
            "Documents",
            size=19,
            weight="bold"
        ).pack(anchor="w")

        label(
            head,
            "Search the documents loaded into the database by their metadata.",
            color="muted"
        ).pack(anchor="w")

        # Banner is used when the screen is opened from another screen.
        self.banner = Banner(self.body)
        self.banner.set_slot(
            row=self._BANNER,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        self._build_search()

        # Shows how many documents are currently displayed.
        self._caption = label(self.body, "", color="muted")
        self._caption.grid(
            row=self._CAPTION,
            column=0,
            sticky="w",
            pady=(12, 4)
        )

        # ---------- Documents table ----------

        self.table = Table(
            self.body,
            columns=[
                ("title", "Title", 320, "w"),
                ("author", "Author", 220, "w"),
                ("year", "Year", 90, "center"),
                ("id", "DocID", 80, "center"),
            ],
            height=5,
            checkboxes=True,
            on_check=self._on_check,
            row_toggle=True
        )

        self.table.grid(
            row=self._TABLE,
            column=0,
            sticky="nsew"
        )

        # The table grows when the window size changes.
        self.body.grid_rowconfigure(self._TABLE, weight=1)

        # ---------- Actions ----------

        self.action_bar = ActionBar(self.body)
        self.action_bar.set_slot(
            row=self._BAR,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        self.action_bar.set_noun("document(s) selected")

        self.action_bar.add_button(
            "Statistics",
            self._statistics
        )

        self.action_bar.add_button(
            "Move to word list",
            self._to_words
        )

        self.action_bar.add_button(
            "Export to XML",
            self._export
        )

        label(
            self.body,
            "Tick documents, or click a row, to reveal the actions bar.",
            color="muted"
        ).grid(
            row=self._HINT,
            column=0,
            sticky="w",
            pady=(6, 0)
        )

    # ---------- Search ----------

    def _build_search(self):
        """Builds the document search panel."""

        panel = Collapsible(self.body, "Search documents")
        panel.grid(
            row=self._SEARCH,
            column=0,
            sticky="ew",
            pady=(12, 0)
        )

        grid = panel.body

        # Search by part of the document title.
        title_col = frame(grid)
        title_col.grid(
            row=0,
            column=0,
            sticky="nw",
            padx=(0, 14)
        )

        label(
            title_col,
            "Document name",
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        self._title = entry(title_col, width=200)
        self._title.pack(anchor="w")

        # Pressing Enter also runs the search.
        self._title.bind(
            "<Return>",
            lambda event: self._run_search()
        )

        # Search by one or more authors.
        self._authors = MultiSelect(
            grid,
            "Authors",
            placeholder="Any author",
            on_change=self._sync_years
        )
        self._authors.grid(
            row=0,
            column=1,
            sticky="new",
            padx=6
        )

        # Search by one or more publication years.
        self._years = MultiSelect(
            grid,
            "Year",
            placeholder="Any year"
        )
        self._years.grid(
            row=0,
            column=2,
            sticky="new",
            padx=6
        )

        for column in (1, 2):
            grid.grid_columnconfigure(
                column,
                weight=1,
                uniform="filter"
            )

        # Search and Clear buttons.
        actions = frame(grid)
        actions.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(12, 0)
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

    # ---------- Data ----------

    def refresh(self):
        """Loads all documents and updates the filters."""

        # Get the documents from the engine.
        self._all_docs = engine.documents()

        # Fill the author and year filters from the loaded data.
        self._authors.set_options(
            sorted({
                doc["author"]
                for doc in self._all_docs
            })
        )

        self._years.set_options(
            sorted({
                str(doc["year"])
                for doc in self._all_docs
                if doc["year"]
            })
        )

        self.banner.hide()
        self._show(self._all_docs)

    def _sync_years(self):
        """Updates the year options according to the selected authors."""

        authors = set(self._authors.values())

        years = sorted({
            str(doc["year"])
            for doc in self._all_docs
            if (not authors or doc["author"] in authors)
            and doc["year"]
        })

        self._years.set_options(years)

    def _show(self, docs):
        """Displays documents in the table."""

        self._caption.configure(text=f"{len(docs)} document(s).")

        self.table.set_rows([
            (
                (
                    doc["title"],
                    doc["author"],
                    doc["year"],
                    doc["doc_id"]
                ),
                doc
            )
            for doc in docs
        ])

    def _run_search(self):
        """Searches documents using the selected filters."""

        # Filtering is done by the engine in SQL.
        docs = engine.documents(
            title=self._title.get().strip() or None,
            authors=self._authors.values(),
            years=self._years.values()
        )

        self._show(docs)

    def _clear(self):
        """Clears all filters and shows every document."""

        self._title.delete(0, "end")

        # Restore all filter options.
        self._authors.set_options(
            sorted({
                doc["author"]
                for doc in self._all_docs
            })
        )

        self._years.set_options(
            sorted({
                str(doc["year"])
                for doc in self._all_docs
                if doc["year"]
            })
        )

        self._authors.clear()
        self._years.clear()

        self.banner.hide()
        self._show(self._all_docs)

    # ---------- Navigation from other screens ----------

    def show_for_word(self, word):
        """Shows only documents that contain a selected word."""

        docs = engine.documents_containing(word)

        self.banner.show(
            f'Documents containing "{word}" ({len(docs)})',
            self._clear
        )

        self._show(docs)

    def show_single(self, doc_id):
        """Shows one selected document."""

        # Load the documents if this screen has not been refreshed yet.
        if not self._all_docs:
            self._all_docs = engine.documents()

        doc = next(
            (
                item
                for item in self._all_docs
                if item["doc_id"] == doc_id
            ),
            None
        )

        if doc is None:
            return

        self.banner.show(
            f'Document: {doc["title"]}',
            self._clear
        )

        self._show([doc])

    # ---------- Actions ----------

    def _on_check(self, count):
        """Updates the action bar when documents are selected."""

        self.action_bar.update_count(count)

    def _checked_ids(self):
        """Returns the IDs of the selected documents."""

        return [
            meta["doc_id"]
            for meta in self.table.checked_meta()
        ]

    def _statistics(self):
        """Opens statistics for the selected documents."""

        ids = self._checked_ids()

        if ids:
            self.app.open_document_stats(ids)

    def _to_words(self):
        """Opens the Words screen for the selected documents."""

        metas = self.table.checked_meta()

        if not metas:
            return

        ids = [meta["doc_id"] for meta in metas]

        titles = ", ".join(
            meta["title"]
            for meta in metas
        )

        self.app.show_words_for_documents(
            ids,
            f"Words from documents: {titles}"
        )

    def _export(self):
        """Exports one selected document to XML."""

        ids = self._checked_ids()

        # Exporting from this screen is allowed for one document at a time.
        if len(ids) != 1:
            return messagebox.showinfo(
                "Export",
                "Tick exactly one document to export. "
                "Use the Home screen to export the whole database."
            )

        export_document_dialog(self.app.root, ids[0])