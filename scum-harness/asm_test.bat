@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0plugin"
echo --- A: no /Fo ---
ml64 /nologo /c dwmapi_thunks.asm
echo exit=%errorlevel%
dir /b *.obj 2>nul
echo --- B: /Fo with space ---
ml64 /nologo /c /Fo dwmapi_thunks2.obj dwmapi_thunks.asm
echo exit=%errorlevel%
dir /b *.obj 2>nul
