"""Home screen of the Concordance System.

Shows statistics about the whole database
and allows the user to load, import, or export documents.
"""

import engine
from ui.widgets import (
    COLORS,
    RADIUS_CARD,
    BORDER_INSET,
    Screen,
    Card,
    frame,
    label,
    button,
    value_bar,
    fmt,
)
from ui.popups import (
    LoadDialog,
    import_xml_dialog,
    export_database_dialog,
)


# Number of rows shown in each statistics chart.
CHART_ROWS = 8


class HomeScreen(Screen):
    # Rows used by the screen layout.
    _HEAD, _TILES, _CHARTS, _ACTIONS = range(4)

    def __init__(self, master, app):
        super().__init__(master, app)

        # ---------- Header ----------

        head = frame(self.body)
        head.grid(row=self._HEAD, column=0, sticky="ew")

        label(
            head,
            "Database Overview",
            size=19,
            weight="bold"
        ).pack(anchor="w")

        label(
            head,
            "Live statistics for the whole corpus, "
            "and a place to load more documents.",
            color="muted"
        ).pack(anchor="w")

        # ---------- Statistics cards ----------

        # This area contains the small statistic tiles.
        self._cards = frame(self.body)
        self._cards.grid(
            row=self._TILES,
            column=0,
            sticky="ew",
            pady=(14, 0)
        )

        # ---------- Charts ----------

        # The two charts share the available width.
        charts = frame(self.body)
        charts.grid(
            row=self._CHARTS,
            column=0,
            sticky="nsew",
            pady=(14, 0)
        )

        charts.grid_columnconfigure(0, weight=1, uniform="chart")
        charts.grid_columnconfigure(1, weight=1, uniform="chart")
        charts.grid_rowconfigure(0, weight=1)

        # Chart of the most common words.
        self._freq = Card(
            charts,
            "Most frequent words (corpus wide)"
        )
        self._freq.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 9)
        )

        # Chart showing how many documents belong to each author.
        self._authors = Card(
            charts,
            "Documents per author"
        )
        self._authors.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(9, 0)
        )

        # The charts grow when the window size changes.
        self.body.grid_rowconfigure(self._CHARTS, weight=1)

        # ---------- Document actions ----------

        actions = Card(
            self.body,
            "Add documents to the database"
        )
        actions.grid(
            row=self._ACTIONS,
            column=0,
            sticky="ew",
            pady=(14, 0)
        )

        row = frame(actions.body)
        row.pack(
            anchor="w",
            padx=14 - BORDER_INSET,
            pady=(0, 12 - BORDER_INSET)
        )

        # Load a regular text file.
        button(
            row,
            "Load text file ...",
            lambda: LoadDialog(self.app.root, self.app),
            accent=True,
            width=150
        ).pack(side="left")

        # Import data from XML.
        button(
            row,
            "Import from XML ...",
            lambda: import_xml_dialog(self.app.root, self.app),
            width=160
        ).pack(side="left", padx=8)

        # Export the whole database to XML.
        button(
            row,
            "Export database to XML ...",
            lambda: export_database_dialog(self.app.root),
            width=200
        ).pack(side="left")

    # ---------- Data ----------

    def refresh(self):
        """Loads and displays the database statistics."""

        # Get general statistics from the engine.
        overview = engine.corpus_overview()

        # Values shown in the small statistic cards.
        cards = [
            ("Documents", fmt(overview["documents"])),
            ("Authors", fmt(overview["authors"])),
            ("Occurrences", fmt(overview["occurrences"])),
            ("Unique words", fmt(overview["unique_words"])),
            ("Words used once", fmt(overview["hapax"])),
            ("Word groups", fmt(overview["groups"])),
            ("Phrases", fmt(overview["phrases"])),
            ("Avg. word length", str(overview["avg_word_length"])),
        ]

        # Remove the old cards before rebuilding them.
        for child in self._cards.winfo_children():
            child.destroy()

        # Create one tile for each statistic.
        for index, (text, value) in enumerate(cards):
            tile = frame(
                self._cards,
                transparent=False,
                fg_color=COLORS["panel"],
                border_width=1,
                border_color=COLORS["line"],
                corner_radius=RADIUS_CARD
            )

            # Four statistic tiles are shown in each row.
            tile.grid(
                row=index // 4,
                column=index % 4,
                sticky="nsew",
                padx=(0 if index % 4 == 0 else 9, 0),
                pady=(0 if index < 4 else 9, 0)
            )

            label(
                tile,
                text.upper(),
                size=9,
                weight="bold",
                color="muted"
            ).pack(
                anchor="w",
                padx=12,
                pady=(9, 0)
            )

            label(
                tile,
                value,
                size=20,
                weight="bold"
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 9)
            )

        # Make all four tile columns the same width.
        for column in range(4):
            self._cards.grid_columnconfigure(
                column,
                weight=1,
                uniform="stat"
            )

        # Show the most frequent words.
        self._render_bars(
            self._freq,
            engine.most_frequent_words(limit=CHART_ROWS),
            key="word",
            value="occurrences",
            mono=True,
            label_width=112
        )

        # Show the authors with the most documents.
        self._render_bars(
            self._authors,
            engine.documents_per_author()[:CHART_ROWS],
            key="author",
            value="documents",
            mono=False,
            label_width=168
        )

    def _render_bars(
        self,
        card,
        rows,
        key,
        value,
        mono=True,
        label_width=112
    ):
        """Displays rows as horizontal value bars."""

        # Remove the previous chart contents.
        card.clear_body()

        # The largest value is used to calculate the bar sizes.
        top = max(
            (row[value] for row in rows),
            default=1
        )

        for row in rows:
            line = frame(card.body)
            line.pack(
                fill="x",
                padx=16 - BORDER_INSET,
                pady=1
            )

            # Name of the word or author.
            label(
                line,
                str(row[key]),
                size=10,
                mono=mono,
                anchor="w",
                width=label_width
            ).pack(side="left")

            # Numeric value shown on the right.
            label(
                line,
                fmt(row[value]),
                size=9,
                color="muted",
                anchor="e",
                width=52
            ).pack(side="right")

            # Bar length is relative to the largest value.
            value_bar(
                line,
                row[value] / top
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(6, 10)
            )

        # Small space at the bottom of the card.
        frame(card.body, height=8 - BORDER_INSET).pack(fill="x")