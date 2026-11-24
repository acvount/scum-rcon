@echo off
rem build.bat — 编译注入 DLL（需要 VS 2022 Build Tools 的 cl.exe）
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

cl /nologo /std:c++17 /EHsc /O2 /MT /LD ^
   /D_WINDOWS /D_USRDLL ^
   ue.cpp reflect.cpp dllmain.cpp ^
   /link /OUT:scum_harness.dll /DEF:scum_harness.def ws2_32.lib psapi.lib
if errorlevel 1 ( echo [!] build failed & exit /b 1 )
echo [+] built scum_harness.dll
endlocal
