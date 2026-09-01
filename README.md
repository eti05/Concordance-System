# Concordance System

A text corpus concordance built for the Open University Database Workshop (20563).

The system loads plain text files, splits them into words, and stores the exact position of every word. It allows the user to search words, view them in context (KWIC), browse the word index, search by position, create word groups and phrases, view statistics, and import or export data as XML.

The corpus contains six children's classics from Project Gutenberg.

## Downloading the project

Either way gives the same files:

- Press the green **Code** button above and choose **Download ZIP**.
- Or download `Concordance.zip` from the file list, which is the same project
  packaged as a single folder.

Then open the unpacked folder and follow the Quick Start below. On macOS and
Linux, if the launcher will not run, restore its executable bit first with
`chmod +x run.sh run.command`.

The project uses:

- Oracle Database
- Python
- CustomTkinter

## Architecture

The project is divided into four main layers:

```text
ui (CustomTkinter) -> loader / engine / xml_io -> db -> Oracle
```

- `db.py` manages the Oracle connection and runs SQL queries and commands.
- `loader.py` reads text files, tokenizes them, and loads them into the database.
- `engine.py` handles searches, KWIC, groups, phrases, documents and statistics.
- `xml_io.py` handles XML import and export.
- `ui/` contains the CustomTkinter user interface.

Only `db.py` communicates directly with Oracle.

The results tables use `ttk.Treeview`, because CustomTkinter does not include a table widget. The Treeview style is configured in `ui/widgets.py` so it matches the rest of the application.

## Requirements

Two things have to be installed before the project runs. Everything else is
handled by the launcher.

| Requirement | Why | How to check |
|---|---|---|
| **Docker** | Runs the Oracle database. Docker Desktop, Colima or Docker Engine all work. | `docker info` |
| **Python 3.9+ with Tk 8.6+** | Runs the application and its interface. | `python3 -c "import tkinter; print(tkinter.TkVersion)"` |

Docker has to be **running**, not only installed, before the launcher is
started. The Python packages (`oracledb` and `customtkinter`, listed in
`requirements.txt`) are installed automatically into a local virtual
environment on the first run, so they do not have to be installed by hand.

No Oracle client and no Oracle installation are needed: the driver works in
thin mode, and the database itself lives in the container.

### A note on Tk

Tk is the graphics library the interface is drawn with, and it ships with
Python rather than being installed separately.

The Python that comes with macOS bundles Tk 8.5, which draws the window
incorrectly, so a newer build is needed. The simplest one to install:

```bash
brew install python-tk
```

`run.sh` looks at the interpreters present on the machine and picks the first
one whose Tk is 8.6 or newer, so once a suitable Python exists nothing else has
to be configured. On Windows the installer from python.org already includes a
current Tk, and on Debian or Ubuntu it comes from `sudo apt install python3-tk`.

## Quick Start

### The short way: one launcher

Start Docker, then start the project with the launcher for your system. There
is one for each, and they do exactly the same work:

| System | File | How to start it |
|---|---|---|
| macOS | `run.command` | Double click it |
| Windows | `run.bat` | Double click it |
| Linux, or any terminal | `run.sh` | `./run.sh` |

The launcher does every manual step described further down: it creates the
virtual environment and installs the packages, starts the Oracle container,
waits until the database is ready, builds the schema and loads the corpus on
the first run, and finally opens the application.

Both launchers accept the same two arguments:

| Argument | What it does |
|---|---|
| `--reset` | Rebuilds the schema and reloads the corpus from scratch |
| `--stop` | Stops the database container; the loaded data is kept |

The first run takes a few minutes, because Oracle has to initialise itself and
the corpus has to be tokenized and inserted. Later runs start in seconds, since
the launcher notices that the database is already prepared and skips straight
to opening the application.

Two things that are specific to macOS. The first time `run.command` is opened,
macOS may refuse to run it because it was downloaded from the internet; right
click the file, choose **Open**, and confirm once. And if the file was unpacked
by a tool that dropped its executable bit, make it runnable again with:

```bash
chmod +x run.sh run.command
```

### The manual way, step by step

Use this if you prefer to run each stage yourself, or to see where a problem is.

### 1. Start Oracle

Docker Desktop or Colima must be running.

Start the Oracle container:

```bash
docker compose up -d
```

Check its status:

```bash
docker compose ps
```

Wait until the Oracle container is healthy before continuing.

### 2. Create the Python environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```text
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Create the database and load the corpus

Create the database schema:

```bash
python scripts/init_db.py
```

Load the corpus:

```bash
python scripts/load_corpus.py
```

After loading the documents, the script refreshes the Oracle optimizer statistics.

### 4. Start the application

`config.py` requires the database password to be supplied through the
environment, so set it before starting the application. The launcher scripts do
this for you; running by hand, it has to be set once per terminal session.

On macOS or Linux:

```bash
export ORACLE_PASSWORD=concordance
python main.py
```

On Windows:

```text
set ORACLE_PASSWORD=concordance
python main.py
```

## Configuration

Database connection settings are stored in `config.py`.

The default settings work with the local Oracle container, but they can be changed using environment variables.

| Variable | Default |
|---|---|
| `ORACLE_USER` | `concordance` |
| `ORACLE_PASSWORD` | none - it must be set, or the application stops with a clear error |
| `ORACLE_DSN` | `localhost:1521/FREEPDB1` |

The password deliberately has no default, so that no password is ever written
in the source. For the bundled container the value is `concordance`, and the
launcher scripts set it.

Optional Oracle Cloud settings are also supported:

- `ORACLE_CONFIG_DIR`
- `ORACLE_WALLET_DIR`
- `ORACLE_WALLET_PASSWORD`

When using Oracle Cloud, `ORACLE_DSN` should contain the required TNS alias.

## Project Layout

```text
concordance/
    run.command         Launcher for macOS (double click)
    run.bat             Launcher for Windows (double click)
    run.sh              Launcher for Linux and for any terminal
    docker-compose.yml  The Oracle container the project runs against
    main.py             Starts the application
    config.py           Oracle connection settings
    db.py               Database access layer
    loader.py           Text tokenization and loading
    engine.py           Searches and statistics
    xml_io.py           XML import and export
    sqlscript.py        Splits SQL files into statements

    ui/                  User interface
    sql/                 Schema, indexes, trigger and views
    data/                Corpus files and corpus.csv
    scripts/             Database setup and corpus loading scripts
    tests/               Python tests
```

## User Interface

The application contains four main screens:

- **Home** - displays general database statistics and document import/export actions.
- **Words** - searches the word index and displays word occurrences.
- **Documents** - searches documents by metadata and displays document statistics.
- **Groups** - creates and manages word groups and phrases.

## XML

XML import and export are the additional topic of the project.

The application supports:

- exporting one document to XML,
- exporting the complete database to XML,
- importing documents, groups and phrases from XML.

Exporting the complete database and importing it into a new schema can rebuild the stored corpus data.

## Tests

Install the project requirements first:

```bash
pip install -r requirements.txt
```

Run the tests with:

```bash
python -m pytest tests
```

The tests cover Python logic such as:

- text tokenization,
- SQL file splitting,
- SQL query building.

These tests do not require an Oracle database.

## Tokenization

The loader converts each text document into normalized words and stores the position of every occurrence.

### Paragraphs and lines

A blank line separates paragraphs.

Paragraph and line numbers are counted from the beginning of the document. Word positions restart from `1` on every line.

For example:

```text
Paragraph 1
Line 1
Word 1

Paragraph 1
Line 1
Word 2
```

Only lines that contain at least one word receive a stored line number.

Lines that contain only numbers, symbols or punctuation do not create word occurrences.

### Words

A word is a sequence of letters.

Punctuation, digits and underscores are treated as separators.

Apostrophes between letters are kept.

For example:

```text
don't
sister's
```

Curved apostrophes are converted to regular apostrophes.

All words are stored in lower case.

For example:

```text
Love
LOVE
love
```

are all stored as:

```text
love
```

The database trigger also normalizes words before they are inserted or updated.

Because the original text is not stored, text reconstructed by the system contains normalized words without the original punctuation or capitalization.

## KWIC

KWIC stands for **Key Word In Context**.

When the user selects a word occurrence, the system shows:

- the line before the occurrence,
- the line containing the word,
- the line after the occurrence.

The matching word is highlighted.

The context is reconstructed from the word occurrences stored in Oracle.

## Database

The main database tables are:

- `Authors`
- `Documents`
- `Words`
- `Occurrences`
- `Groups`
- `GroupMembers`
- `Phrases`
- `PhraseWords`

The database also contains views used for statistics and indexes used to speed up common searches.