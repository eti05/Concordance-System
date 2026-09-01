#!/usr/bin/env bash
# Concordance System - launcher for macOS and Linux.
#
#   ./run.sh            start the database, prepare it if needed, open the app
#   ./run.sh --reset    rebuild the schema and reload the corpus from scratch
#   ./run.sh --stop     stop the database container
#
# Requirements: Docker (Desktop, Colima or Engine) and Python 3.9+ with Tk 8.6+.
# Nothing here is specific to any one machine: every path is resolved relative
# to this file, and the Python interpreter is auto-detected.

set -euo pipefail
cd "$(dirname "$0")"

# The application user created by docker-compose.yml.
export ORACLE_USER="${ORACLE_USER:-concordance}"
export ORACLE_PASSWORD="${ORACLE_PASSWORD:-concordance}"
export ORACLE_DSN="${ORACLE_DSN:-localhost:1521/FREEPDB1}"

CONTAINER="concordance-oracle"
VENV=".venv"

die() { echo "ERROR: $*" >&2; exit 1; }

if [ "${1:-}" = "--stop" ]; then
    if ! docker info >/dev/null 2>&1; then
        echo "Docker is not running, so there is nothing to stop."
        exit 0
    fi
    echo "Stopping the database container ..."
    docker compose down >/dev/null 2>&1 || true
    echo "Done. The loaded data is kept for next time."
    exit 0
fi

if [ "${1:-}" = "--clean" ]; then
    echo "This removes the database container, the loaded corpus and the local"
    echo "virtual environment. The project files themselves are not touched."
    printf "Type 'yes' to continue: "
    read -r answer
    [ "$answer" = "yes" ] || { echo "Cancelled."; exit 0; }
    if docker info >/dev/null 2>&1; then
        echo "Removing the container and its data volume ..."
        docker compose down --volumes >/dev/null 2>&1 || true
    else
        echo "Docker is not running, so the container could not be removed."
        echo "Start Docker and run this again to remove the data volume."
    fi
    echo "Removing the virtual environment ..."
    rm -rf "$VENV"
    find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache
    echo "Done. Nothing of this project is left running or stored."
    exit 0
fi

command -v docker >/dev/null 2>&1 || die "Docker is not installed or not on PATH."
docker info >/dev/null 2>&1 || die "Docker is installed but not running. Start it and try again."

# ---------------------------------------------------------------- python ---
# Prefer a Python that ships a modern Tk. The macOS system Tk is 8.5 and
# renders a blank window, so a build with Tk 8.6+ is required.
find_python() {
    for candidate in python3 python3.13 python3.12 python3.11 python; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        if "$candidate" - <<'PY' >/dev/null 2>&1
import sys, tkinter
sys.exit(0 if tkinter.TkVersion >= 8.6 else 1)
PY
        then echo "$candidate"; return 0; fi
    done
    return 1
}

if [ ! -x "$VENV/bin/python" ]; then
    PY=$(find_python) || die "No Python with Tk 8.6+ was found.
On macOS install one with:  brew install python-tk
On Debian/Ubuntu:           sudo apt install python3-tk"
    echo "Creating the virtual environment with $PY ..."
    "$PY" -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r requirements.txt
fi
PYTHON="$VENV/bin/python"

# -------------------------------------------------------------- database ---
echo "1/3  Starting the Oracle database ..."
docker compose up -d >/dev/null

printf "     Waiting for it to become ready "
for _ in $(seq 1 90); do
    status=$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo starting)
    [ "$status" = "healthy" ] && break
    printf "."
    sleep 5
done
echo
[ "${status:-}" = "healthy" ] || die "The database did not become ready in time. Run 'docker compose logs oracle' to see why."

# ---------------------------------------------------------------- schema ---
needs_setup=0
if [ "${1:-}" = "--reset" ]; then
    needs_setup=1
else
    # Fresh volume? Then the schema is not there yet.
    "$PYTHON" - <<'PY' >/dev/null 2>&1 || needs_setup=1
import db
db.run_query("SELECT 1 FROM Documents WHERE ROWNUM = 1")
PY
fi

if [ "$needs_setup" = "1" ]; then
    echo "2/3  Preparing the database (this runs once and takes a minute) ..."
    "$PYTHON" scripts/init_db.py
    "$PYTHON" scripts/load_corpus.py
else
    echo "2/3  The database is already prepared."
fi

# ------------------------------------------------------------------- app ---
echo "3/3  Opening the Concordance System. Look for a new window."
"$PYTHON" scripts/launch.py
echo "Closed. Run './run.sh --stop' when you want to shut the database down."
