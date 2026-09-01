"""Popup windows and file dialogs of the Concordance System.

Includes occurrence viewing, document statistics,
and text/XML load, import and export actions.
"""

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

import engine
import loader
import xml_io
from ui.widgets import (
    COLORS,
    RADIUS_CONTROL,
    Table,
    frame,
    label,
    button,
    entry,
    value_bar,
    font,
    fmt,
    Spin,
)


class OccurrencePopup(ctk.CTkToplevel):
    """Shows one word or phrase occurrence with its context.

    The context is rebuilt from the occurrence records.
    span tells how many words should be highlighted.
    """

    def __init__(self, master, app, header, occurrences, span=1):
        super().__init__(master)

        self.app = app
        self.occurrences = occurrences
        self.span = span

        # Index of the occurrence currently shown.
        self.index = 0

        self.title(header)
        self.configure(fg_color=COLORS["panel"])
        self.transient(master)
        self.resizable(False, False)

        # ---------- Main area ----------

        body = frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        self._header = label(body, "", size=13, weight="bold")
        self._header.pack(anchor="w")

        # ---------- Navigation ----------

        nav = frame(body)
        nav.pack(fill="x", pady=(10, 8))

        self._prev = button(nav, "< Previous", lambda: self.step(-1), width=110)
        self._prev.pack(side="left")

        self._next = button(nav, "Next >", lambda: self.step(1), width=90)
        self._next.pack(side="left", padx=(6, 0))

        label(nav, "Go to #", color="muted").pack(side="left", padx=(16, 4))

        # Lets the user jump directly to an occurrence number.
        self._goto = Spin(
            nav,
            from_=1,
            to=max(1, len(occurrences)),
            command=self._goto_changed
        )
        self._goto.pack(side="left")
        self._goto.bind_return(self._goto_changed)

        # ---------- Context text ----------

        self.text = ctk.CTkTextbox(
            body,
            width=560,
            height=112,
            wrap="word",
            corner_radius=RADIUS_CONTROL,
            fg_color=COLORS["panel_2"],
            border_color=COLORS["line"],
            border_width=1,
            text_color=COLORS["ink"],
            font=font(12, mono=True)
        )
        self.text.pack(fill="x")

        # Normal context and highlighted match use different styles.
        self.text.tag_config(
            "ctx",
            foreground=COLORS["muted"]
        )

        self.text.tag_config(
            "hit",
            background=COLORS["hit"],
            foreground="#3a2c00"
        )

        self.text.configure(state="disabled")

        # ---------- Occurrence details ----------

        meta = frame(body)
        meta.pack(fill="x", pady=(10, 0))

        label(
            meta,
            "Document",
            color="muted"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12)
        )

        self._doc_link = label(meta, "", color="accent_ink")
        self._doc_link.grid(row=0, column=1, sticky="w")

        label(
            meta,
            "Location",
            color="muted"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12)
        )

        self._location = label(meta, "")
        self._location.grid(row=1, column=1, sticky="w")

        label(
            body,
            "Context is reconstructed from the occurrence records. "
            "The full text is not stored.",
            color="muted",
            wraplength=520
        ).pack(
            anchor="w",
            pady=(8, 0)
        )

        button(
            body,
            "Close",
            self.destroy,
            width=90
        ).pack(
            anchor="e",
            pady=(12, 0)
        )

        # Show the first occurrence when data exists.
        if occurrences:
            self.render()
        else:
            self._header.configure(text=header + "  (no occurrences)")

        self.lift()
        self.focus_force()

    def step(self, delta):
        """Moves to the previous or next occurrence."""

        self.index = max(
            0,
            min(
                len(self.occurrences) - 1,
                self.index + delta
            )
        )

        self.render()

    def _goto_changed(self):
        """Moves directly to the selected occurrence number."""

        value = self._goto.value()

        if value is None:
            return

        # The control starts at 1, while list indexes start at 0.
        self.index = max(
            0,
            min(
                len(self.occurrences) - 1,
                value - 1
            )
        )

        self.render()

    def render(self):
        """Displays the current occurrence and its context."""

        occurrence = self.occurrences[self.index]

        self._header.configure(
            text=(
                f"{self.index + 1} / "
                f"{len(self.occurrences)} occurrence(s)"
            )
        )

        # Rebuild the surrounding text from stored occurrences.
        context = engine.context(
            occurrence["doc_id"],
            occurrence["line"]
        )

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        if context["before"]:
            self.text.insert("end", context["before"] + "\n", "ctx")

        # Highlight the current word or phrase.
        self._insert_hit_line(
            context["line"] or "",
            occurrence["position"]
        )

        if context["after"]:
            self.text.insert("end", "\n" + context["after"], "ctx")

        self.text.configure(state="disabled")

        # Show the exact position of the occurrence.
        self._location.configure(
            text=(
                f"Paragraph {occurrence['paragraph']}  ·  "
                f"Line {occurrence['line']}  ·  "
                f"Word {occurrence['position']}"
            )
        )

        # Clicking the document title opens that document.
        self._doc_link.configure(text=occurrence["title"])

        self._doc_link.bind(
            "<Button-1>",
            lambda event, doc_id=occurrence["doc_id"]:
            self._open_doc(doc_id)
        )

        # Disable navigation at the first and last occurrence.
        self._prev.configure(
            state="disabled" if self.index == 0 else "normal"
        )

        self._next.configure(
            state=(
                "disabled"
                if self.index >= len(self.occurrences) - 1
                else "normal"
            )
        )

    def _insert_hit_line(self, line, position):
        """Adds the line and highlights the matching words."""

        words = line.split(" ") if line else []

        # Convert the stored word position to a list index.
        start = position - 1
        end = start + self.span

        for index, word in enumerate(words):
            tag = "hit" if start <= index < end else ()

            self.text.insert("end", word, tag)

            if index < len(words) - 1:
                self.text.insert("end", " ")

    def _open_doc(self, doc_id):
        """Closes the popup and opens the selected document."""

        self.destroy()
        self.app.show_document(doc_id)


class DocumentStatsPopup(ctk.CTkToplevel):
    """Shows statistics for one or more selected documents."""

    def __init__(self, master, app, doc_ids):
        super().__init__(master)

        self.app = app
        self.doc_ids = doc_ids

        self.title("Document statistics")
        self.configure(fg_color=COLORS["panel"])
        self.transient(master)

        self.body = frame(self)
        self.body.pack(fill="both", expand=True, padx=16, pady=14)

        # One document gets a detailed statistics view.
        if len(doc_ids) == 1:
            self._build_single(doc_ids[0])
        else:
            self._build_multi(doc_ids)

        self.lift()
        self.focus_force()

    def _build_single(self, doc_id):
        """Builds the statistics view for one document."""

        stats = engine.document_stats(doc_id)

        if not stats:
            label(self.body, "No statistics for this document.").pack()
            return

        label(
            self.body,
            stats["title"],
            size=13,
            weight="bold"
        ).pack(anchor="w")

        # ---------- Basic statistics ----------

        grid = frame(self.body)
        grid.pack(fill="x", pady=(10, 6))

        rows = [
            ("Total words", fmt(stats["total_words"])),
            ("Unique words", fmt(stats["unique_words"])),
            ("Average word length", f"{stats['avg_word_length']} chars"),
            ("Paragraphs", fmt(stats["paragraphs"])),
        ]

        for index, (text, value) in enumerate(rows):
            label(
                grid,
                text,
                color="muted"
            ).grid(
                row=index,
                column=0,
                sticky="w",
                pady=2
            )

            label(
                grid,
                value
            ).grid(
                row=index,
                column=1,
                sticky="e",
                padx=(40, 0),
                pady=2
            )

        grid.grid_columnconfigure(1, weight=1)

        # ---------- Frequent words ----------

        label(
            self.body,
            "Most frequent words",
            color="muted"
        ).pack(
            anchor="w",
            pady=(8, 4)
        )

        _frequency_bars(
            self.body,
            engine.most_frequent_words(doc_id=doc_id, limit=8)
        )

        # ---------- Actions ----------

        buttons = frame(self.body)
        buttons.pack(fill="x", pady=(12, 0))

        button(
            buttons,
            "Full text",
            lambda: self._full_text(doc_id, stats["title"]),
            width=110
        ).pack(side="left")

        button(
            buttons,
            "Export to XML",
            lambda: export_document_dialog(self, doc_id),
            width=140
        ).pack(
            side="left",
            padx=6
        )

    def _build_multi(self, doc_ids):
        """Builds a comparison view for several documents."""

        label(
            self.body,
            f"{len(doc_ids)} documents",
            size=13,
            weight="bold"
        ).pack(anchor="w")

        # Table comparing the selected documents.
        table = Table(
            self.body,
            columns=[
                ("title", "Title", 240, "w"),
                ("total", "Total words", 100, "center"),
                ("unique", "Unique words", 100, "center"),
                ("paras", "Paragraphs", 90, "center"),
                ("avg", "Avg length", 90, "center"),
            ],
            height=min(12, len(doc_ids) + 1),
        )

        table.pack(fill="both", expand=True, pady=(10, 0))

        rows = []

        # Get statistics for every selected document.
        for doc_id in doc_ids:
            stats = engine.document_stats(doc_id)

            if stats:
                rows.append((
                    (
                        stats["title"],
                        fmt(stats["total_words"]),
                        fmt(stats["unique_words"]),
                        fmt(stats["paragraphs"]),
                        stats["avg_word_length"]
                    ),
                    stats
                ))

        table.set_rows(rows)

        # ---------- Frequent words ----------

        label(
            self.body,
            "Most frequent words (across the selected documents)",
            color="muted"
        ).pack(
            anchor="w",
            pady=(14, 4)
        )

        # Count words only inside the selected documents.
        combined = engine.words_in_documents(doc_ids)

        combined = sorted(
            combined,
            key=lambda word: word["occurrences"],
            reverse=True
        )[:8]

        _frequency_bars(self.body, combined)

    def _full_text(self, doc_id, title):
        """Opens the reconstructed full text of a document."""

        top = ctk.CTkToplevel(self)

        top.title(f"Full text - {title}")
        top.configure(fg_color=COLORS["panel"])

        holder = frame(top)
        holder.pack(fill="both", expand=True, padx=12, pady=12)

        # The text is rebuilt from normalized word occurrences.
        label(
            holder,
            "Reconstructed from occurrences "
            "(normalized words, no punctuation).",
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        text = ctk.CTkTextbox(
            holder,
            width=760,
            height=520,
            wrap="word",
            corner_radius=RADIUS_CONTROL,
            fg_color=COLORS["panel_2"],
            border_color=COLORS["line"],
            border_width=1,
            text_color=COLORS["ink"],
            font=font(11, mono=True)
        )

        text.pack(fill="both", expand=True)
        text.insert("1.0", engine.full_text(doc_id))

        # Full text is shown as read-only.
        text.configure(state="disabled")

        top.lift()


def _frequency_bars(master, freq):
    """Draws horizontal bars for word frequencies."""

    holder = frame(master)
    holder.pack(fill="x")

    # The largest count is used as the full bar length.
    top = max(
        (item["occurrences"] for item in freq),
        default=1
    )

    for item in freq:
        row = frame(holder)
        row.pack(fill="x", pady=2)

        label(
            row,
            item["word"],
            size=10,
            mono=True,
            anchor="w",
            width=100
        ).pack(side="left")

        # Bar size is relative to the most frequent word.
        value_bar(
            row,
            item["occurrences"] / top,
            width=230
        ).pack(side="left")

        label(
            row,
            fmt(item["occurrences"]),
            size=9,
            color="muted",
            anchor="w",
            width=56
        ).pack(
            side="left",
            padx=(8, 0)
        )


# ---------- Load / import / export ----------


class LoadDialog(ctk.CTkToplevel):
    """Loads a text file and its metadata into the database."""

    def __init__(self, master, app):
        super().__init__(master)

        self.app = app
        self.path = None

        self.title("Load text file")
        self.configure(fg_color=COLORS["panel"])
        self.transient(master)
        self.lift()
        self.focus_force()

        body = frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        label(
            body,
            "Load a .txt file",
            size=13,
            weight="bold"
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w"
        )

        label(
            body,
            "The file is split into words and positions "
            "and inserted in a single all or nothing transaction.",
            color="muted",
            wraplength=380,
            justify="left"
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(2, 10)
        )

        # ---------- File selection ----------

        self._file_label = label(
            body,
            "No file selected",
            color="muted"
        )

        button(
            body,
            "Browse ...",
            self._browse,
            width=110
        ).grid(
            row=2,
            column=0,
            sticky="w"
        )

        self._file_label.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(8, 0)
        )

        # ---------- Document metadata ----------

        self._entries = {}

        for index, (key, text) in enumerate([
            ("title", "Title"),
            ("author", "Author"),
            ("year", "Year"),
            ("source", "Source"),
        ]):
            label(
                body,
                text,
                color="muted"
            ).grid(
                row=3 + index,
                column=0,
                sticky="w",
                pady=3
            )

            field = entry(body, width=260)
            field.grid(
                row=3 + index,
                column=1,
                sticky="we",
                pady=3
            )

            self._entries[key] = field

        # ---------- Buttons ----------

        buttons = frame(body)
        buttons.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(12, 0)
        )

        button(
            buttons,
            "Cancel",
            self.destroy,
            width=90
        ).pack(
            side="right",
            padx=(6, 0)
        )

        button(
            buttons,
            "Load and commit",
            self._load,
            accent=True,
            width=150
        ).pack(side="right")

    def _browse(self):
        """Lets the user choose a text file."""

        path = filedialog.askopenfilename(
            title="Choose a text file",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if path:
            self.path = path
            self._file_label.configure(text=os.path.basename(path))

            # Suggest the file name as the title if the title is empty.
            if not self._entries["title"].get():
                guess = (
                    os.path.splitext(os.path.basename(path))[0]
                    .replace("-", " ")
                    .title()
                )

                self._entries["title"].insert(0, guess)

    def _load(self):
        """Validates the form and loads the selected document."""

        # A file must be selected first.
        if not self.path:
            messagebox.showwarning(
                "Load",
                "Please choose a file first.",
                parent=self
            )
            return

        title = self._entries["title"].get().strip()
        author = self._entries["author"].get().strip()

        # Title and author are required.
        if not title or not author:
            messagebox.showwarning(
                "Load",
                "Title and author are required.",
                parent=self
            )
            return

        year_raw = self._entries["year"].get().strip()
        year = int(year_raw) if year_raw.isdigit() else None

        source = self._entries["source"].get().strip() or None

        # Show a waiting cursor while the document is loaded.
        self.configure(cursor="watch")
        self.update_idletasks()

        try:
            summary = loader.load_document(
                self.path,
                title,
                author,
                year,
                source
            )

        except loader.LoaderError as error:
            self.configure(cursor="")

            messagebox.showerror(
                "Load failed",
                str(error),
                parent=self
            )
            return

        self.configure(cursor="")

        # Show how many words were loaded.
        messagebox.showinfo(
            "Loaded",
            (
                f"Loaded {title}: "
                f"{fmt(summary['words_loaded'])} words "
                f"({fmt(summary['unique_words'])} unique)."
            ),
            parent=self
        )

        # Refresh all screens so the new document appears everywhere.
        self.app.refresh_all()
        self.destroy()


def import_xml_dialog(master, app):
    """Imports data from an XML file."""

    path = filedialog.askopenfilename(
        title="Import from XML",
        filetypes=[
            ("XML files", "*.xml"),
            ("All files", "*.*")
        ]
    )

    if not path:
        return

    try:
        summary = xml_io.import_xml(path)

    except Exception as error:
        messagebox.showerror(
            "Import failed",
            str(error),
            parent=master
        )
        return

    # Show a summary of the imported data.
    messagebox.showinfo(
        "Import complete",
        (
            f"Documents imported: {summary['documents_imported']}\n"
            f"Documents skipped (already present): "
            f"{summary['documents_skipped']}\n"
            f"Groups: {summary['groups_imported']}\n"
            f"Phrases: {summary['phrases_imported']}"
        ),
        parent=master
    )

    app.refresh_all()


def export_database_dialog(master):
    """Exports the whole database to an XML file."""

    path = filedialog.asksaveasfilename(
        title="Export database to XML",
        defaultextension=".xml",
        filetypes=[
            ("XML files", "*.xml")
        ],
        initialfile="concordance.xml"
    )

    if not path:
        return

    try:
        xml_io.export_database(path)

    except Exception as error:
        messagebox.showerror(
            "Export failed",
            str(error),
            parent=master
        )
        return

    messagebox.showinfo(
        "Export complete",
        f"Database exported to\n{path}",
        parent=master
    )


def export_document_dialog(master, doc_id):
    """Exports one document to an XML file."""

    path = filedialog.asksaveasfilename(
        title="Export document to XML",
        defaultextension=".xml",
        filetypes=[
            ("XML files", "*.xml")
        ],
        initialfile="document.xml"
    )

    if not path:
        return

    try:
        xml_io.export_document(doc_id, path)

    except Exception as error:
        messagebox.showerror(
            "Export failed",
            str(error),
            parent=master
        )
        return

    messagebox.showinfo(
        "Export complete",
        f"Document exported to\n{path}",
        parent=master
    )