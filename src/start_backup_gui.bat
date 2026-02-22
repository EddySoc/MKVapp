@echo off
REM Start MKVApp Backup GUI

echo.
echo ====================================
echo   Starting MKVApp Backup GUI
echo ====================================
echo.

REM Check if in virtual environment
if defined VIRTUAL_ENV (
    echo Using virtual environment: %VIRTUAL_ENV%
) else (
    REM Try to activate virtual environment
    if exist ".venv\Scripts\activate.bat" (
        echo Activating virtual environment...
        call .venv\Scripts\activate.bat
    ) else (
        echo Warning: Virtual environment not found
        echo Running with system Python...
    )
)

REM Run the backup GUI (module in scripts package)
python -m scripts.backup_gui

if errorlevel 1 (
    echo.
    echo Error running backup GUI!
    pause
)
