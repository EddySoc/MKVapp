@echo off
REM Start MKVApp vanuit de juiste src-map, ongeacht waar je deze batch uitvoert
SET "VENV_DIR=%~dp0venv"
SET "SRC_DIR=%~dp0src"

REM Activeer venv als nodig (optioneel, voor interactief gebruik)
REM call "%VENV_DIR%\Scripts\activate.bat"

REM Start de app
"%VENV_DIR%\Scripts\python.exe" "%SRC_DIR%\app_launcher.py"

pause
