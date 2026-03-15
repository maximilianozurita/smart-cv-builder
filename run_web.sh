#!/usr/bin/env bash
# Run the smart-cv-builder web UI from the project root.
# WeasyPrint on macOS (Homebrew) needs pango/gobject libs visible.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Make Homebrew libs visible to WeasyPrint (macOS only)
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"

echo "Starting smart-cv-builder at http://localhost:8000"
uvicorn web.main:app --reload --port 8000
