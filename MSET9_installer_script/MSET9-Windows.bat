@echo off
chcp 65001 > nul

set PY1="py"
set PY2="%WINDIR%\py"
set PY3="%LOCALAPPDATA%\Programs\Python\Launcher\py"

setlocal enableDelayedExpansion
for /l %%x in (1, 1, 3) do (
	set PY=!PY%%x!
	!PY! -V > nul 2> nul
	if !errorlevel! EQU 0 goto found
)
endlocal

echo Python 3 is not installed.
echo Please install Python 3 and try again.
echo https://www.python.org/downloads/
echo.
pause
exit

:found
%PY% -3 mset9.py
if %errorlevel% NEQ 0 pause
