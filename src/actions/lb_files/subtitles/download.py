#-------------------------------------------------------------------------------
# Name:        actions_download.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# popup_actions/actions_download.py

import os
import requests
import subprocess
from decorators.decorators import menu_tag

def get_opensub_api_key():
    return config.get("opensubtitles", {}).get("api_key")

@menu_tag(label="Download Sub", icon="🔽", group="videos")
def download_subtitles_for_selected(app=None):
    from shared_data import get_shared
    from utils.text_helpers import tb_update
    s = get_shared()
    app = app or s.app
    
    # Close any open menus immediately
    app.update_idletasks()
    app.update()
    
    # Get selected files first to count them
    selection = app.lb_files.listbox.curselection()
    if not selection:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No files selected.", "geel")
        return
    
    tb_update('tb_info', f"🔽 Download Sub - {len(selection)} file(s)", "normal")
    
    process_selected_files(app, _download_subtitle_logic)
    
    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ Download Sub complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")
    
    # Refresh the listbox to show downloaded subtitles
    from utils.scan_helpers import reload
    reload(app)

def _download_subtitle_logic(app, video_path, file_name):
    from shared_data import get_shared
    from utils.text_helpers import tb_update
    s = get_shared()
    config = s.config
    cfg = config.get("persistent_cfg", {})
    lang_code3 = cfg.get("Language", "eng")
    lang_code2 = config.get("lang_dict", {}).get(lang_code3, ["en"])[0]
    method = cfg.get("SubtitleMethod", "api")

    tb_update('tb_info', f"🔽 Downloading: {file_name}", "normal")
    
    if method == "filebot":
        _download_with_filebot(video_path, lang_code2)
    else:
        _download_with_opensubtitles(video_path, lang_code2, lang_code3)
    
    tb_update('tb_info', f"✅ Downloaded: {file_name}", "normal")

def _download_with_opensubtitles(video_path, lang_code2, lang_code3):
    OPENSUB_API_KEY = get_opensub_api_key()
    base = os.path.splitext(os.path.basename(video_path))[0]
    query = base.replace(".", " ")
    headers = {
        "Api-Key": OPENSUB_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MkvTool v1.0"
    }

    #print(f"🔍 Searching subtitles for: {query}")
    search_url = f"https://api.opensubtitles.com/api/v1/subtitles?query={query}&languages={lang_code2}"

    try:
        resp = requests.get(search_url, headers=headers)
        if resp.status_code != 200:
            from utils import log_error
            log_error(f"\u274c API request failed: {resp.status_code} \u2014 {resp.text}")
            return

        data = resp.json()
        result = data.get("data", [])[0]
        file_id = result["attributes"]["files"][0]["file_id"]

        dl_resp = requests.post("https://api.opensubtitles.com/api/v1/download",
                                headers=headers, json={"file_id": file_id})
        link = dl_resp.json().get("link")
        if not link:
            from utils import log_error
            log_error("\u274c No download link found.")
            return

        text = requests.get(link).text
        output = os.path.join(os.path.dirname(video_path), f"{base}.{lang_code3}.srt")
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)

        #print(f"✅ Saved: {output}")

    except Exception as e:
        from utils import log_error
        log_error(f"⚠️ Subtitle download error: {e}")

def _download_with_filebot(video_path, lang_code2):
    #print(f"🎬 Using FileBot for: {os.path.basename(video_path)}")

    try:
        result = subprocess.run([
            "filebot", "-get-subtitles", video_path,
            "--lang", lang_code2,
            "--output", "srt", "--encoding", "UTF-8"
        ], capture_output=True, text=True)

        print(result.stdout.strip() or result.stderr.strip())

        if not result.returncode == 0:
            print("❌ FileBot failed.")

    except FileNotFoundError:
        print("🚫 FileBot not found. Is it installed and in PATH?")

def process_selected_files(app, processor_fn):
    from shared_data import get_shared
    from utils.text_helpers import tb_update
    s = get_shared()
    selection = app.lb_files.listbox.curselection()
    if not selection:
        from utils import log_error
        log_error("⚠️ No files selected.")
        return

    total = len(selection)
    s.bottomrow_label.label.grid_remove()
    s.bottomrow_label.progress.grid()
    s.bottomrow_label.progress.configure(mode="determinate")
    s.bottomrow_label.progress.set(0)

    for idx, index in enumerate(selection):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
            
        file_name = app.lb_files.listbox.get(index)
        video_path = app.file_path_map.get(file_name)

        progress = (idx + 1) / total
        s.bottomrow_label.progress.set(progress)
        app.update_idletasks()

        if not video_path or not os.path.exists(video_path):
            msg = f"❌ Missing: {file_name}"
            update_tbinfo(msg,"rood")
        else:
            processor_fn(app, video_path, file_name)

        app.lb_files.deselect_item_by_index(index)

    s.bottomrow_label.progress.set(1.0)
    
    # Rescan directory to show new subtitle files
    try:
        if selection:
            file_name = app.lb_files.listbox.get(selection[0])
            first_video_path = app.file_path_map.get(file_name)
            if first_video_path:
                scan_path = os.path.dirname(first_video_path)
                from utils.scan_helpers import fast_scandir, update_lb
                fast_scandir(app, scan_path)
                update_lb(app)
                update_tbinfo("🔄 File list refreshed", tag="groen")
    except Exception as e:
        update_tbinfo(f"⚠️ Refresh failed: {e}", tag="geel")
