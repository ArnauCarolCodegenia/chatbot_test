@echo off
REM =============================================================================
REM  Google ADK Project — Windows virtual environment setup
REM  Run this script ONCE from the project root to create + activate the venv
REM  and install all dependencies.
REM
REM  Usage:
REM    setup_venv.bat
REM
REM  After first run, activate manually with:
REM    .venv\Scripts\activate.bat
REM =============================================================================

setlocal

echo.
echo ============================================================
echo  ADK Project — Virtual Environment Setup (Windows)
echo ============================================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo        Install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

REM Create venv
echo.
echo [2/5] Creating virtual environment in .venv ...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate venv
echo.
echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo [5/5] Installing project dependencies from requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Some packages failed to install. Check the output above.
    pause
    exit /b 1
)

REM Copy .env if not present
if not exist .env (
    echo.
    echo [INFO] No .env file found.
    echo        A template has been provided — edit it before running the project:
    echo        notepad .env
) else (
    echo.
    echo [INFO] .env already exists — skipping copy.
)

echo.
echo ============================================================
echo  Setup complete!
echo.
echo  Next steps:
echo    1. Edit .env with your API keys and project settings.
echo    2. Activate the venv (already active in this session):
echo         .venv\Scripts\activate.bat
echo    3. Launch the ADK dev UI:
echo         adk web
echo    4. Or run a quick CLI test:
echo         python main.py "Hello, what can you do?"
echo ============================================================
echo.

endlocal
pause
