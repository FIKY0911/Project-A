#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$DIR/.venv/bin/activate"

echo "[J.A.R.V.I.S.] Starting Python Backend Service on 127.0.0.1:8765..."
python "$DIR/main.py"
