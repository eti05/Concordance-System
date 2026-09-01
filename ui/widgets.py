"""Shared UI widgets used by the Concordance System.

Contains the common colors, controls, tables, scrolling,
filters, banners and action bars used by the application.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

import customtkinter as ctk


# Colors used by all screens.
COLORS = {
    "bg": "#eef1f6",
    "panel": "#ffffff",
    "panel_2": "#f7f9fc",
    "ink": "#1d2433",
    "muted": "#67748c",
    "line": "#dde3ee",
    "accent": "#2f6df0",
    "accent_weak": "#e7efff",
    "accent_ink": "#1b4fc4",
    "chip": "#eef2fb",
    "chip_ink": "#33415c",
    "gray_bar": "#e9edf5",
    "slate": "#38415a",
    "slate_hi": "#4c5773",
    "hit": "#ffe24d",
    "good": "#1f9d57",
    "error": "#c0392b",
}


# Corner sizes used by cards and controls.
RADIUS_CARD = 8
RADIUS_CONTROL = 6

# Space between a bordered panel and its contents.
BORDER_INSET = 4

# Height of one row in the results tables.
ROW_HEIGHT = 30

# Font families are selected when the application starts.
FONT_FAMILY = "Helvetica"
MONO_FAMILY = "Courier"

_SANS_CHOICES = (
    "Segoe UI",
    "SF Pro Text",
    "Helvetica Neue",
    "Helvetica",
    "Arial"
)

_MONO_CHOICES = (
    "SF Mono",
    "Menlo",
    "Consolas",
    "Monaco",
    "Courier New"
)


def font(size=11, weight="normal", mono=False):
    """Returns the font used by a widget."""

    return (MONO_FAMILY if mono else FONT_FAMILY, size, weight)


def _resolve_family(choices, fallback):
    """Finds the first available font from a list."""

    available = set(tkfont.families())

    for name in choices:
        if name in available:
            return name

    return fallback


def setup_styles(root):
    """Sets the fonts and table style used by the application."""

    global FONT_FAMILY, MONO_FAMILY

    # Choose fonts that exist on the current computer.
    FONT_FAMILY = _resolve_family(_SANS_CHOICES, "Helvetica")
    MONO_FAMILY = _resolve_family(_MONO_CHOICES, "Courier")

    ctk.set_appearance_mode("light")
    root.configure(fg_color=COLORS["bg"])

    # Treeview is used for the application tables.
    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Style the results table to match the rest of the interface.
    style.configure(
        "Treeview",
        background=COLORS["panel"],
        fieldbackground=COLORS["panel"],
        foreground=COLORS["ink"],
        rowheight=ROW_HEIGHT,
        borderwidth=0,
        relief="flat",
        bordercolor=COLORS["panel"],
        lightcolor=COLORS["panel"],
        darkcolor=COLORS["panel"],
        font=font(11)
    )

    # Give the table headings a separate style.
    style.configure(
        "Treeview.Heading",
        font=font(10, "bold"),
        relief="flat",
        background=COLORS["gray_bar"],
        foreground=COLORS["chip_ink"],
        borderwidth=0,
        padding=(8, 8)
    )

    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["gray_bar"])]
    )

    style.map(
        "Treeview",
        background=[("selected", COLORS["accent_weak"])],
        foreground=[("selected", COLORS["accent_ink"])]
    )

    return FONT_FAMILY


# ---------- Common helpers ----------

def frame(master, transparent=True, **kwargs):
    """Creates a small frame used for screen layouts."""

    if transparent:
        kwargs.setdefault("fg_color", "transparent")

    kwargs.setdefault("width", 0)
    kwargs.setdefault("height", 0)

    return ctk.CTkFrame(master, **kwargs)


def label(
    master,
    text="",
    size=11,
    color="ink",
    weight="normal",
    mono=False,
    **kwargs
):
    """Creates a text label using the application style."""

    return ctk.CTkLabel(
        master,
        text=text,
        font=font(size, weight, mono),
        text_color=COLORS[color],
        fg_color="transparent",
        **kwargs
    )


def button(master, text, command, accent=False, **kwargs):
    """Creates a regular or highlighted button."""

    if accent:
        kwargs.setdefault("fg_color", COLORS["accent"])
        kwargs.setdefault("hover_color", COLORS["accent_ink"])
        kwargs.setdefault("text_color", "#ffffff")
        kwargs.setdefault("border_width", 0)
    else:
        kwargs.setdefault("fg_color", COLORS["panel_2"])
        kwargs.setdefault("hover_color", COLORS["accent_weak"])
        kwargs.setdefault("text_color", COLORS["ink"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["line"])

    kwargs.setdefault("corner_radius", RADIUS_CONTROL)
    kwargs.setdefault("height", 32)
    kwargs.setdefault("font", font(11))

    return ctk.CTkButton(master, text=text, command=command, **kwargs)


def entry(master, width=140, **kwargs):
    """Creates a text entry using the application style."""

    kwargs.setdefault("fg_color", COLORS["panel"])
    kwargs.setdefault("border_color", COLORS["line"])
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("text_color", COLORS["ink"])
    kwargs.setdefault("corner_radius", RADIUS_CONTROL)
    kwargs.setdefault("height", 32)
    kwargs.setdefault("font", font(11))

    return ctk.CTkEntry(master, width=width, **kwargs)


def checkbox(master, text, variable, command=None):
    """Creates a checkbox using the application style."""

    return ctk.CTkCheckBox(
        master,
        text=text,
        variable=variable,
        command=command,
        font=font(11),
        text_color=COLORS["ink"],
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_ink"],
        border_color=COLORS["line"],
        border_width=2,
        checkmark_color="#ffffff",
        corner_radius=4,
        checkbox_width=17,
        checkbox_height=17
    )


def value_bar(master, fraction, width=0):
    """Creates a horizontal bar used in statistics charts."""

    bar = ctk.CTkProgressBar(
        master,
        height=13,
        corner_radius=3,
        width=width,
        fg_color=COLORS["gray_bar"],
        progress_color=COLORS["accent"]
    )

    # Keep the value inside the valid progress bar range.
    bar.set(max(0.02, min(1.0, fraction)))

    return bar


def fmt(number):
    """Formats numbers with thousands separators."""

    try:
        return "{:,}".format(int(number))
    except (TypeError, ValueError):
        return str(number)


# ---------- Scrolling ----------

# Space used by one scrollbar.
BAR = 14

_SCROLLBAR_STYLE = {
    "button_color": COLORS["gray_bar"],
    "button_hover_color": COLORS["muted"],
    "fg_color": "transparent",
}


def scrollbar(master, orientation, command):
    """Creates a scrollbar used by screens and tables."""

    if orientation == "vertical":
        size = {"width": BAR, "height": 0}
    else:
        size = {"height": BAR, "width": 0}

    return ctk.CTkScrollbar(
        master,
        orientation=orientation,
        command=command,
        **size,
        **_SCROLLBAR_STYLE
    )


def _reflow_host(widget):
    """Updates the surrounding scroll area after the layout changes."""

    parent = getattr(widget, "master", None)

    # Move through the parent widgets until the ScrollHost is found.
    while parent is not None:
        if isinstance(parent, ScrollHost):
            parent.reflow()
            return

        parent = getattr(parent, "master", None)


class ScrollHost(tk.Frame):
    """A screen container that adds scrollbars when content does not fit."""

    # Widgets that already handle their own scrolling.
    SELF_SCROLLING = (
        ttk.Treeview,
        ctk.CTkScrollbar,
        ctk.CTkScrollableFrame,
        ctk.CTkTextbox,
        tk.Text
    )

    def __init__(self, master):
        super().__init__(
            master,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0
        )

        # Canvas that holds the screen content.
        self.view = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            bg=COLORS["panel"]
        )

        self._vbar = scrollbar(self, "vertical", self._yview)
        self._hbar = scrollbar(self, "horizontal", self._xview)

        self.view.configure(
            yscrollcommand=self._vbar.set,
            xscrollcommand=self._hbar.set
        )

        self.view.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Put the screen content inside the scrolling canvas.
        self.content = frame(self.view)

        self._item = self.view.create_window(
            0,
            0,
            window=self.content,
            anchor="nw"
        )

        # Stores whether vertical and horizontal bars are visible.
        self.bars = (False, False)
        self._waiting = False

        # Recalculate scrolling when the window changes size.
        self.bind("<Configure>", lambda event: self.reflow())

        self.winfo_toplevel().bind(
            "<MouseWheel>",
            self._wheel,
            add="+"
        )

    def reflow(self):
        """Recalculates the scrollbars after the layout changes."""

        if not self._waiting:
            self._waiting = True
            self.after_idle(self._apply)

    def _apply(self):
        """Checks whether horizontal or vertical scrolling is needed."""

        self._waiting = False

        if not self.winfo_exists():
            return

        # Wait for Tk to finish layout calculations before measuring.
        self.update_idletasks()

        host_width = self.winfo_width()
        host_height = self.winfo_height()

        if host_width <= 1 or host_height <= 1:
            return

        needed_width = self.content.winfo_reqwidth()
        needed_height = self.content.winfo_reqheight()

        # Decide which scrollbars are needed.
        show_vertical = needed_height > host_height

        show_horizontal = (
            needed_width > host_width - (BAR if show_vertical else 0)
        )

        # A horizontal scrollbar can reduce the available height.
        if show_horizontal and not show_vertical:
            show_vertical = needed_height > host_height - BAR

        width = max(
            host_width - (BAR if show_vertical else 0),
            needed_width
        )

        height = max(
            host_height - (BAR if show_horizontal else 0),
            needed_height
        )

        self.view.itemconfigure(
            self._item,
            width=width,
            height=height
        )

        self.view.configure(
            scrollregion=(0, 0, width, height)
        )

        # Show or hide scrollbars when their state changes.
        if (show_vertical, show_horizontal) != self.bars:
            self.bars = (show_vertical, show_horizontal)

            if show_vertical:
                self._vbar.grid(row=0, column=1, sticky="ns")
            else:
                self._vbar.grid_remove()

            if show_horizontal:
                self._hbar.grid(row=1, column=0, sticky="ew")
            else:
                self._hbar.grid_remove()

        # Move back to the start when scrolling is no longer needed.
        if not show_vertical:
            self.view.yview_moveto(0)

        if not show_horizontal:
            self.view.xview_moveto(0)

    # ---------- Scroll actions ----------

    def _yview(self, *args):
        """Moves the screen vertically."""

        # Close an open dropdown before scrolling.
        close_dropdown()
        self.view.yview(*args)

    def _xview(self, *args):
        """Moves the screen horizontally."""

        close_dropdown()
        self.view.xview(*args)

    def _wheel(self, event):
        """Handles mouse-wheel scrolling for the screen."""

        if not self.bars[0] or not self._wants_wheel(event.widget):
            return

        close_dropdown()
        self.view.yview_scroll(
            -1 if event.delta > 0 else 1,
            "units"
        )

    def _wants_wheel(self, widget):
        """Checks whether the whole screen should handle the wheel."""

        while widget is not None:
            # Leave scrolling to widgets that already scroll themselves.
            if isinstance(widget, self.SELF_SCROLLING):
                return False

            if widget is self.view:
                return True

            widget = getattr(widget, "master", None)

        return False


# ---------- Screen base ----------

class Screen(ctk.CTkFrame):
    """Base class used by the four main application screens."""

    PAD = 18

    def __init__(self, master, app, pad=None):
        super().__init__(
            master,
            fg_color=COLORS["panel"],
            corner_radius=0,
            width=0,
            height=0
        )

        self.app = app

        # Each screen is placed inside a scrolling container.
        self.scroll = ScrollHost(self)
        self.scroll.pack(fill="both", expand=True)

        pad = self.PAD if pad is None else pad

        # Screens build their controls inside body.
        self.body = frame(self.scroll.content)
        self.body.pack(
            fill="both",
            expand=True,
            padx=pad,
            pady=pad
        )

        self.body.grid_columnconfigure(0, weight=1)

    def reflow(self):
        """Updates the screen scrolling after its layout changes."""

        self.scroll.reflow()


# ---------- Card ----------

class Card(ctk.CTkFrame):
    """A bordered panel with an optional title and a content area."""

    def __init__(self, master, title=None, **kwargs):
        kwargs.setdefault("fg_color", COLORS["panel"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["line"])
        kwargs.setdefault("corner_radius", RADIUS_CARD)

        super().__init__(master, **kwargs)

        # Add a title when one was supplied.
        if title is not None:
            label(
                self,
                title,
                size=12,
                weight="bold"
            ).pack(
                anchor="w",
                padx=16,
                pady=(12, 4)
            )

        # Other widgets are placed inside body.
        self.body = frame(self)

        self.body.pack(
            fill="both",
            expand=True,
            padx=BORDER_INSET,
            pady=(
                0 if title is not None else BORDER_INSET,
                BORDER_INSET
            )
        )

    def clear_body(self):
        """Removes all widgets from the card body."""

        for child in self.body.winfo_children():
            child.destroy()


# ---------- Collapsible panel ----------

class Collapsible(ctk.CTkFrame):
    """A panel that can be expanded or collapsed by the user."""

    def __init__(self, master, title, start_collapsed=True):
        super().__init__(
            master,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["line"],
            corner_radius=RADIUS_CARD
        )

        self._collapsed = start_collapsed

        # ---------- Header ----------

        self._header = frame(self)
        self._header.pack(
            fill="x",
            padx=BORDER_INSET,
            pady=(BORDER_INSET, 0)
        )

        # Arrow showing whether the panel is open.
        self._chevron = label(
            self._header,
            "",
            color="muted",
            height=18
        )

        self._chevron.pack(
            side="left",
            anchor="n",
            padx=(12, 7),
            pady=(8, 0)
        )

        self._titles = frame(self._header)
        self._titles.pack(side="left", pady=8)

        self._title = label(
            self._titles,
            title,
            size=12,
            weight="bold",
            height=18
        )

        self._title.pack(anchor="w")

        self._hint = label(
            self._titles,
            "click to expand",
            size=9,
            color="muted",
            height=14
        )

        self._hint.pack(anchor="w")

        # Separator between the header and the content.
        self._sep = ctk.CTkFrame(
            self,
            fg_color=COLORS["line"],
            height=1,
            corner_radius=0
        )

        # Content area of the panel.
        self.body = frame(self)

        # Clicking the header toggles the panel.
        for widget in (
            self._header,
            self._chevron,
            self._titles,
            self._title,
            self._hint
        ):
            widget.bind(
                "<Button-1>",
                lambda event: self.toggle()
            )

        self._header.bind(
            "<Enter>",
            lambda event: self._title.configure(
                text_color=COLORS["accent_ink"]
            )
        )

        self._header.bind(
            "<Leave>",
            lambda event: self._title.configure(
                text_color=COLORS["ink"]
            )
        )

        self._apply()

    def toggle(self):
        """Opens or closes the panel."""

        self._collapsed = not self._collapsed
        self._apply()

    def _apply(self):
        """Updates the panel according to its current state."""

        if self._collapsed:
            self._sep.pack_forget()
            self.body.pack_forget()

            self._chevron.configure(text="▸")
            self._hint.pack(anchor="w")
            self._header.pack_configure(pady=BORDER_INSET)

        else:
            self._header.pack_configure(
                pady=(BORDER_INSET, 0)
            )

            self._sep.pack(
                fill="x",
                padx=BORDER_INSET
            )

            self.body.pack(
                fill="x",
                padx=16,
                pady=(12, 16)
            )

            self._chevron.configure(text="▾")
            self._hint.pack_forget()

        close_dropdown()
        _reflow_host(self)


# ---------- Number box ----------

class Spin(ctk.CTkFrame):
    """A small number field with up and down buttons."""

    def __init__(self, master, from_=1, to=99999, width=58, command=None):
        super().__init__(master, fg_color="transparent")

        self._from = from_
        self._to = to
        self._command = command

        # Text field that holds the number.
        self._entry = entry(
            self,
            width=width,
            height=28,
            justify="center"
        )

        self._entry.pack(side="left")
        self._entry.insert(0, str(from_))

        # Up and down buttons.
        steps = frame(self)
        steps.pack(side="left", padx=(3, 0))

        self._up = self._step_button(steps, "▴", 1)
        self._up.pack()

        self._down = self._step_button(steps, "▾", -1)
        self._down.pack(pady=(2, 0))

    def _step_button(self, master, glyph, delta):
        """Creates one of the number step buttons."""

        return ctk.CTkButton(
            master,
            text=glyph,
            width=22,
            height=12,
            corner_radius=3,
            font=font(8),
            fg_color=COLORS["panel_2"],
            hover_color=COLORS["accent_weak"],
            text_color=COLORS["muted"],
            border_width=1,
            border_color=COLORS["line"],
            command=lambda: self._step(delta)
        )

    def _step(self, delta):
        """Changes the number by one step."""

        value = self.value()

        if value is None:
            value = self._from
        else:
            value += delta

        # Keep the number inside the allowed range.
        self.set(max(self._from, min(self._to, value)))

        if self._command:
            self._command()

    def value(self):
        """Returns the current number, or None if it is invalid."""

        try:
            return int(self._entry.get().strip())
        except ValueError:
            return None

    def get(self):
        """Returns the current text in the number field."""

        return self._entry.get()

    def set(self, value):
        """Changes the current value."""

        self._entry.delete(0, "end")
        self._entry.insert(0, str(value))

    def set_range(self, from_, to):
        """Changes the allowed number range."""

        self._from = from_
        self._to = to

    def set_state(self, state):
        """Enables or disables the whole control."""

        for widget in (self._entry, self._up, self._down):
            widget.configure(state=state)

    def bind_return(self, callback):
        """Runs a callback when Enter is pressed."""

        self._entry.bind(
            "<Return>",
            lambda event: callback()
        )


# ---------- Results table ----------

class Table(ctk.CTkFrame):
    """Reusable results table based on ttk.Treeview.

    It can also show checkboxes and store metadata for each row.
    """

    _BOX_OFF = "☐"
    _BOX_ON = "☑"

    def __init__(
        self,
        master,
        columns,
        selectmode="browse",
        height=14,
        checkboxes=False,
        on_check=None,
        row_toggle=False
    ):
        super().__init__(
            master,
            fg_color="transparent",
            width=0,
            height=0
        )

        self._checkboxes = checkboxes
        self._on_check = on_check
        self._row_toggle = row_toggle
        self._checked = set()

        # Add a checkbox column when selection by checkbox is enabled.
        if checkboxes:
            columns = [
                ("__check__", self._BOX_OFF, 42, "center")
            ] + list(columns)

            selectmode = "none"

        self._columns = columns
        keys = [column[0] for column in columns]

        # ---------- Treeview ----------

        self.tree = ttk.Treeview(
            self,
            columns=keys,
            show="headings",
            selectmode=selectmode,
            height=height
        )

        # Create each table column.
        for key, heading, width, anchor in columns:
            self.tree.heading(
                key,
                text=heading,
                anchor=anchor
            )

            stretch = key != "__check__"

            self.tree.column(
                key,
                width=width,
                anchor=anchor,
                stretch=stretch,
                minwidth=42 if key == "__check__" else 60
            )

        if checkboxes:
            self.tree.heading(
                "__check__",
                command=self._toggle_all
            )

        # Different styles for alternating, checked and selected rows.
        self.tree.tag_configure(
            "stripe",
            background=COLORS["panel_2"]
        )

        self.tree.tag_configure(
            "checked",
            background=COLORS["accent_weak"]
        )

        self.tree.tag_configure(
            "chosen",
            background=COLORS["accent_weak"],
            foreground=COLORS["accent_ink"]
        )

        self._tags = {}
        self._chosen = ()

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._sync_selection,
            add="+"
        )

        # ---------- Scrolling ----------

        self._scroll = scrollbar(
            self,
            "vertical",
            self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=self._scroll.set
        )

        # Minimum number of rows to keep visible.
        self._min_rows = height

        # Keep table rows at complete heights.
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._header = max(
            0,
            self.tree.winfo_reqheight() - height * ROW_HEIGHT
        )

        self._waiting = False

        # Divider lines between columns.
        self._dividers = []
        self._drag = None

        self.configure(
            width=sum(column[2] for column in columns) + BAR,
            height=self._header + height * ROW_HEIGHT
        )

        self.bind(
            "<Configure>",
            lambda event: self._fit_rows()
        )

        self._fit_rows()

        # Metadata is stored separately from the values shown in the table.
        self._meta = {}
        self._cell_click = None

        self.tree.bind(
            "<Button-1>",
            self._on_click,
            add="+"
        )

        # Update divider lines when columns are resized.
        for sequence in (
            "<B1-Motion>",
            "<ButtonRelease-1>"
        ):
            self.tree.bind(
                sequence,
                lambda event: self._fit_rows(),
                add="+"
            )

    def _fit_rows(self):
        """Updates the table after resizing."""

        if not self._waiting:
            self._waiting = True
            self.after_idle(self._place_tree)

    def _place_tree(self):
        """Resizes the table so only complete rows are shown."""

        self._waiting = False

        if not self.winfo_exists():
            return

        # Read the final size after Tk finishes resizing.
        self.update_idletasks()

        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)

        rows = max(
            self._min_rows,
            (height - self._header) // ROW_HEIGHT
        )

        drawn = self._header + rows * ROW_HEIGHT

        self.tree.place(
            x=0,
            y=0,
            width=max(1, width - BAR),
            height=drawn
        )

        # Position the scrollbar next to the table.
        self._scroll.configure(height=drawn)

        self._scroll.place(
            x=max(1, width - BAR),
            y=0
        )

        self._place_dividers(
            max(1, width - BAR),
            rows
        )

    def _place_dividers(self, width, rows):
        """Moves the divider lines to the current column positions."""

        keys = [column[0] for column in self._columns]

        # Make sure there is one divider between each pair of columns.
        while len(self._dividers) < len(keys) - 1:
            self._dividers.append(self._divider())

        filled = min(
            len(self.tree.get_children()),
            rows
        )

        x = 0

        for divider, key in zip(
            self._dividers,
            keys[:-1]
        ):
            x += self.tree.column(key, "width")

            if not filled or x >= width:
                divider.place_forget()
                continue

            divider.configure(
                height=self._header + filled * ROW_HEIGHT
            )

            divider.place(x=x, y=0)

    def _divider(self):
        """Creates one divider between two table columns."""

        rule = ctk.CTkFrame(
            self,
            fg_color=COLORS["line"],
            width=1,
            height=0,
            corner_radius=0,
            cursor="sb_h_double_arrow"
        )

        rule.bind(
            "<Button-1>",
            lambda event, current_rule=rule:
            self._grab_rule(event, current_rule)
        )

        rule.bind(
            "<B1-Motion>",
            lambda event: self._drag_rule(event)
        )

        rule.bind(
            "<ButtonRelease-1>",
            lambda event, current_rule=rule:
            self._drop_rule(event, current_rule)
        )

        rule.lift()

        return rule

    def _grab_rule(self, event, rule):
        """Starts resizing a table column."""

        self._drag = {
            "key": self._columns[self._dividers.index(rule)][0],
            "from": event.x_root
        }

        self._drag["width"] = self.tree.column(
            self._drag["key"],
            "width"
        )

    def _drag_rule(self, event):
        """Resizes the column while its divider is dragged."""

        if not self._drag:
            return

        key = self._drag["key"]

        width = (
            self._drag["width"]
            + event.x_root
            - self._drag["from"]
        )

        self.tree.column(
            key,
            width=max(
                self.tree.column(key, "minwidth"),
                width
            )
        )

        self._fit_rows()

    def _drop_rule(self, event, rule):
        """Finishes resizing a column."""

        moved = (
            self._drag
            and abs(
                event.x_root
                - self._drag["from"]
            ) > 2
        )

        self._drag = None

        # A click without dragging belongs to the row below the divider.
        if not moved:
            self._forward_click(event, rule)

    def _forward_click(self, event, rule):
        """Passes a divider click to the table row below it."""

        event.x += rule.winfo_x()
        event.y += rule.winfo_y()

        self._on_click(event)

    # ---------- Table data ----------

    def set_rows(self, rows):
        """Replaces all rows currently shown in the table."""

        self.tree.delete(*self.tree.get_children())

        self._meta.clear()
        self._checked.clear()
        self._tags.clear()

        self._chosen = ()

        self.add_rows(rows)

        if self._checkboxes:
            self.tree.heading(
                "__check__",
                text=self._BOX_OFF
            )

            self._fire_check()

    def add_rows(self, rows):
        """Adds rows without removing the rows already shown."""

        position = len(self.tree.get_children())

        for values, meta in rows:
            # Add an empty checkbox value when needed.
            if self._checkboxes:
                values = (self._BOX_OFF,) + tuple(values)

            # Give every second row a different background.
            tags = ("stripe",) if position % 2 else ()

            item_id = self.tree.insert(
                "",
                "end",
                values=values,
                tags=tags
            )

            self._meta[item_id] = meta
            self._tags[item_id] = tags

            position += 1

        # Update column divider lengths.
        self._fit_rows()

    def _sync_selection(self, _event=None):
        """Updates the colors of selected table rows."""

        selected = tuple(self.tree.selection())

        # Restore rows that are no longer selected.
        for item_id in self._chosen:
            if (
                item_id not in selected
                and self.tree.exists(item_id)
            ):
                self.tree.item(
                    item_id,
                    tags=self._tags.get(item_id, ())
                )

        # Highlight the new selection.
        for item_id in selected:
            self.tree.item(
                item_id,
                tags=("chosen",)
            )

        self._chosen = selected

    def selected_meta(self):
        """Returns metadata for the selected table rows."""

        return [
            self._meta[item_id]
            for item_id in self.tree.selection()
            if item_id in self._meta
        ]

    def checked_meta(self):
        """Returns metadata for rows selected with checkboxes."""

        return [
            self._meta[item_id]
            for item_id in self._checked
            if item_id in self._meta
        ]

    def bind_cell_click(self, callback):
        """Sets the function called when a data cell is clicked."""

        self._cell_click = callback

    def bind_select(self, callback):
        """Runs a callback when the table selection changes."""

        self.tree.bind(
            "<<TreeviewSelect>>",
            lambda event: callback(
                self.selected_meta()
            ),
            add="+"
        )

    # ---------- Checkbox handling ----------

    def _set_checked(self, item_id, on):
        """Checks or unchecks one row."""

        if on:
            self._checked.add(item_id)

            self.tree.set(
                item_id,
                "__check__",
                self._BOX_ON
            )

            self.tree.item(
                item_id,
                tags=("checked",)
            )

        else:
            self._checked.discard(item_id)

            self.tree.set(
                item_id,
                "__check__",
                self._BOX_OFF
            )

            self.tree.item(
                item_id,
                tags=self._tags.get(item_id, ())
            )

    def _toggle_all(self):
        """Checks or unchecks all rows."""

        children = self.tree.get_children()
        turn_on = len(self._checked) < len(children)

        for item_id in children:
            self._set_checked(
                item_id,
                turn_on
            )

        self.tree.heading(
            "__check__",
            text=self._BOX_ON if turn_on else self._BOX_OFF
        )

        self._fire_check()

    def _toggle_row(self, item_id):
        """Changes the checkbox state of one row."""

        self._set_checked(
            item_id,
            item_id not in self._checked
        )

        self._fire_check()

    def _fire_check(self):
        """Reports how many rows are currently checked."""

        if self._on_check:
            self._on_check(len(self._checked))

    def _on_click(self, event):
        """Handles clicks inside the table."""

        row = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not row or not column:
            return

        # Treeview returns columns as '#1', '#2', ...
        index = int(column[1:]) - 1

        if index < 0 or index >= len(self._columns):
            return

        key = self._columns[index][0]

        # Checkbox column.
        if key == "__check__":
            self._toggle_row(row)
            return

        # Call the screen's cell-click function when one exists.
        if self._cell_click:
            meta = self._meta.get(row)

            if meta is not None:
                self._cell_click(meta, key)

            return

        # Optionally let the whole row toggle the checkbox.
        if self._checkboxes and self._row_toggle:
            self._toggle_row(row)


# ---------- Multi-select dropdown ----------

# Only one multi-select dropdown can be open at a time.
_open_multi = None


def close_dropdown():
    """Closes the currently open multi-select dropdown."""

    if _open_multi is not None:
        _open_multi._close()


class MultiSelect(ctk.CTkFrame):
    """A dropdown that allows the user to select several values.

    An empty selection means that all values are included.
    """

    # Maximum and minimum height of the dropdown list.
    LIST_MAX = 230
    LIST_MIN = 90

    def __init__(
        self,
        master,
        label_text,
        values=(),
        on_change=None,
        placeholder=None,
        height=None
    ):
        super().__init__(
            master,
            fg_color="transparent",
            width=0,
            height=0
        )

        self._on_change = on_change
        self._placeholder = (
            placeholder
            or "All " + label_text.lower()
        )

        self._values = []
        self._selected = set()

        self._popup = None
        self._is_open = False
        self._close_id = None

        # ---------- Label ----------

        label(
            self,
            label_text,
            color="muted"
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        # ---------- Selection box ----------

        self._box = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["line"],
            corner_radius=RADIUS_CONTROL,
            width=130,
            height=32
        )

        self._box.pack(fill="x")
        self._box.pack_propagate(False)

        # Text showing the current selection.
        self._summary = label(
            self._box,
            "",
            color="muted",
            anchor="w"
        )

        self._summary.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 4)
        )

        # Arrow shown on the right side.
        self._arrow = label(
            self._box,
            "▾",
            size=10,
            color="muted"
        )

        self._arrow.pack(
            side="right",
            padx=(0, 10)
        )

        # Clicking any part of the box opens the dropdown.
        for widget in (
            self._box,
            self._summary,
            self._arrow
        ):
            widget.bind(
                "<Button-1>",
                lambda event: self._toggle()
            )

        self.set_options(values)

    # ---------- Public actions ----------

    def set_options(self, values):
        """Sets the possible values shown in the dropdown."""

        self._values = [
            str(value)
            for value in values
        ]

        # Remove selections that no longer exist.
        self._selected &= set(self._values)

        self._render_summary()

    def values(self):
        """Returns the selected values in their original display order."""

        return [
            value
            for value in self._values
            if value in self._selected
        ]

    def set_values(self, chosen):
        """Changes the current selected values."""

        self._selected = {
            str(value)
            for value in chosen
        } & set(self._values)

        self._render_summary()

    def clear(self):
        """Clears the current selection."""

        self._selected.clear()
        self._render_summary()

    # ---------- Selection summary ----------

    def _render_summary(self):
        """Updates the text shown inside the selection box."""

        chosen = self.values()

        # No selection means all values.
        if not chosen:
            self._summary.configure(
                text=self._placeholder,
                text_color=COLORS["muted"]
            )

        # Show the selected values directly when there are only one or two.
        elif len(chosen) <= 2:
            self._summary.configure(
                text=", ".join(chosen),
                text_color=COLORS["ink"]
            )

        # For larger selections show only the count.
        else:
            self._summary.configure(
                text=f"{len(chosen)} selected",
                text_color=COLORS["ink"]
            )

    # ---------- Dropdown ----------

    def _toggle(self):
        """Opens or closes the dropdown."""

        if self._is_open:
            self._close()
        else:
            self._open()

    def _build_popup(self):
        """Creates the dropdown list the first time it is opened."""

        self._popup = ctk.CTkFrame(
            self.winfo_toplevel(),
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["line"],
            corner_radius=RADIUS_CONTROL,
            width=0,
            height=0
        )

        # ---------- Dropdown header ----------

        self._head = frame(self._popup)

        self._head.pack(
            fill="x",
            padx=6,
            pady=(6, 0)
        )

        self._link_button(
            self._head,
            "Select all",
            self._select_all,
            COLORS["accent_ink"]
        ).pack(side="left")

        self._link_button(
            self._head,
            "Clear",
            self._clear_all,
            COLORS["muted"]
        ).pack(
            side="left",
            padx=(4, 0)
        )

        # ---------- Options list ----------

        # The list becomes scrollable when there are many options.
        self._rows_host = ctk.CTkScrollableFrame(
            self._popup,
            fg_color=COLORS["panel"],
            width=0,
            height=0,
            corner_radius=0
        )

        self._rows_host.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=6
        )

        # The dropdown size is calculated when it opens.
        self._popup.pack_propagate(False)

    def _open(self):
        """Opens and positions the dropdown."""

        global _open_multi

        # Close another MultiSelect if one is already open.
        if (
            _open_multi is not None
            and _open_multi is not self
        ):
            _open_multi._close()

        _open_multi = self

        top = self.winfo_toplevel()

        # Build the popup only once.
        if self._popup is None:
            self._build_popup()

        # Rebuild the current option rows.
        for row in self._rows_host.winfo_children():
            row.destroy()

        self._option_rows = {}

        for value in self._values:
            self._build_option_row(value)

        top.update_idletasks()

        # ---------- Calculate popup position ----------

        # Space used by the header and padding.
        chrome = self._head.winfo_reqheight() + 18

        # Height needed to display all options.
        wanted = self._rows_host.winfo_reqheight()

        box_x = (
            self._box.winfo_rootx()
            - top.winfo_rootx()
        )

        box_y = (
            self._box.winfo_rooty()
            - top.winfo_rooty()
        )

        below = (
            top.winfo_height()
            - (
                box_y
                + self._box.winfo_height()
            )
            - 10
        )

        above = box_y - 10

        # Open below when there is enough space.
        # Otherwise use the side with more room.
        downward = (
            below >= wanted + chrome
            or below >= above
        )

        room = below if downward else above

        list_height = max(
            self.LIST_MIN,
            min(
                wanted,
                self.LIST_MAX,
                room - chrome
            )
        )

        height = list_height + chrome
        width = max(self._box.winfo_width(), 200)

        x = max(
            4,
            min(
                box_x,
                top.winfo_width() - width - 4
            )
        )

        if downward:
            y = (
                box_y
                + self._box.winfo_height()
                + 2
            )
        else:
            y = box_y - height - 2

        y = max(
            4,
            min(
                y,
                top.winfo_height() - height - 4
            )
        )

        # ---------- Show popup ----------

        self._popup.configure(
            width=width,
            height=height
        )

        self._popup.place(x=x, y=y)
        self._popup.lift()

        self._is_open = True
        self._arrow.configure(text="▴")

        # Close the dropdown when the user clicks somewhere else.
        self.after_idle(self._install_close)

    def _link_button(self, master, text, command, color):
        """Creates a small text-style button inside the dropdown."""

        return ctk.CTkButton(
            master,
            text=text,
            command=command,
            height=24,
            corner_radius=RADIUS_CONTROL,
            font=font(10),
            fg_color="transparent",
            hover_color=COLORS["accent_weak"],
            text_color=color,
            border_width=0,
            width=1
        )

    def _install_close(self):
        """Adds the event that closes the dropdown on an outside click."""

        if self._is_open:
            self._close_id = self.winfo_toplevel().bind(
                "<Button-1>",
                self._maybe_close,
                add="+"
            )

    def _maybe_close(self, event):
        """Closes the dropdown when the click is outside it."""

        if not self._is_open:
            return

        name = str(event.widget)
        popup_name = str(self._popup)

        # Keep the list open when the click is inside it.
        if (
            name == popup_name
            or name.startswith(popup_name + ".")
        ):
            return

        self._close()

    def _build_option_row(self, value):
        """Creates one selectable row in the dropdown."""

        row = frame(self._rows_host)
        row.pack(fill="x")

        selected = value in self._selected

        # Checkbox symbol.
        glyph = label(
            row,
            Table._BOX_ON if selected else Table._BOX_OFF,
            color="accent" if selected else "muted"
        )

        glyph.pack(
            side="left",
            padx=(8, 7),
            pady=4
        )

        # Option text.
        text = label(
            row,
            value,
            anchor="w"
        )

        text.pack(
            side="left",
            padx=(0, 12),
            pady=4
        )

        self._option_rows[value] = (
            glyph,
            text
        )

        # Change background while the mouse is over the row.
        def enter(_event):
            for widget in (
                row,
                glyph,
                text
            ):
                widget.configure(
                    fg_color=COLORS["accent_weak"]
                )

        def leave(_event):
            for widget in (
                row,
                glyph,
                text
            ):
                widget.configure(
                    fg_color="transparent"
                )

        # Clicking any part of the row changes the selection.
        for widget in (
            row,
            glyph,
            text
        ):
            widget.bind(
                "<Button-1>",
                lambda event, option=value:
                self._toggle_value(option)
            )

            widget.bind(
                "<Enter>",
                enter
            )

            widget.bind(
                "<Leave>",
                leave
            )

    def _toggle_value(self, value):
        """Adds or removes one value from the selection."""

        if value in self._selected:
            self._selected.discard(value)
        else:
            self._selected.add(value)

        self._refresh_glyph(value)
        self._render_summary()

        if self._on_change:
            self._on_change()

    def _refresh_glyph(self, value):
        """Updates the checkbox symbol of one option."""

        glyph, _text = self._option_rows[value]
        selected = value in self._selected

        glyph.configure(
            text=(
                Table._BOX_ON
                if selected
                else Table._BOX_OFF
            ),
            text_color=(
                COLORS["accent"]
                if selected
                else COLORS["muted"]
            )
        )

    def _select_all(self):
        """Selects every available value."""

        self._selected = set(self._values)
        self._refresh_rows()

    def _clear_all(self):
        """Clears all selected values."""

        self._selected.clear()
        self._refresh_rows()

    def _refresh_rows(self):
        """Updates all option rows after the selection changes."""

        for value in self._option_rows:
            self._refresh_glyph(value)

        self._render_summary()

        if self._on_change:
            self._on_change()

    def _close(self):
        """Closes the dropdown."""

        global _open_multi

        # Remove the outside-click event.
        if self._close_id is not None:
            try:
                self.winfo_toplevel().unbind(
                    "<Button-1>",
                    self._close_id
                )
            except tk.TclError:
                pass

            self._close_id = None

        if self._popup is not None:
            self._popup.place_forget()

        self._is_open = False
        self._arrow.configure(text="▾")

        if _open_multi is self:
            _open_multi = None


# ---------- Cross-screen banner ----------

class Banner(ctk.CTkFrame):
    """Shows an active filter that came from another screen."""

    def __init__(self, master):
        super().__init__(
            master,
            fg_color=COLORS["accent_weak"],
            border_width=1,
            border_color=COLORS["accent"],
            corner_radius=RADIUS_CONTROL,
            width=0,
            height=0
        )

        self._slot = {}
        self._on_clear = None

        # Button that removes the current cross-screen filter.
        self._clear_btn = ctk.CTkButton(
            self,
            text="✕ clear filter",
            command=self._clear,
            height=26,
            width=110,
            corner_radius=RADIUS_CONTROL,
            font=font(10, "bold"),
            fg_color="transparent",
            hover_color=COLORS["accent"],
            text_color=COLORS["accent_ink"],
            border_width=0
        )

        self._clear_btn.pack(
            side="right",
            padx=(6, 8),
            pady=6
        )

        # Text explaining which filter is active.
        self._label = label(
            self,
            "",
            color="accent_ink",
            anchor="w"
        )

        self._label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(12, 0),
            pady=6
        )

    def set_slot(self, **grid_options):
        """Stores the grid position used when the banner is shown."""

        self._slot = grid_options

    def show(self, text, on_clear):
        """Shows the banner with an active filter."""

        self._label.configure(text=text)
        self._on_clear = on_clear

        self.grid(**self._slot)
        _reflow_host(self)

    def hide(self):
        """Hides the banner."""

        self._on_clear = None

        if self.winfo_manager() == "grid":
            self.grid_remove()

        _reflow_host(self)

    def _clear(self):
        """Removes the active filter and hides the banner."""

        callback = self._on_clear
        self.hide()

        if callback:
            callback()


# ---------- Bottom action bar ----------

class ActionBar(ctk.CTkFrame):
    """Shows actions for rows selected with checkboxes."""

    def __init__(self, master):
        super().__init__(
            master,
            fg_color=COLORS["slate"],
            corner_radius=RADIUS_CARD,
            width=0,
            height=0
        )

        self._slot = {}

        # Number of selected rows.
        self._count = label(
            self,
            "",
            weight="bold"
        )

        self._count.configure(
            text_color="#ffffff"
        )

        self._count.pack(
            side="left",
            padx=(16, 10),
            pady=11
        )

        # Area containing the action buttons.
        self._actions = frame(self)
        self._actions.pack(
            side="right",
            padx=10
        )

        self._noun = "selected"

    def add_button(self, text, command):
        """Adds one button to the action bar."""

        action_button = ctk.CTkButton(
            self._actions,
            text=text,
            command=command,
            height=30,
            corner_radius=RADIUS_CONTROL,
            font=font(11),
            fg_color=COLORS["slate_hi"],
            hover_color=COLORS["accent"],
            text_color="#ffffff",
            border_width=0
        )

        action_button.pack(
            side="left",
            padx=4,
            pady=8
        )

        return action_button

    def set_noun(self, noun):
        """Sets the word used after the selected-row count."""

        self._noun = noun

    def set_slot(self, **grid_options):
        """Stores the grid position used when the bar is shown."""

        self._slot = grid_options

    def update_count(self, count):
        """Shows or hides the bar according to the selection count."""

        if count > 0:
            self._count.configure(
                text=f"{count} {self._noun}"
            )

            self.grid(**self._slot)

        elif self.winfo_manager() == "grid":
            self.grid_remove()

        _reflow_host(self)