#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <stdbool.h>

void PrintBanner() {
    wprintf(L"\n");
    wprintf(L"  ===============================================================\n");
    wprintf(L"      J.A.R.V.I.S. - Autonomous Desktop Assistant (Windows x64)  \n");
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
    PrintBanner();

    // 1. Get directory of current executable
    wchar_t exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    wchar_t *lastSlash = wcsrchr(exePath, L'\\');
    if (lastSlash) {
        *lastSlash = L'\0';
    }
    SetCurrentDirectoryW(exePath);
    wprintf(L"[*] Working Directory: %ls\n", exePath);

    // Check if --config is passed
    if (argc > 1 && (wcscmp(argv[1], L"--config") == 0 || wcscmp(argv[1], L"-c") == 0)) {
        wprintf(L"[*] Launching J.A.R.V.I.S. Configuration Utility...\n");
        wchar_t configExe[MAX_PATH];
        swprintf(configExe, MAX_PATH, L"%ls\\jarvis-config.exe", exePath);
        if (FileExistsW(configExe)) {
            _wsystem(configExe);
            return 0;
        }
    }

    // 2. Locate Python executable
    wchar_t pythonCmd[MAX_PATH] = L"python";
    wchar_t venvPython[MAX_PATH];
    swprintf(venvPython, MAX_PATH, L"%ls\\backend\\.venv\\Scripts\\python.exe", exePath);
    if (FileExistsW(venvPython)) {
        swprintf(pythonCmd, MAX_PATH, L"\"%ls\"", venvPython);
    } else {
        // Fallback to system python
        wcscpy(pythonCmd, L"python");
    }

    // 3. Locate Java executable
    wchar_t javaCmd[MAX_PATH] = L"javaw";
    // Check if java exists
    if (_wsystem(L"where javaw >nul 2>&1") != 0) {
        if (_wsystem(L"where java >nul 2>&1") == 0) {
            wcscpy(javaCmd, L"java");
        } else {
            wprintf(L"[!] WARNING: 'java' or 'javaw' (Java 21+) was not found in your PATH.\n");
            wprintf(L"[!] Please install OpenJDK 21 or Java 21 to run the Sci-Fi HUD.\n\n");
            wprintf(L"Press any key to continue anyway...");
            getchar();
        }
    }

    // 4. Start Backend Server
    wprintf(L"[*] Starting J.A.R.V.I.S. Core Backend on port 8765...\n");
    wchar_t backendScript[MAX_PATH];
    swprintf(backendScript, MAX_PATH, L"%ls\\backend\\main.py", exePath);
    if (!FileExistsW(backendScript)) {
        wprintf(L"[!] Error: Backend script not found at '%ls'\n", backendScript);
        wprintf(L"Press any key to exit...");
        getchar();
        return 1;
    }

    wchar_t backendCommandLine[MAX_PATH * 2];
    swprintf(backendCommandLine, MAX_PATH * 2, L"%ls \"%ls\"", pythonCmd, backendScript);

    STARTUPINFOW siBackend;
    PROCESS_INFORMATION piBackend;
    ZeroMemory(&siBackend, sizeof(siBackend));
    siBackend.cb = sizeof(siBackend);
    ZeroMemory(&piBackend, sizeof(piBackend));

    wchar_t backendDir[MAX_PATH];
    swprintf(backendDir, MAX_PATH, L"%ls\\backend", exePath);

    BOOL bBackendSuccess = CreateProcessW(
        NULL,
        backendCommandLine,
        NULL,
        NULL,
        FALSE,
        CREATE_NEW_CONSOLE,
        NULL,
        backendDir,
        &siBackend,
        &piBackend
    );

    if (!bBackendSuccess) {
        wprintf(L"[!] Failed to launch Python backend! Error code: %lu\n", GetLastError());
        wprintf(L"[*] Try running 'install_windows.bat' first to install required dependencies.\n");
        wprintf(L"Press any key to exit...");
        getchar();
        return 1;
    }

    wprintf(L"[+] Backend process started (PID: %lu). Initializing WebSocket server...\n", piBackend.dwProcessId);
    Sleep(2500); // Allow backend to bind port 8765

    // 5. Start JavaFX Frontend HUD
    wprintf(L"[*] Starting J.A.R.V.I.S. Sci-Fi HUD...\n");
    wchar_t frontendJar[MAX_PATH];
    swprintf(frontendJar, MAX_PATH, L"%ls\\frontend\\jarvis-hud.jar", exePath);

    if (!FileExistsW(frontendJar)) {
        wprintf(L"[!] Error: Frontend JAR not found at '%ls'\n", frontendJar);
        TerminateProcess(piBackend.hProcess, 0);
        CloseHandle(piBackend.hProcess);
        CloseHandle(piBackend.hThread);
        return 1;
    }

    wchar_t guiCommandLine[MAX_PATH * 2];
    swprintf(guiCommandLine, MAX_PATH * 2, L"%ls -jar \"%ls\"", javaCmd, frontendJar);

    STARTUPINFOW siGui;
    PROCESS_INFORMATION piGui;
    ZeroMemory(&siGui, sizeof(siGui));
    siGui.cb = sizeof(siGui);
    ZeroMemory(&piGui, sizeof(piGui));

    BOOL bGuiSuccess = CreateProcessW(
        NULL,
        guiCommandLine,
        NULL,
        NULL,
        FALSE,
        0,
        NULL,
        exePath,
        &siGui,
        &piGui
    );

    if (!bGuiSuccess) {
        wprintf(L"[!] Failed to launch Java HUD! Trying fallback with java.exe...\n");
        swprintf(guiCommandLine, MAX_PATH * 2, L"java -jar \"%ls\"", frontendJar);
        bGuiSuccess = CreateProcessW(
            NULL,
            guiCommandLine,
            NULL,
            NULL,
            FALSE,
            0,
            NULL,
            exePath,
            &siGui,
            &piGui
        );
    }

    if (bGuiSuccess) {
        wprintf(L"[+] HUD Interface online (PID: %lu). J.A.R.V.I.S. is ready.\n\n", piGui.dwProcessId);
        wprintf(L"    -> Speak 'Jarvis ...' to command hands-free.\n");
        wprintf(L"    -> Close the HUD window to shutdown J.A.R.V.I.S.\n\n");

        // Wait for HUD window to be closed
        WaitForSingleObject(piGui.hProcess, INFINITE);

        wprintf(L"[*] HUD Interface closed. Shutting down Core Backend...\n");
        TerminateProcess(piBackend.hProcess, 0);

        CloseHandle(piGui.hProcess);
        CloseHandle(piGui.hThread);
    } else {
        wprintf(L"[!] Failed to launch Java HUD! Error code: %lu\n", GetLastError());
        TerminateProcess(piBackend.hProcess, 0);
    }

    CloseHandle(piBackend.hProcess);
    CloseHandle(piBackend.hThread);
    wprintf(L"[+] J.A.R.V.I.S. shutdown cleanly. Good bye, Sir.\n");
    return 0;
}
