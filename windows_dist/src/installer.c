#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <stdio.h>
#include <stdbool.h>

void PrintBanner() {
    wprintf(L"\n");
    wprintf(L"  ===============================================================\n");
    wprintf(L"      J.A.R.V.I.S. - Automated Windows Installer (x64)           \n");
    wprintf(L"  ===============================================================\n\n");
}

bool FileExistsW(const wchar_t *path) {
    DWORD dwAttrib = GetFileAttributesW(path);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

bool DirExistsW(const wchar_t *path) {
    DWORD dwAttrib = GetFileAttributesW(path);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

int wmain(int argc, wchar_t *argv[]) {
    SetConsoleTitleW(L"J.A.R.V.I.S. Windows Installer");
    PrintBanner();

    // 1. Get directory of current installer executable
    wchar_t exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    wchar_t *lastSlash = wcsrchr(exePath, L'\\');
    if (lastSlash) {
        *lastSlash = L'\0';
    }
    SetCurrentDirectoryW(exePath);
    wprintf(L"[*] Installation Directory: %ls\n\n", exePath);

    // 2. Check Python in PATH
    wprintf(L"[*] Checking Python environment...\n");
    if (_wsystem(L"where python >nul 2>&1") != 0) {
        wprintf(L"\n[!] ERROR: Python 3.10+ was not found in your PATH.\n");
        wprintf(L"    Please install Python from https://www.python.org/downloads/\n");
        wprintf(L"    Ensure 'Add Python to PATH' is checked during installation.\n\n");
        wprintf(L"Press any key to exit...");
        getchar();
        return 1;
    }
    _wsystem(L"python --version");
    wprintf(L"\n");

    // 3. Check Java in PATH
    wprintf(L"[*] Checking Java environment...\n");
    if (_wsystem(L"where java >nul 2>&1") != 0 && _wsystem(L"where javaw >nul 2>&1") != 0) {
        wprintf(L"[!] WARNING: Java 21+ was not found in your PATH.\n");
        wprintf(L"    The Iron Man HUD interface requires OpenJDK 21 LTS.\n");
        wprintf(L"    Download link: https://adoptium.net/ (Eclipse Temurin 21)\n\n");
    } else {
        _wsystem(L"java --version");
        wprintf(L"\n");
    }

    // 4. Setup Python Virtual Environment
    wchar_t venvDir[MAX_PATH];
    swprintf(venvDir, MAX_PATH, L"%ls\\backend\\.venv", exePath);

    wchar_t reqFile[MAX_PATH];
    swprintf(reqFile, MAX_PATH, L"%ls\\backend\\requirements.txt", exePath);

    wchar_t venvPython[MAX_PATH];
    swprintf(venvPython, MAX_PATH, L"%ls\\backend\\.venv\\Scripts\\python.exe", exePath);

    wchar_t venvPip[MAX_PATH];
    swprintf(venvPip, MAX_PATH, L"%ls\\backend\\.venv\\Scripts\\pip.exe", exePath);

    wprintf(L"[*] Creating Python virtual environment in backend\\.venv ...\n");
    wchar_t createVenvCmd[MAX_PATH * 2];
    swprintf(createVenvCmd, MAX_PATH * 2, L"python -m venv \"%ls\"", venvDir);
    int venvRet = _wsystem(createVenvCmd);

    if (venvRet != 0 || !FileExistsW(venvPython)) {
        wprintf(L"[!] Virtual environment creation failed. Falling back to global pip...\n");
        wchar_t pipGlobalCmd[MAX_PATH * 2];
        swprintf(pipGlobalCmd, MAX_PATH * 2, L"pip install -r \"%ls\"", reqFile);
        _wsystem(pipGlobalCmd);
    } else {
        wprintf(L"[+] Virtual environment created successfully.\n");
        wprintf(L"[*] Upgrading pip...\n");
        wchar_t upgradePipCmd[MAX_PATH * 2];
        swprintf(upgradePipCmd, MAX_PATH * 2, L"\"%ls\" -m pip install --upgrade pip --quiet", venvPython);
        _wsystem(upgradePipCmd);

        wprintf(L"[*] Installing dependencies from requirements.txt...\n");
        wchar_t installReqCmd[MAX_PATH * 2];
        swprintf(installReqCmd, MAX_PATH * 2, L"\"%ls\" install -r \"%ls\"", venvPip, reqFile);
        _wsystem(installReqCmd);
    }

    wprintf(L"\n");
    wprintf(L"  ===============================================================\n");
    wprintf(L"      INSTALLATION COMPLETED SUCCESSFULLY!                      \n");
    wprintf(L"  ===============================================================\n\n");
    wprintf(L"  [+] Double-click 'jarvis.exe' to launch J.A.R.V.I.S.\n");
    wprintf(L"  [+] Double-click 'jarvis-config.exe' to configure AI models.\n\n");

    // Don't pause if --silent or --no-pause is passed
    if (argc > 1 && (wcscmp(argv[1], L"--silent") == 0 || wcscmp(argv[1], L"--no-pause") == 0)) {
        return 0;
    }

    wprintf(L"Press any key to close this installer...");
    getchar();
    return 0;
}
