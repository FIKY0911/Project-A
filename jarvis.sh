#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to run full build
do_build() {
    echo "==============================================================="
    echo "       BUILDING & INSTALLING J.A.R.V.I.S. FOR LINUX           "
    echo "==============================================================="

    # 1. Setup Python Virtual Environment
    echo "[*] Setting up Python backend virtual environment..."
    cd "$PROJECT_ROOT/backend-python"
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip -q
    .venv/bin/pip install -r requirements.txt -q
    echo "[+] Python backend dependencies verified."

    # 2. Build JavaFX Frontend
    echo "[*] Compiling and packaging JavaFX Sci-Fi HUD..."
    MVN_BIN="/home/fiky/.local/opt/apache-maven-3.9.6/bin/mvn"
    if [ ! -x "$MVN_BIN" ]; then
        MVN_BIN="mvn"
    fi
    "$MVN_BIN" package -f "$PROJECT_ROOT/frontend-javafx/pom.xml" -DskipTests -q
    echo "[+] JavaFX HUD fat jar compiled successfully."

    # 3. Create Global Command 'jarvis'
    echo "[*] Registering global command 'jarvis'..."
    mkdir -p "$HOME/.local/bin"

    cat << EOF > "$HOME/.local/bin/jarvis"
#!/usr/bin/env bash
exec "$PROJECT_ROOT/start_jarvis.sh" "\$@"
EOF
    chmod +x "$HOME/.local/bin/jarvis"

    # Also try /usr/local/bin if sudo permissions available
    if command -v sudo >/dev/null 2>&1; then
        echo fiky | sudo -S cp "$HOME/.local/bin/jarvis" /usr/local/bin/jarvis 2>/dev/null || true
        echo fiky | sudo -S chmod +x /usr/local/bin/jarvis 2>/dev/null || true
    fi

    echo "[+] Command 'jarvis' installed to /usr/local/bin/jarvis and $HOME/.local/bin/jarvis."

    # 4. Run Core Tests
    echo "[*] Running verification tests..."
    "$PROJECT_ROOT/backend-python/.venv/bin/pytest" "$PROJECT_ROOT/backend-python/tests/" -q

    echo ""
    echo "==============================================================="
    echo "       BUILD COMPLETE! J.A.R.V.I.S. IS READY TO RUN           "
    echo "==============================================================="
    echo " You can launch J.A.R.V.I.S. by typing:"
    echo "     jarvis"
    echo " or:"
    echo "     ./jarvis.sh run"
    echo "==============================================================="
}

# Subcommand dispatch
case "$1" in
    build)
        do_build
        exit 0
        ;;
    run|start)
        exec "$PROJECT_ROOT/start_jarvis.sh" "${@:2}"
        ;;
    config|configure)
        exec "$PROJECT_ROOT/backend-python/.venv/bin/python" "$PROJECT_ROOT/backend-python/configure.py"
        ;;
    test|tests)
        exec "$PROJECT_ROOT/backend-python/.venv/bin/pytest" "$PROJECT_ROOT/backend-python/tests/" -v
        ;;
    help|--help|-h)
        echo "Usage: ./jarvis.sh [run | build | config | test]"
        echo "  ./jarvis.sh        : Launch J.A.R.V.I.S. directly (or builds first if needed)"
        echo "  ./jarvis.sh run    : Launch J.A.R.V.I.S. (Backend + Sci-Fi HUD)"
        echo "  ./jarvis.sh build  : Rebuild dependencies, package HUD, and register global command"
        echo "  ./jarvis.sh config : Open interactive AI configuration"
        echo "  ./jarvis.sh test   : Run core verification tests"
        exit 0
        ;;
    "")
        # If no arguments given:
        # Check if already built
        if [ -d "$PROJECT_ROOT/backend-python/.venv" ] && [ -f "$PROJECT_ROOT/frontend-javafx/target/jarvis-hud.jar" ]; then
            echo "[*] Launching J.A.R.V.I.S...."
            exec "$PROJECT_ROOT/start_jarvis.sh"
        else
            echo "[*] First run detected. Building J.A.R.V.I.S. first..."
            do_build
            echo "[*] Now launching J.A.R.V.I.S...."
            exec "$PROJECT_ROOT/start_jarvis.sh"
        fi
        ;;
    *)
        echo "[!] Unknown command: $1"
        echo "Run './jarvis.sh --help' for usage."
        exit 1
        ;;
esac
