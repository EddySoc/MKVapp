# MKVapp

Repository: https://github.com/EddySoc/MKVapp

Short summary
- Desktop GUI application for MKV/media utilities.
- Settings (external tools like ffmpeg/ffsubsync/mkvtoolnix) are stored in the `Settings/` folder and must be configured for runtime.

Quick build (development)
1. create and activate a virtualenv

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app in-place

```powershell
& .venv\Scripts\python.exe -m app_launcher
```

Quick PyInstaller single-file build (example)
```powershell
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean MKVApp.spec
```

Notes
- This README was added automatically during a workspace cleanup on 2026-02-22.
- Do not commit the `.venv/` directory; use the provided `requirements.txt` to recreate the environment.
- If you want me to create a GitHub release and upload a ZIP, say so and provide release notes.
