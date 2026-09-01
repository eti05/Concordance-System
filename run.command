#!/usr/bin/env bash
# Double click this file on macOS to start the Concordance System.
#
# macOS only opens a Terminal for files ending in .command, which is why this
# wrapper exists. It does nothing except hand over to run.sh, so both entry
# points behave identically.
#
# If macOS refuses to open it ("unidentified developer"), right click the file
# and choose Open once; macOS then remembers the choice.

cd "$(dirname "$0")"

# The executable bit is lost when a zip is unpacked by some tools, so restore it.
chmod +x run.sh 2>/dev/null

./run.sh "$@"
status=$?

# Terminal closes the window the moment the script ends, taking the last message
# with it, so always wait for a keypress rather than only after a failure.
echo
if [ "$status" -ne 0 ]; then
    echo "The launcher stopped with an error. The message above explains why."
fi
read -r -p "Press Return to close this window. "
exit $status
