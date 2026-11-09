@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo ERROR: Project virtual environment not found: "%PYTHON%"
    echo This installer must be placed in the TradingAgents project root.
    pause
    exit /b 1
)

findstr /x /c:"dashboard.html" .gitignore >nul 2>&1
if errorlevel 1 echo dashboard.html>>.gitignore

"%PYTHON%" -m py_compile "%~dp0dashboard.py"
if errorlevel 1 (
    echo ERROR: Dashboard syntax check failed.
    pause
    exit /b 1
)

"%PYTHON%" "%~dp0dashboard.py"
if errorlevel 1 (
    echo ERROR: Dashboard generation failed.
    pause
    exit /b 1
)

start "" "%~dp0dashboard.html"
echo.
echo Dashboard setup complete.
echo Add dashboard.py, run_daily.bat and LOCAL_AUTOMATION_GUIDE.md to Git.
pause
