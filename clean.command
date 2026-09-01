#!/usr/bin/env bash
# Double click this file on macOS to remove everything this project created.
#
# It removes the Oracle container, the Docker volume holding the loaded corpus,
# and the local virtual environment. It asks for confirmation first, and it
# never touches the project's own files.

cd "$(dirname "$0")"
chmod +x run.sh 2>/dev/null
./run.sh --clean

echo
echo "Press any key to close this window."
read -n 1 -s -r
