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


def _parse_filebot_data_dir_from_sysinfo(text):
    for line in (text or "").splitlines():
        if line.startswith("DATA:"):
            value = line.split(":", 1)[1].strip()
            if " @ " in value:
                value = value.split(" @ ", 1)[0].strip()
            return value
    return None


def _resolve_filebot_settings_path():
    # 1) explicit FILEBOT_DATA (if set)
    filebot_data = os.environ.get("FILEBOT_DATA")
    if filebot_data:
        return os.path.join(filebot_data, "settings.properties")

    # 2) ask filebot runtime where DATA dir is
    try:
        info = subprocess.run(
            ["filebot", "-script", "fn:sysinfo"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        data_dir = _parse_filebot_data_dir_from_sysinfo(info.stdout)
        if data_dir:
            return os.path.join(data_dir, "settings.properties")
    except Exception:
        pass

    # 3) fallback to common Windows location
    return r"C:\Video\Filebot\data\settings.properties"


def get_filebot_credentials():
    from shared_data import get_shared
    import json

    try:
        from utils.shared_utils import get_settings_file
    except Exception:
        get_settings_file = None

    s = get_shared()
    config = getattr(s, "config", {}) or {}
    api_cfg = config.get("API_cfg", {})

    fb_user = api_cfg.get("filebot", {}).get("username")
    fb_pass = api_cfg.get("filebot", {}).get("password")

    # Fallback if user kept credentials under opensubtitles section
    if not fb_user:
        fb_user = api_cfg.get("opensubtitles", {}).get("username")
    if not fb_pass:
        fb_pass = api_cfg.get("opensubtitles", {}).get("password")

    if fb_user and fb_pass:
        return fb_user, fb_pass

    if get_settings_file is not None:
        try:
            settings_path = get_settings_file("API_cfg")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                fb_user = raw.get("filebot", {}).get("username") or raw.get("opensubtitles", {}).get("username")
                fb_pass = raw.get("filebot", {}).get("password") or raw.get("opensubtitles", {}).get("password")
                if fb_user and fb_pass:
                    return fb_user, fb_pass
        except Exception:
            pass

    return None, None


def _write_or_update_filebot_login(settings_path, username, password):
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    login_key = "net/filebot/login/OpenSubtitles"
    login_value = f"{username}\\t{password}"

    lines = []
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()

    replaced = False
    out = []
    for line in lines:
        if line.startswith(login_key + "="):
            out.append(f"{login_key}={login_value}")
            replaced = True
        else:
            out.append(line)

    if not replaced:
        out.append(f"{login_key}={login_value}")

    with open(settings_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")


def configure_filebot_from_api_cfg():
    from utils.text_helpers import update_tbsettings

    user, pwd = get_filebot_credentials()
    if not user or not pwd:
        update_tbsettings(
            "⚠️ Geen FileBot credentials in API_cfg.json. Voeg filebot.username en filebot.password toe.",
            "geel",
        )
        return

    try:
        settings_path = _resolve_filebot_settings_path()
        _write_or_update_filebot_login(settings_path, user, pwd)
        update_tbsettings(f"✅ FileBot account geconfigureerd in: {settings_path}", "groen")
    except Exception as e:
        update_tbsettings(f"❌ FileBot config failed: {e}", "rood")


def clear_filebot_cache():
    from utils.text_helpers import update_tbsettings

    try:
        result = subprocess.run(
            ["filebot", "-clear-cache"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            update_tbsettings("✅ FileBot cache cleared", "groen")
            if output:
                print(output)
        else:
            update_tbsettings(f"❌ FileBot cache clear failed: {output or 'unknown error'}", "rood")
    except FileNotFoundError:
        update_tbsettings("❌ FileBot not found in PATH.", "rood")
    except Exception as e:
        update_tbsettings(f"❌ FileBot cache clear error: {e}", "rood")


def test_filebot_login():
    from utils.text_helpers import update_tbsettings

    update_tbsettings("🧪 Testing FileBot/OpenSubtitles account...", "info")

    try:
        result = subprocess.run(
            ["filebot", "-script", "fn:configure"],
            capture_output=True,
            text=True,
            timeout=25,
        )
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        out_lower = output.lower()

        if result.returncode == 0 and "checking... ok" in out_lower:
            # Optional diagnostics if present
            vip_line = None
            remain_line = None
            for line in output.splitlines():
                if line.strip().lower().startswith("vip:"):
                    vip_line = line.strip()
                if line.strip().lower().startswith("remaining_downloads:"):
                    remain_line = line.strip()

            if vip_line:
                update_tbsettings(f"✅ FileBot login OK ({vip_line})", "groen")
            else:
                update_tbsettings("✅ FileBot login OK", "groen")

            if remain_line:
                update_tbsettings(f"ℹ️ {remain_line}", "normal")
            return

        # Explicit auth failures from provider responses
        if "401 unauthorized" in out_lower or "invalid" in out_lower or "failed" in out_lower:
            msg = output.strip().splitlines()[-1] if output.strip() else "auth failed"
            update_tbsettings(f"❌ FileBot login failed: {msg}", "rood")
            return

        # Generic non-OK result
        tail = output.strip().splitlines()[-1] if output.strip() else "no output"
        update_tbsettings(f"⚠️ FileBot test inconclusive: {tail}", "geel")

    except FileNotFoundError:
        update_tbsettings("❌ FileBot not found in PATH.", "rood")
    except subprocess.TimeoutExpired:
        update_tbsettings("⚠️ FileBot test timed out (possibly waiting for interactive input).", "geel")
    except Exception as e:
        update_tbsettings(f"❌ FileBot login test error: {e}", "rood")

def get_opensub_api_key():
    from shared_data import get_shared
    import json

    try:
        from utils.shared_utils import get_settings_file
    except Exception:
        get_settings_file = None

    s = get_shared()
    config = getattr(s, "config", {}) or {}
    api_key = (
        config.get("API_cfg", {})
        .get("opensubtitles", {})
        .get("api_key")
    )
    if api_key:
        return api_key

    if get_settings_file is not None:
        try:
            settings_path = get_settings_file("API_cfg")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                return raw.get("opensubtitles", {}).get("api_key")
        except Exception:
            pass

    return None

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

    success = False
    if method == "filebot":
        success = _download_with_filebot(video_path, lang_code2)
        if not success and get_opensub_api_key():
            tb_update('tb_info', "⚠️ FileBot failed, trying OpenSubtitles API...", "geel")
            success = _download_with_opensubtitles(video_path, lang_code2, lang_code3)
    else:
        success = _download_with_opensubtitles(video_path, lang_code2, lang_code3)

    if success:
        tb_update('tb_info', f"✅ Downloaded: {file_name}", "normal")
    else:
        tb_update('tb_info', f"⚠️ No subtitles downloaded: {file_name}", "geel")

def _download_with_opensubtitles(video_path, lang_code2, lang_code3):
    from utils import log_error

    OPENSUB_API_KEY = get_opensub_api_key()
    if not OPENSUB_API_KEY:
        log_error("❌ OpenSubtitles API key missing in API_cfg.json")
        return False

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
            log_error(f"\u274c API request failed: {resp.status_code} \u2014 {resp.text}")
            return False

        data = resp.json()
        results = data.get("data", [])
        if not results:
            log_error(f"⚠️ No subtitles found via OpenSubtitles API: {base}", tag="geel")
            return False

        result = results[0]
        file_id = result["attributes"]["files"][0]["file_id"]

        dl_resp = requests.post("https://api.opensubtitles.com/api/v1/download",
                                headers=headers, json={"file_id": file_id})
        if dl_resp.status_code != 200:
            log_error(f"❌ Download request failed: {dl_resp.status_code} — {dl_resp.text}")
            return False

        link = dl_resp.json().get("link")
        if not link:
            log_error("\u274c No download link found.")
            return False

        file_resp = requests.get(link)
        file_resp.raise_for_status()
        text = file_resp.text
        output = os.path.join(os.path.dirname(video_path), f"{base}.{lang_code3}.srt")
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)

        return True

    except Exception as e:
        log_error(f"⚠️ Subtitle download error: {e}")
        return False

def _download_with_filebot(video_path, lang_code2):
    from utils import log_error

    #print(f"🎬 Using FileBot for: {os.path.basename(video_path)}")

    try:
        result = subprocess.run([
            "filebot", "-get-subtitles", video_path,
            "--lang", lang_code2,
            "--output", "srt", "--encoding", "UTF-8"
        ], capture_output=True, text=True)

        output = result.stdout.strip() or result.stderr.strip()
        if output:
            print(output)

        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode == 0 and "no subtitles" not in combined_output and "401 unauthorized" not in combined_output:
            return True

        log_error(f"⚠️ FileBot failed: {output or 'unknown error'}", tag="geel")
        return False

    except FileNotFoundError:
        print("🚫 FileBot not found. Is it installed and in PATH?")
        return False

def process_selected_files(app, processor_fn):
    from shared_data import get_shared
    from utils import update_tbinfo
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
