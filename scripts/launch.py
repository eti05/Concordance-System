"""Starts the application, after making sure Tk can find its own library.

Why this file exists
--------------------
On Windows the Tcl and Tk libraries live inside the base Python installation,
in a folder called ``tcl`` next to ``python.exe``. A virtual environment does
not carry them along, so ``tkinter`` looks in the wrong place and Tcl reports
``Can't find a usable init.tcl``. The database starts normally and only the
window fails to open, which makes the cause hard to guess.

The fix is to point ``TCL_LIBRARY`` and ``TK_LIBRARY`` at the real folders
before Tk starts. That is done here, in Python, rather than in ``run.bat``,
for one specific reason: the path can contain characters outside ASCII, such as
a user name written in Hebrew, and such a path cannot survive being captured
through a cmd pipe. Python handles it natively.

Running ``main.py`` directly still works. This wrapper only adds the Tk fix and
a clear message when Tk cannot start at all.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Folder names such as tcl8.6, tk8.6, tcl9.0. Anything else in the tcl folder
# (tcllib, tzdata and friends) is not a library root and is ignored.
_VERSIONED_DIR = re.compile(r"^(tcl|tk)(\d+)\.(\d+)$")


def _library_roots():
    """Return the folders that may hold the Tcl and Tk libraries."""

    # The base installation first, since that is where they really live, then
    # the environment itself for the unusual case of a full copy.
    seen = []
    for prefix in (sys.base_prefix, sys.prefix):
        candidate = Path(prefix) / "tcl"
        if candidate.is_dir() and candidate not in seen:
            seen.append(candidate)
    return seen


def _newest(root, kind):
    """Return the highest versioned <kind> folder inside root, or None."""

    found = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        match = _VERSIONED_DIR.match(entry.name)
        if match and match.group(1) == kind:
            found.append(((int(match.group(2)), int(match.group(3))), entry))
    if not found:
        return None
    found.sort()
    return found[-1][1]


def configure_tk():
    """Point TCL_LIBRARY and TK_LIBRARY at the installed libraries.

    Returns the list of folders that were searched, so a failure can say where
    it looked. An existing setting is never overwritten.
    """

    roots = _library_roots()
    for root in roots:
        for variable, kind in (("TCL_LIBRARY", "tcl"), ("TK_LIBRARY", "tk")):
            if os.environ.get(variable):
                continue
            directory = _newest(root, kind)
            if directory is not None:
                # Tcl reads this with getenv() when it initialises, and
                # assigning to os.environ updates the C environment too.
                os.environ[variable] = str(directory)
    return roots


def check_tk(roots):
    """Start Tcl without opening a window, to fail early and clearly."""

    import tkinter

    try:
        tkinter.Tcl()
        return True
    except tkinter.TclError as error:
        print()
        print("ERROR: Python was found, but its graphics library (Tk) cannot start.")
        print()
        print("This is a problem with the Python installation, not with the project.")
        print("Tcl reported:")
        print("   %s" % str(error).strip().splitlines()[0])
        print()
        print("Python installation : %s" % sys.base_prefix)
        if roots:
            print("Tcl folders searched:")
            for root in roots:
                print("   %s" % root)
        else:
            print("No 'tcl' folder was found next to the Python installation,")
            print("which means Python was installed without its graphics files.")
        for variable in ("TCL_LIBRARY", "TK_LIBRARY"):
            print("%-20s: %s" % (variable, os.environ.get(variable, "not set")))
        print()
        print("On Windows, repair the installation: open Settings, then Apps,")
        print("find Python, choose Modify, and tick 'tcl/tk and IDLE'. Then")
        print("delete the .venv folder in this project and start again.")
        print()
        return False


def main():
    roots = configure_tk()
    if not check_tk(roots):
        return 1

    # Import the application only once Tk is known to work, so a Tk problem
    # cannot be reported as an import error.
    sys.path.insert(0, str(PROJECT_DIR))
    import main as application

    application.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
