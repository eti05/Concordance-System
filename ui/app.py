"""Main window of the Concordance System.

Builds the tabs, handles navigation, and manages the database connection.
"""

from tkinter import messagebox

import customtkinter as ctk

import db
import engine

from ui.widgets import (
    setup_styles,
    fmt,
    COLORS,
    frame,
    label,
    button,
    RADIUS_CARD,
)
from ui.home import HomeScreen
from ui.words import WordsScreen
from ui.documents import DocumentsScreen
from ui.groups import GroupsScreen
from ui.popups import DocumentStatsPopup


class ConcordanceApp:
    # Size of each tab.
    TAB_HEIGHT = 38
    TAB_WIDTH = 104

    def __init__(self, root):
        self.root = root

        # Main window settings.
        root.title("Concordance System")
        root.geometry("1180x820")
        root.minsize(900, 600)

        setup_styles(root)

        self.connected = False

        # Build the main parts of the window.
        self._build_appbar()
        self._build_tabs()
        self._build_statusbar()

        # Connect to Oracle and load the data.
        self.connect()
        self.refresh_all()

    # ---------- Top bar ----------

    def _build_appbar(self):
        """Creates the top bar."""

        bar = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["panel"],
            corner_radius=0
        )
        bar.pack(fill="x")

        sep = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["line"],
            height=1,
            corner_radius=0
        )
        sep.pack(fill="x")

        # Small logo.
        logo = ctk.CTkLabel(
            bar,
            text="C",
            width=30,
            height=30,
            corner_radius=6,
            fg_color=COLORS["accent"],
            text_color="#ffffff",
            font=("", 15, "bold")
        )
        logo.pack(side="left", padx=(16, 12), pady=11)

        # Application title.
        titles = frame(bar)
        titles.pack(side="left")

        label(
            titles,
            "Concordance System",
            size=15,
            weight="bold"
        ).pack(anchor="w")

        label(
            titles,
            "20563 Database Workshop  ·  Spring 2026  ·  "
            "Children's classics (Project Gutenberg)",
            size=9,
            color="muted"
        ).pack(anchor="w")

        # Reconnect button appears only when the connection is lost.
        self._reconnect = button(
            bar,
            "Reconnect",
            self._reconnect_clicked,
            accent=True,
            width=100,
            height=28
        )

    # ---------- Tabs ----------

    def _build_tabs(self):
        """Creates the four application tabs."""

        self._tabbar = frame(
            self.root,
            transparent=False,
            fg_color=COLORS["bg"],
            corner_radius=0,
            height=self.TAB_HEIGHT
        )
        self._tabbar.pack(fill="x", pady=(6, 0))

        # Container for all screens.
        content = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["panel"],
            corner_radius=0
        )
        content.pack(fill="both", expand=True)

        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Create the screens.
        self.home = HomeScreen(content, self)
        self.words = WordsScreen(content, self)
        self.documents = DocumentsScreen(content, self)
        self.groups = GroupsScreen(content, self)

        self._screens = {
            "home": self.home,
            "words": self.words,
            "documents": self.documents,
            "groups": self.groups
        }

        # All screens use the same place in the window.
        for screen in self._screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        self._tabs = {}
        self._active = None

        x = 12

        # Create the tab buttons.
        for name, text in [
            ("home", "Home"),
            ("words", "Words"),
            ("documents", "Documents"),
            ("groups", "Groups")
        ]:
            tab = ctk.CTkLabel(
                self._tabbar,
                text=text,
                font=("", 11, "bold"),
                width=self.TAB_WIDTH,
                height=self.TAB_HEIGHT + RADIUS_CARD,
                corner_radius=RADIUS_CARD,
                fg_color=COLORS["bg"],
                text_color=COLORS["muted"]
            )

            tab.place(x=x, y=0)
            x += self.TAB_WIDTH + 4

            # Mouse actions for the tab.
            tab.bind("<Button-1>", lambda event, n=name: self.go(n))
            tab.bind("<Enter>", lambda event, n=name: self._hover_tab(n, True))
            tab.bind("<Leave>", lambda event, n=name: self._hover_tab(n, False))

            self._tabs[name] = tab

        self.go("home")

    def _hover_tab(self, name, entering):
        """Changes the tab color when the mouse is over it."""

        if name == self._active:
            return

        self._tabs[name].configure(
            text_color=COLORS["ink"] if entering else COLORS["muted"]
        )

    # ---------- Status bar ----------

    def _build_statusbar(self):
        """Creates the bottom status bar."""

        sep = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["line"],
            height=1,
            corner_radius=0
        )
        sep.pack(fill="x", side="bottom")

        bar = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["panel_2"],
            corner_radius=0
        )
        bar.pack(fill="x", side="bottom")

        # Database connection status.
        self._led = label(
            bar,
            " ● Connecting ...",
            size=9,
            color="muted"
        )
        self._led.pack(side="left", padx=12, pady=5)

        # Database totals.
        self._counts = label(bar, "", size=9, color="muted")
        self._counts.pack(side="right", padx=12)

    # ---------- Database connection ----------

    def connect(self):
        """Tries to connect to Oracle."""

        try:
            db.close()
            db.get_connection()
            self.connected = True

        except Exception as error:
            self.connected = False
            self._connect_error = error

        self._update_led()

    def _reconnect_clicked(self):
        """Tries to connect again when Reconnect is clicked."""

        self.connect()

        if self.connected:
            self.refresh_all()
        else:
            messagebox.showerror(
                "Not connected",
                "Could not connect to Oracle.\n\n"
                f"{self._connect_error}\n\n"
                "Start the database with 'docker compose up -d', "
                "wait until it is healthy, then click Reconnect."
            )

    def _update_led(self):
        """Updates the connection message in the status bar."""

        if self.connected:
            self._led.configure(
                text=" ● Oracle - Connected",
                text_color=COLORS["good"]
            )
            self._reconnect.pack_forget()
        else:
            self._led.configure(
                text=" ● Not connected",
                text_color=COLORS["error"]
            )
            self._reconnect.pack(side="right", padx=16)

    # ---------- Refresh data ----------

    def refresh_all(self):
        """Refreshes all screens."""

        if not self.connected:
            return

        try:
            self.home.refresh()
            self.words.refresh()
            self.documents.refresh()
            self.groups.refresh()

            self._update_counts()

        except Exception as error:
            self.connected = False
            self._connect_error = error

            self._update_led()

            messagebox.showerror(
                "Database error",
                str(error)
            )

    def _update_counts(self):
        """Updates the totals shown at the bottom."""

        overview = engine.corpus_overview()

        self._counts.configure(
            text=(
                f"Documents: {fmt(overview['documents'])}   ·   "
                f"Unique words: {fmt(overview['unique_words'])}   ·   "
                f"Occurrences: {fmt(overview['occurrences'])}"
            )
        )

    # ---------- Navigation ----------

    def go(self, name):
        """Opens one of the main screens."""

        self._screens[name].tkraise()

        # Highlight the active tab.
        for tab_name, tab in self._tabs.items():
            if tab_name == name:
                tab.configure(
                    fg_color=COLORS["panel"],
                    text_color=COLORS["accent_ink"]
                )
            else:
                tab.configure(
                    fg_color=COLORS["bg"],
                    text_color=COLORS["muted"]
                )

        self._active = name

    def show_documents_for_word(self, word):
        """Opens Documents and filters by a word."""

        self.go("documents")
        self.documents.show_for_word(word)

    def show_document(self, doc_id):
        """Opens one document."""

        self.go("documents")
        self.documents.show_single(doc_id)

    def show_words_for_documents(self, doc_ids, label):
        """Opens Words for selected documents."""

        self.go("words")
        self.words.show_for_documents(doc_ids, label)

    def show_words_for_group(self, name):
        """Opens Words for a selected group."""

        self.go("words")
        self.words.show_for_group(name)

    def show_groups_for_word(self, word):
        """Opens Groups for a selected word."""

        self.go("groups")
        self.groups.show_for_word(word)

    def open_document_stats(self, doc_ids):
        """Opens document statistics."""

        if doc_ids:
            DocumentStatsPopup(
                self.root,
                self,
                doc_ids
            )