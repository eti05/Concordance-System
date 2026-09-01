#!/usr/bin/env bash
# Double click this file on macOS to stop the Concordance System.
#
# It stops the Oracle container and frees the memory it was using. The loaded
# corpus is kept in a Docker volume, so the next start is quick and no data is
# lost. To delete the data as well, use clean.command instead.

cd "$(dirname "$0")"
chmod +x run.sh 2>/dev/null
./run.sh --stop
status=$?

echo
read -r -p "Press Return to close this window. "
exit $status
