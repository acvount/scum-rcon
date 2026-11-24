// entry_inject.cpp — DllMain for the injectable build
#include <windows.h>
extern "C" void HarnessAttach(HMODULE hModule);

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) HarnessAttach(hModule);
    return TRUE;
}
