// inject.cpp — 远程注入器：把 scum_harness.dll 载入 SCUMServer.exe
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <string>
#include <vector>

static DWORD FindPid(const wchar_t* name) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32W pe{}; pe.dwSize = sizeof(pe);
    DWORD pid = 0;
    if (Process32FirstW(snap, &pe)) {
        do {
            if (_wcsicmp(pe.szExeFile, name) == 0) { pid = pe.th32ProcessID; break; }
        } while (Process32NextW(snap, &pe));
    }
    CloseHandle(snap);
    return pid;
}

static bool EnableDebugPrivilege() {
    HANDLE tok = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &tok)) return false;
    TOKEN_PRIVILEGES tp{};
    tp.PrivilegeCount = 1;
    LookupPrivilegeValueW(nullptr, L"SeDebugPrivilege", &tp.Privileges[0].Luid);
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    bool ok = AdjustTokenPrivileges(tok, FALSE, &tp, sizeof(tp), nullptr, nullptr) != 0;
    CloseHandle(tok);
    return ok;
}

int wmain(int argc, wchar_t** argv) {
    if (argc < 3) {
        wprintf(L"usage: scum_inject.exe <pid|process.exe> <full_path_to_dll>\n");
        return 1;
    }
    DWORD pid = 0;
    std::wstring target = argv[1];
    bool numeric = !target.empty();
    for (wchar_t c : target) if (!iswdigit(c)) { numeric = false; break; }
    pid = numeric ? (DWORD)_wtoi(target.c_str()) : FindPid(target.c_str());
    if (!pid) { wprintf(L"[!] target process not found: %s\n", argv[1]); return 2; }

    std::wstring dll = argv[2];
    wchar_t full[MAX_PATH];
    if (!GetFullPathNameW(dll.c_str(), MAX_PATH, full, nullptr)) {
        wprintf(L"[!] bad dll path\n"); return 3;
    }
    if (GetFileAttributesW(full) == INVALID_FILE_ATTRIBUTES) {
        wprintf(L"[!] dll missing: %s\n", full); return 3;
    }

    EnableDebugPrivilege();

    HANDLE hProc = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                               PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ,
                               FALSE, pid);
    if (!hProc) { wprintf(L"[!] OpenProcess failed: %lu\n", GetLastError()); return 4; }

    size_t bytes = (wcslen(full) + 1) * sizeof(wchar_t);
    void* remote = VirtualAllocEx(hProc, nullptr, bytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remote) { wprintf(L"[!] VirtualAllocEx failed: %lu\n", GetLastError()); CloseHandle(hProc); return 5; }

    if (!WriteProcessMemory(hProc, remote, full, bytes, nullptr)) {
        wprintf(L"[!] WriteProcessMemory failed: %lu\n", GetLastError()); return 6;
    }

    HMODULE k32 = GetModuleHandleW(L"kernel32.dll");
    FARPROC loadLib = GetProcAddress(k32, "LoadLibraryW");
    HANDLE th = CreateRemoteThread(hProc, nullptr, 0, (LPTHREAD_START_ROUTINE)loadLib, remote, 0, nullptr);
    if (!th) { wprintf(L"[!] CreateRemoteThread failed: %lu\n", GetLastError()); return 7; }

    WaitForSingleObject(th, 15000);
    DWORD code = 0;
    GetExitCodeThread(th, &code);
    CloseHandle(th);
    VirtualFreeEx(hProc, remote, 0, MEM_RELEASE);
    CloseHandle(hProc);

    wprintf(L"[+] injected into pid %lu, LoadLibraryW returned 0x%lx\n", pid, code);
    wprintf(L"[+] control channel: 127.0.0.1:17880\n");
    return code ? 0 : 8;
}
