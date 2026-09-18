#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
MVN="/home/fiky/.local/bin/mvn"

echo "[J.A.R.V.I.S.] Launching JavaFX Iron Man HUD..."
$MVN javafx:run -f "$DIR/pom.xml"
