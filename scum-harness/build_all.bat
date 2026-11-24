@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0plugin"

rem --- asm hooks (shared by both DLLs) ---
ml64 /nologo /c vthooks.asm
if errorlevel 1 ( echo ASM_BUILD_FAILED & exit /b 1 )

rem --- 1) injectable plugin ---
cl /nologo /utf-8 /std:c++17 /EHa /O2 /MT /LD ^
   ue.cpp reflect.cpp dllmain.cpp entry_inject.cpp ^
   vthooks.obj ^
   /link /OUT:scum_harness.dll ws2_32.lib psapi.lib
if errorlevel 1 ( echo PLUGIN_BUILD_FAILED & exit /b 1 )
echo PLUGIN_BUILD_OK

rem --- 2) dwmapi proxy: loads with the server at startup ---
ml64 /nologo /c dwmapi_thunks.asm
if errorlevel 1 ( echo ASM_BUILD_FAILED & exit /b 1 )
cl /nologo /utf-8 /std:c++17 /EHa /O2 /MT /LD ^
   ue.cpp reflect.cpp dllmain.cpp proxy_entry.cpp dwmapi_bridge.cpp ^
   dwmapi_thunks.obj vthooks.obj ^
   /link /OUT:dwmapi.dll /DEF:dwmapi_proxy.def ws2_32.lib psapi.lib
if errorlevel 1 ( echo PROXY_BUILD_FAILED & exit /b 1 )
echo PROXY_BUILD_OK

cd /d "%~dp0injector"
cl /nologo /utf-8 /std:c++17 /EHsc /O2 /MT inject.cpp /link /OUT:scum_inject.exe advapi32.lib
if errorlevel 1 ( echo INJECTOR_BUILD_FAILED & exit /b 1 )
echo INJECTOR_BUILD_OK
endlocal
