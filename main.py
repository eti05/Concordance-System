"""Starts the Concordance System user interface."""

import customtkinter as ctk

from ui.app import ConcordanceApp


def main():
    """Creates and starts the main application window."""

    # Create the main window and application.
    root = ctk.CTk()
    ConcordanceApp(root)

    # Bring the window to the front when the application starts.
    root.lift()
    root.attributes("-topmost", True)
    root.after(600, lambda: root.attributes("-topmost", False))
    root.focus_force()

    # Start the user interface.
    root.mainloop()


if __name__ == "__main__":
    main()