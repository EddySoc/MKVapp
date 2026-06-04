@echo off
REM Start MKVApp vanuit de juiste src-map, ongeacht waar je deze batch uitvoert
SET "SRC_DIR=%~dp0src"

REM Ondersteun zowel oude als nieuwe venv-locatie
if exist "%~dp0src\.venv\Scripts\python.exe" (
	SET "VENV_DIR=%~dp0src\.venv"
) else if exist "%~dp0venv\Scripts\python.exe" (
	SET "VENV_DIR=%~dp0venv"
) else (
	echo FOUT: Python venv niet gevonden.
	echo Verwacht op: "%~dp0src\.venv" of "%~dp0venv"
	exit /b 1
)

if not exist "%SRC_DIR%\app_launcher.py" (
	echo FOUT: app_launcher.py niet gevonden op "%SRC_DIR%\app_launcher.py"
	exit /b 1
)

REM Activeer venv als nodig (optioneel, voor interactief gebruik)
REM call "%VENV_DIR%\Scripts\activate.bat"

REM Start stil met pythonw (geen consolevenster), fallback naar python.exe
if exist "%VENV_DIR%\Scripts\pythonw.exe" (
	start "" /b "%VENV_DIR%\Scripts\pythonw.exe" "%SRC_DIR%\app_launcher.py"
) else (
	start "" /b "%VENV_DIR%\Scripts\python.exe" "%SRC_DIR%\app_launcher.py"
)

exit /b 0
