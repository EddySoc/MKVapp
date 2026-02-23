@echo off
REM recreate_venv.bat - recreate the project virtual environment and install dependencies
REM Usage: run this from the project `src` folder: recreate_venv.bat









































endlocalecho    .venv\Scripts\activate.batecho To activate in cmd.exe:echo    & .venv\Scripts\Activate.ps1echo To activate the environment (PowerShell):
necho Done.)    echo You can manually install packages and then run the build.    echo No requirements file found (searched for venv_packages_*.txt and requirements.txt). Skipping install.) else (    .venv\Scripts\python.exe -m pip install -r %REQ%    echo Installing dependencies from %REQ% ...
nif defined REQ (if not defined REQ if exist requirements.txt set "REQ=requirements.txt"if not defined REQ if exist venv_packages.txt set "REQ=venv_packages.txt"if not defined REQ if exist venv_packages_after_cleanup.txt set "REQ=venv_packages_after_cleanup.txt"if not defined REQ if exist venv_packages_final.txt set "REQ=venv_packages_final.txt"if exist venv_packages_cleanup.txt set "REQ=venv_packages_cleanup.txt"set "REQ="
nREM Choose requirements file order: prefer pinned venv freeze if present.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
necho Upgrading pip, setuptools and wheel...)    exit /b 1    echo Failed to create virtualenv. Ensure `python` is on PATH and is the correct version.if errorlevel 1 (python -m venv .venv
necho Creating virtual environment `.venv`...)    )        exit /b 0        echo Aborting without changes.    ) else (        rmdir /s /q .venv        echo Removing existing .venv...    if /I "!REPLY!"=="y" (    set /p REPLY=`.venv` exists. Remove and recreate it? [y/N]: if exist .venv (
recho Checking for existing .venv folder...nsetlocal enabledelayedexpansion