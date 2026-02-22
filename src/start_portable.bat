@echo off
REM Portable launcher for the Python app 
SETLOCAL
SET "BASEDIR=%~dp0"
SET "VENV_DIR=%BASEDIR%.venv"
IF NOT EXIST "%VENV_DIR%\Scripts\python.exe" (
    echo Virtual environment not found! Cannot start.
    echo Copy the full .venv folder for portable use.
    pause
    exit /b 1
)
REM Start app direct met venv-python
start "" "%VENV_DIR%\Scripts\python.exe" app_launcher.py
ENDLOCAL
GOTO :EOF
