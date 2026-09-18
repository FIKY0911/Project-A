#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
WIN_DIR="$DIST_DIR/jarvis-windows-x64"
ZIP_OUTPUT="$PROJECT_ROOT/jarvis-windows-x64.zip"

echo "==============================================================="
echo "       BUILDING & PACKAGING J.A.R.V.I.S. FOR WINDOWS (x64)      "
echo "==============================================================="

# 1. Compile JavaFX multi-OS fat JAR if needed
echo "[*] Building JavaFX multi-OS fat jar..."
/home/fiky/.local/opt/apache-maven-3.9.6/bin/mvn package -f "$PROJECT_ROOT/frontend-javafx/pom.xml" -DskipTests -q

# 2. Compile Windows Native Executables
echo "[*] Compiling native Windows PE executables (x86_64)..."
mkdir -p "$PROJECT_ROOT/windows_dist"
x86_64-w64-mingw32-gcc -O2 -municode "$PROJECT_ROOT/windows_dist/src/launcher.c" -o "$PROJECT_ROOT/windows_dist/jarvis.exe"
x86_64-w64-mingw32-gcc -O2 -municode "$PROJECT_ROOT/windows_dist/src/config_tool.c" -o "$PROJECT_ROOT/windows_dist/jarvis-config.exe"

# 3. Prepare Staging Directory
echo "[*] Staging Windows distribution files..."
rm -rf "$WIN_DIR"
mkdir -p "$WIN_DIR/frontend"
mkdir -p "$WIN_DIR/backend/data"
mkdir -p "$WIN_DIR/backend/audio_cache"

# Copy Executables and batch files
cp "$PROJECT_ROOT/windows_dist/jarvis.exe" "$WIN_DIR/"
cp "$PROJECT_ROOT/windows_dist/jarvis-config.exe" "$WIN_DIR/"
cp "$PROJECT_ROOT/windows_dist/install_windows.bat" "$WIN_DIR/"
cp "$PROJECT_ROOT/windows_dist/start_jarvis.bat" "$WIN_DIR/"
cp "$PROJECT_ROOT/windows_dist/README_WINDOWS.txt" "$WIN_DIR/"

# Copy Frontend JAR
cp "$PROJECT_ROOT/frontend-javafx/target/jarvis-hud.jar" "$WIN_DIR/frontend/"

# Copy Backend files (excluding venv, pycache, and cached mp3s)
rsync -av --exclude='__pycache__' --exclude='.venv' --exclude='.pytest_cache' --exclude='tests' \
    --exclude='audio_cache/*.mp3' \
    "$PROJECT_ROOT/backend-python/" "$WIN_DIR/backend/"


# Copy initialized database with current settings
if [ -f "$PROJECT_ROOT/backend-python/data/jarvis_memory.db" ]; then
    cp "$PROJECT_ROOT/backend-python/data/jarvis_memory.db" "$WIN_DIR/backend/data/"
fi

# 4. Create ZIP Archive
echo "[*] Compiling ZIP archive: $ZIP_OUTPUT ..."
rm -f "$ZIP_OUTPUT"
cd "$DIST_DIR"
zip -r -q "$ZIP_OUTPUT" "jarvis-windows-x64"

echo "==============================================================="
echo "[+] SUCCESS: Windows package created successfully!"
echo "[+] Location: $ZIP_OUTPUT"
ls -lh "$ZIP_OUTPUT"
echo "==============================================================="
