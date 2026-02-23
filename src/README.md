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

Changelog (selected recent fixes)
-------------------------------
- Fix: Correct folder selection when multiple folders share the same basename (e.g. multiple `s01` folders).
	- Files changed: `utils/scan_helpers.py` — store folder display keys (including indentation) in `folder_path_map` and resolve selection via the full display string.
- Fix: Clicking a folder line now reliably resolves to the correct full path and updates `lb_files`.
	- Files changed: `widgets/base_textbox.py` — forward index args in `BaseTBox.get`, improve click-to-path lookup, and make parent-navigation detection more robust.
- Fix: Parent navigation (⬆️ / `[..]`) now correctly goes to the normalized parent folder even when paths have trailing slashes.
	- Files changed: `actions/tb_folders/folder_nav.py` — compute parent from the normalized `base_path`.

If you want these changes committed to the repo history, I can create the git commit now (and optionally push it to a remote). Say `commit` to proceed or `no` to skip.
