
@echo off
REM Portable launcher: gebruik altijd venv-python
SETLOCAL
SET "BASEDIR=%~dp0"
SET "VENV_DIR=%BASEDIR%venv"
echo BASEDIR: %BASEDIR%
echo VENV_DIR: %VENV_DIR%


IF NOT EXIST "%VENV_DIR%\Scripts\python.exe" (
    echo [DEBUG] Virtuele omgeving niet gevonden! Kan niet starten.
    echo [DEBUG] Kopieer de volledige venv-map mee voor portable gebruik.
    pause
    exit /b 1
)

REM Start app_launcher.py direct met venv-python
"%VENV_DIR%\Scripts\python.exe" app_launcher.py

ENDLOCAL
GOTO :EOF
