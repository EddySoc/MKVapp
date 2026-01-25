@echo off
REM Portable launcher for the Python app
SETLOCAL
SET "BASEDIR=%~dp0"
SET "VENV_DIR=%BASEDIR%venv"



IF NOT EXIST "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    IF %ERRORLEVEL% NEQ 0 GOTO VENV_ERROR
    echo Installing requirements (if requirements.txt exists)...
    IF EXIST "%BASEDIR%requirements.txt" "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%BASEDIR%requirements.txt"
)



REM Start app direct met venv-python
"%VENV_DIR%\Scripts\python.exe" app_launcher.py
ENDLOCAL
GOTO :EOF

:VENV_ERROR
echo Failed to create virtual environment. Ensure Python is installed and in PATH.
pause
exit /b 1
