#!/bin/bash
# Launches the Python monitor from its own directory.
# Usage: ./run_monitor.sh [monitor.py options]   e.g. ./run_monitor.sh --loop -i 30

cd "$(dirname "$(readlink -f "$0")")" || exit 1

echo "Starting Linux system monitor..."
python3 monitor.py "$@"
status=$?

if [ "$status" -ne 0 ]; then
    echo "Monitor exited with status $status" >&2
fi
exit "$status"
