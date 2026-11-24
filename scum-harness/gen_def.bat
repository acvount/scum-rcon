@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0plugin"
echo LIBRARY dwmapi> dwmapi_proxy.def
echo EXPORTS>> dwmapi_proxy.def
dumpbin /nologo /exports C:\Windows\System32\dwmapi.dll | findstr /R "^ *[0-9][0-9]* *[0-9]* *[0-9A-F]* *[A-Za-z]" >> dwmapi_proxy.def
