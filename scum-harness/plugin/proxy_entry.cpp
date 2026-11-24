// proxy_entry.cpp — DllMain for the dwmapi proxy build (loads with SCUMServer.exe)
#include <windows.h>
extern "C" void HarnessAttach(HMODULE hModule);
void InitDwmapiForwarders(HMODULE self);

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        // Forwarders must resolve before any dwmapi export is called.
        InitDwmapiForwarders(hModule);
        HarnessAttach(hModule);
    }
    return TRUE;
}
