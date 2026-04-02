#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="8000"
HOST_ARG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --host)
      HOST_ARG="--host $2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Activate virtual environment
source .venv/bin/activate

# macOS libs
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"

echo "Starting smart-cv-builder at http://${HOST_ARG:+$HOST_ARG }$PORT"

# Run uvicorn
uvicorn web.main:app --reload $HOST_ARG --port "$PORT"