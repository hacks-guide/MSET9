@echo off

for /f "tokens=4,5 delims=,. "  %%a in ('ver') do set WINBUILD=%%a.%%b
call :compareVersions %WINBUILD% 10.0
if %errorlevel% NEQ -1 chcp 65001 >nul

set MINPYVER=3.7

set PY1="py"
set PY2="%WINDIR%\py"
set PY3="%LOCALAPPDATA%\Programs\Python\Launcher\py"

setlocal enableDelayedExpansion
for /l %%x in (1, 1, 3) do (
	set PY=!PY%%x!
	!PY! -V >nul 2>nul
	if !errorlevel! EQU 0 goto found_launcher
)
endlocal

set REG1="HKCU\SOFTWARE\Python\PythonCore"
set REG2="HKLM\SOFTWARE\Python\PythonCore"
set REG3="HKLM\SOFTWARE\Microsoft\AppModel\Lookaside\user\Software\Python\PythonCore"

setlocal enableDelayedExpansion
for /l %%x in (1, 1, 3) do (
	set REGK=!REG%%x!
	call :getPythonFromReg !REGK!
	call :compareVersions !PYVER! !MINPYVER!
	if !errorlevel! NEQ -1 goto found_python
)
endlocal



echo Python 3 is not installed.
echo Please install Python 3 and try again.
echo https://www.python.org/downloads/
echo.
pause
exit

:outdated
echo Python %PYVER% is too old, you need %MINPYVER% or later.
echo Please install newer version and try again.
echo https://www.python.org/downloads/
echo.
pause
exit



:found_launcher
call :testPython %PY% -3
if %errorlevel% NEQ 0 goto outdated
call :launchInstaller %PY% -3

:found_python
call :testPython %PY%
if %errorlevel% NEQ 0 goto outdated
call :launchInstaller %PY%



exit

:launchInstaller
%* mset9.py
if %errorlevel% NEQ 0 pause
exit

:testPython
for /F "tokens=* USEBACKQ" %%o in (`%* -V`) do (
	set PYVER=%%o
)
set PYVER=%PYVER:* =%
call :compareVersions %PYVER% %MINPYVER%
if %errorlevel% EQU -1 exit /b 1
exit /b 0

:getPythonFromReg
setlocal enableDelayedExpansion
set PYVER=0.0
set PY=""
set REGK="%1"
for /F "tokens=* USEBACKQ" %%k in (`reg query %REGK% /k /f * 2^>nul`) do (
	set k=%%k
	if "!k:~0,2!"=="HK" (
		for %%v in ("!k!") do set "v=%%~nxv"
		call :compareVersions !PYVER! !v!
		if !errorlevel! EQU -1 (
			set PYVER=!v!
			for /f "tokens=2* USEBACKQ" %%o in (`reg query "%REGK:"=%\!v!\InstallPath" /v ExecutablePath ^|findstr /ri "REG_SZ"`) do set PY="%%p"
		)
	)
)
endlocal & (
	set PYVER=%PYVER%
	set PY=%PY%
)
exit /b

:: from: https://stackoverflow.com/questions/15807762/compare-version-numbers-in-batch-file
:compareVersions  version1  version2
::
:: Compares two version numbers and returns the result in the ERRORLEVEL
::
:: Returns 1 if version1 > version2
::         0 if version1 = version2
::        -1 if version1 < version2
::
:: The nodes must be delimited by . or , or -
::
:: Nodes are normally strictly numeric, without a 0 prefix. A letter suffix
:: is treated as a separate node
::
setlocal enableDelayedExpansion
set "v1=%~1"
set "v2=%~2"
call :divideLetters v1
call :divideLetters v2
:loop
call :parseNode "%v1%" n1 v1
call :parseNode "%v2%" n2 v2
if %n1% gtr %n2% exit /b 1
if %n1% lss %n2% exit /b -1
if not defined v1 if not defined v2 exit /b 0
if not defined v1 exit /b -1
if not defined v2 exit /b 1
goto :loop

:parseNode  version  nodeVar  remainderVar
for /f "tokens=1* delims=.,-" %%A in ("%~1") do (
  set "%~2=%%A"
  set "%~3=%%B"
)
exit /b

:divideLetters  versionVar
for %%C in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do set "%~1=!%~1:%%C=.%%C!"
exit /b

