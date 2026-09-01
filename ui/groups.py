"""Groups and phrases screen of the Concordance System.

Allows the user to create and manage word groups and phrases,
view their statistics, and open their related words or occurrences.
"""

from tkinter import messagebox, filedialog

import customtkinter as ctk

import engine
import loader
from ui.widgets import (
    COLORS,
    RADIUS_CONTROL,
    Screen,
    Table,
    Collapsible,
    Banner,
    ActionBar,
    frame,
    label,
    button,
    entry,
    font,
    fmt,
)
from ui.popups import OccurrencePopup


class GroupsScreen(Screen):
    # Rows used by the screen layout.
    # The two table rows get extra space when the window grows.
    (
        _HEAD,
        _BANNER,
        _MANAGE,
        _GROUPS_TITLE,
        _GROUPS,
        _PHRASES_TITLE,
        _PHRASES,
        _PHRASE_ACTIONS,
        _BAR,
        _HINT,
    ) = range(10)

    def __init__(self, master, app):
        super().__init__(master, app, pad=16)

        # ---------- Header ----------

        head = frame(self.body)
        head.grid(row=self._HEAD, column=0, sticky="ew")

        label(
            head,
            "Word Groups and Phrases",
            size=19,
            weight="bold"
        ).pack(anchor="w")

        label(
            head,
            "Groups gather words with a shared meaning. "
            "Phrases are ordered word sequences.",
            color="muted"
        ).pack(anchor="w")

        # Banner is used when this screen is opened from another screen.
        self.banner = Banner(self.body)
        self.banner.set_slot(
            row=self._BANNER,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        self._build_manage()

        # ---------- Groups table ----------

        label(
            self.body,
            "Groups",
            size=13,
            weight="bold"
        ).grid(
            row=self._GROUPS_TITLE,
            column=0,
            sticky="w",
            pady=(14, 2)
        )

        self.groups_table = Table(
            self.body,
            columns=[
                ("name", "Group name", 220, "w"),
                ("words", "Words", 90, "center"),
                ("occ", "Total occurrences", 150, "center"),
                ("docs", "Documents", 110, "center"),
            ],
            height=3,
            checkboxes=True,
            on_check=self._on_group_check
        )

        self.groups_table.grid(
            row=self._GROUPS,
            column=0,
            sticky="nsew"
        )

        # Clicking a group can open its words.
        self.groups_table.bind_cell_click(self._on_group_cell)

        # ---------- Phrases table ----------

        label(
            self.body,
            "Phrases (built-in group)",
            size=13,
            weight="bold"
        ).grid(
            row=self._PHRASES_TITLE,
            column=0,
            sticky="w",
            pady=(12, 2)
        )

        self.phrases_table = Table(
            self.body,
            columns=[
                ("phrase", "Phrase", 320, "w"),
                ("occ", "Occurrences", 120, "center"),
                ("docs", "Documents", 110, "center"),
            ],
            selectmode="browse",
            height=2
        )

        self.phrases_table.grid(
            row=self._PHRASES,
            column=0,
            sticky="nsew"
        )

        # Clicking a phrase opens its occurrences.
        self.phrases_table.bind_cell_click(self._on_phrase_cell)

        # Share extra window space between the two tables.
        self.body.grid_rowconfigure(self._GROUPS, weight=3)
        self.body.grid_rowconfigure(self._PHRASES, weight=2)

        # ---------- Phrase actions ----------

        phrase_actions = frame(self.body)
        phrase_actions.grid(
            row=self._PHRASE_ACTIONS,
            column=0,
            sticky="w",
            pady=(6, 2)
        )

        button(
            phrase_actions,
            "Delete phrase",
            self._delete_phrase,
            width=130
        ).pack(side="left")

        # ---------- Group actions ----------

        self.action_bar = ActionBar(self.body)
        self.action_bar.set_slot(
            row=self._BAR,
            column=0,
            sticky="ew",
            pady=(6, 0)
        )

        self.action_bar.set_noun("group(s) selected")

        self.action_bar.add_button(
            "Move to word list",
            self._group_to_words
        )

        self.action_bar.add_button(
            "Export word list",
            self._export_group
        )

        self.action_bar.add_button(
            "Delete group",
            self._delete_group
        )

        label(
            self.body,
            "Click a group's name or word count to see its words. "
            "Click a phrase to see its occurrences.",
            color="muted"
        ).grid(
            row=self._HINT,
            column=0,
            sticky="w",
            pady=(6, 0)
        )

    # ---------- Manage panel ----------

    def _build_manage(self):
        """Builds the panel for creating groups, adding words and adding phrases."""

        panel = Collapsible(self.body, "Manage groups")
        panel.grid(
            row=self._MANAGE,
            column=0,
            sticky="ew",
            pady=(12, 0)
        )

        grid = panel.body

        # Three equal columns for the three management actions.
        for column in range(3):
            grid.grid_columnconfigure(
                column,
                weight=1,
                uniform="manage"
            )

        # ---------- Add group ----------

        add_group = frame(grid)
        add_group.grid(
            row=0,
            column=0,
            sticky="new",
            padx=(0, 16)
        )

        label(
            add_group,
            "Add group",
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        row_g = frame(add_group)
        row_g.pack(fill="x")

        self._new_group = entry(row_g, width=60)
        self._new_group.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6)
        )

        button(
            row_g,
            "Add group",
            self._add_group,
            accent=True,
            width=100
        ).pack(side="left")

        # ---------- Add word to group ----------

        add_word = frame(grid)
        add_word.grid(
            row=0,
            column=1,
            sticky="new",
            padx=(0, 16)
        )

        label(
            add_word,
            "Add word to group",
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        row_w = frame(add_word)
        row_w.pack(fill="x")

        self._add_word = entry(row_w, width=60)
        self._add_word.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6)
        )

        # Dropdown containing the existing groups.
        self._word_group = ctk.CTkOptionMenu(
            row_w,
            values=[""],
            width=110,
            height=32,
            corner_radius=RADIUS_CONTROL,
            font=font(11),
            fg_color=COLORS["panel_2"],
            button_color=COLORS["panel_2"],
            button_hover_color=COLORS["accent_weak"],
            text_color=COLORS["ink"],
            dropdown_fg_color=COLORS["panel"],
            dropdown_text_color=COLORS["ink"],
            dropdown_hover_color=COLORS["accent_weak"],
            dropdown_font=font(11)
        )

        self._word_group.pack(side="left", padx=(0, 6))

        button(
            row_w,
            "Add",
            self._add_word_to_group,
            width=70
        ).pack(side="left")

        # ---------- Add phrase ----------

        add_phrase = frame(grid)
        add_phrase.grid(row=0, column=2, sticky="new")

        label(
            add_phrase,
            "Add phrase",
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        row_p = frame(add_phrase)
        row_p.pack(fill="x")

        self._new_phrase = entry(row_p, width=60)
        self._new_phrase.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6)
        )

        button(
            row_p,
            "Add phrase",
            self._add_phrase,
            width=110
        ).pack(side="left")

        # Shows success or error messages.
        self._msg = label(grid, "", color="muted")
        self._msg.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(10, 0)
        )

    # ---------- Data ----------

    def refresh(self):
        """Loads groups and phrases from the engine."""

        groups = engine.list_groups()

        # Show group statistics in the table.
        self.groups_table.set_rows([
            (
                (
                    group["name"],
                    group["word_count"],
                    fmt(group["occurrences"]),
                    group["documents"]
                ),
                group
            )
            for group in groups
        ])

        # Update the group dropdown used when adding a word.
        names = [group["name"] for group in groups]

        # The option menu needs at least one value.
        self._word_group.configure(values=names or [""])

        if names and self._word_group.get() not in names:
            self._word_group.set(names[0])
        elif not names:
            self._word_group.set("")

        # Show all stored phrases and their statistics.
        phrases = engine.list_phrases()

        self.phrases_table.set_rows([
            (
                (
                    phrase["phrase"],
                    fmt(phrase["occurrences"]),
                    phrase["documents"]
                ),
                phrase
            )
            for phrase in phrases
        ])

        self.banner.hide()

    def show_for_word(self, word):
        """Shows only groups that contain the selected word."""

        names = set(engine.groups_of_word(word))

        groups = [
            group
            for group in engine.list_groups()
            if group["name"] in names
        ]

        self.groups_table.set_rows([
            (
                (
                    group["name"],
                    group["word_count"],
                    fmt(group["occurrences"]),
                    group["documents"]
                ),
                group
            )
            for group in groups
        ])

        self.banner.show(
            f'Groups containing "{word}": '
            f'{", ".join(sorted(names)) or "none"}',
            self.refresh
        )

    # ---------- Manage actions ----------

    def _ok(self, text):
        """Shows a success message."""

        self._msg.configure(
            text=text,
            text_color=COLORS["good"]
        )

    def _err(self, text):
        """Shows an error message."""

        self._msg.configure(
            text=text,
            text_color=COLORS["error"]
        )

    def _add_group(self):
        """Creates a new word group."""

        try:
            engine.create_group(self._new_group.get())
        except engine.EngineError as error:
            return self._err(str(error))

        self._ok(
            f'Group "{self._new_group.get().strip()}" created.'
        )

        self._new_group.delete(0, "end")

        # Refresh all screens because group data may appear elsewhere.
        self.app.refresh_all()

    def _add_word_to_group(self):
        """Adds a word to the selected group."""

        group = self._word_group.get()
        word = self._add_word.get().strip()

        if not group:
            return self._err("Choose a group first.")

        try:
            engine.add_word_to_group(group, word)
        except engine.EngineError as error:
            return self._err(str(error))

        self._ok(
            f'Added "{word.lower()}" to {group}.'
        )

        self._add_word.delete(0, "end")
        self.app.refresh_all()

    def _add_phrase(self):
        """Creates a new phrase."""

        text = self._new_phrase.get().strip()

        try:
            engine.create_phrase(text)
        except engine.EngineError as error:
            return self._err(str(error))

        self._ok(
            f'Phrase "{text}" stored.'
        )

        self._new_phrase.delete(0, "end")
        self.app.refresh_all()

    # ---------- Group table actions ----------

    def _on_group_check(self, count):
        """Updates the action bar when groups are selected."""

        self.action_bar.update_count(count)

    def _on_group_cell(self, meta, key):
        """Opens a group's words when its name or word count is clicked."""

        if key in ("name", "words"):
            self.app.show_words_for_group(meta["name"])

    def _group_to_words(self):
        """Opens the Words screen for one selected group."""

        metas = self.groups_table.checked_meta()

        if len(metas) != 1:
            return messagebox.showinfo(
                "Move to word list",
                "Tick exactly one group."
            )

        self.app.show_words_for_group(metas[0]["name"])

    def _export_group(self):
        """Exports one group's word list to a text file."""

        metas = self.groups_table.checked_meta()

        if len(metas) != 1:
            return messagebox.showinfo(
                "Export",
                "Tick exactly one group to export."
            )

        name = metas[0]["name"]

        # Ask the user where to save the text file.
        path = filedialog.asksaveasfilename(
            title="Export group word list",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"{name}.txt"
        )

        if not path:
            return

        words = engine.group_words(name)

        # Write the group and its word statistics to the file.
        with open(path, "w", encoding="utf-8") as file:
            file.write(f"Group: {name}\n")
            file.write("word\toccurrences\tdocuments\n")

            for word in words:
                file.write(
                    f"{word['word']}\t"
                    f"{word['occurrences']}\t"
                    f"{word['documents']}\n"
                )

        messagebox.showinfo(
            "Export complete",
            f"Word list exported to\n{path}"
        )

    def _delete_group(self):
        """Deletes the selected groups."""

        metas = self.groups_table.checked_meta()

        if not metas:
            return messagebox.showinfo(
                "Delete",
                "Tick one or more groups to delete."
            )

        names = [meta["name"] for meta in metas]

        # Ask for confirmation before deleting.
        if not messagebox.askyesno(
            "Delete groups",
            f'Delete: {", ".join(names)}?'
        ):
            return

        for name in names:
            engine.delete_group(name)

        self.app.refresh_all()

    # ---------- Phrase table actions ----------

    def _on_phrase_cell(self, meta, key):
        """Shows all occurrences of the selected phrase."""

        phrase = meta["phrase"]
        occurrences = engine.phrase_occurrences(phrase)

        # Number of words in the phrase is used for the highlighted span.
        span = len(loader.extract_words(phrase))

        OccurrencePopup(
            self.app.root,
            self.app,
            f'Occurrences of "{phrase}"',
            occurrences,
            span=max(1, span)
        )

    def _delete_phrase(self):
        """Deletes the selected phrase."""

        metas = self.phrases_table.selected_meta()

        if not metas:
            return messagebox.showinfo(
                "Delete",
                "Select a phrase to delete."
            )

        phrase = metas[0]["phrase"]

        # Ask for confirmation before deleting.
        if not messagebox.askyesno(
            "Delete phrase",
            f'Delete "{phrase}"?'
        ):
            return

        engine.delete_phrase(phrase)
        self.app.refresh_all()