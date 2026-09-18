#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <stdbool.h>

bool FileExistsW(const wchar_t *path) {
    DWORD dwAttrib = GetFileAttributesW(path);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

int wmain(int argc, wchar_t *argv[]) {
    // 1. Get directory of current executable
    wchar_t exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    wchar_t *lastSlash = wcsrchr(exePath, L'\\');
    if (lastSlash) {
        *lastSlash = L'\0';
    }
    SetCurrentDirectoryW(exePath);

    // 2. Locate Python executable
    wchar_t pythonCmd[MAX_PATH] = L"python";
    wchar_t venvPython[MAX_PATH];
    swprintf(venvPython, MAX_PATH, L"%ls\\backend\\.venv\\Scripts\\python.exe", exePath);
    if (FileExistsW(venvPython)) {
        swprintf(pythonCmd, MAX_PATH, L"\"%ls\"", venvPython);
    } else {
        wcscpy(pythonCmd, L"python");
    }

    // 3. Locate configure.py
    wchar_t scriptPath[MAX_PATH];
    swprintf(scriptPath, MAX_PATH, L"%ls\\backend\\configure.py", exePath);
    if (!FileExistsW(scriptPath)) {
        wprintf(L"[!] Error: Configuration script not found at '%ls'\n", scriptPath);
        wprintf(L"Press any key to exit...");
        getchar();
        return 1;
    }

    // 4. Run configure.py synchronously
    wchar_t cmd[MAX_PATH * 2];
    swprintf(cmd, MAX_PATH * 2, L"%ls \"%ls\"", pythonCmd, scriptPath);

    _wsystem(cmd);

    wprintf(L"\nPress any key to close...");
    getchar();
    return 0;
}
