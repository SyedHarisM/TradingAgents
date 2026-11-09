@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo ERROR: Project virtual environment not found: "%PYTHON%"
    exit /b 1
)

echo ============================================================
echo TradingAgents daily automation
echo ============================================================

"%PYTHON%" "%~dp0daily_bot.py"
set "BOT_EXIT=%ERRORLEVEL%"

"%PYTHON%" "%~dp0dashboard.py"
set "DASHBOARD_EXIT=%ERRORLEVEL%"

if not "%BOT_EXIT%"=="0" exit /b %BOT_EXIT%
exit /b %DASHBOARD_EXIT%
