@echo off
REM Start MKVApp vanuit de juiste src-map, ongeacht waar je deze batch uitvoert
SET "VENV_DIR=%~dp0src\.venv"
SET "SRC_DIR=%~dp0src"

REM Activeer venv als nodig (optioneel, voor interactief gebruik)
REM call "%VENV_DIR%\Scripts\activate.bat"

REM Start de app
pushd "%SRC_DIR%"
"%VENV_DIR%\Scripts\python.exe" "app_launcher.py"
popd

pause
