#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check Python 3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 is required but not found in PATH." >&2
    exit 1
fi

echo "[i] Launching BenchQC Stress & Battery Sustenance Suite on macOS..."
"$PY_CMD" -m benchqc "$@"
