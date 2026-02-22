#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:      actions_extract.pyn
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# popup_actions/actions_extract.py

import os, sys, shutil, subprocess, re
from tqdm import tqdm
from pymediainfo import MediaInfo
from concurrent.futures import ThreadPoolExecutor
from decorators.decorators import menu_tag

ISO6392_TO_ISO6393 = {
    "ar": "ara", "bg": "bul", "cs": "ces", "da": "dan", "de": "deu", 
    "el": "ell", "en": "eng", "es": "spa", "et": "est", "fi": "fin",
    "fr": "fra", "he": "heb", "hi": "hin", "hu": "hun", "id": "ind",
    "it": "ita", "ja": "jpn", "ko": "kor", "lt": "lit", "lv": "lav",
    "ms": "msa", "nl": "nld", "no": "nor", "pl": "pol", "pt": "por",
    "ru": "rus", "sk": "slk", "sl": "slv", "sv": "swe", "ta": "tam",
    "te": "tel", "th": "tha", "tr": "tur", "uk": "ukr", "vi": "vie",
    "zh": "zho"
}

def get_mkvextract_path():
    """Get mkvextract executable path from config or PATH"""
    import json
    
    # First check if it's in PATH
    if shutil.which("mkvextract"):
        return "mkvextract"
    
    # Check config file for custom path
    try:
        config_path = os.path.join("Settings", "tools_cfg.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                mkvtoolnix_path = config.get("mkvtoolnix_path", "")
                
                if mkvtoolnix_path:
                    # Try mkvextract.exe in the specified directory
                    mkvextract_exe = os.path.join(mkvtoolnix_path, "mkvextract.exe")
                    if os.path.exists(mkvextract_exe):
                        return mkvextract_exe
    except Exception as e:
        print(f"⚠️ Error reading tools config: {e}")
    
    return None

@menu_tag(label="Extract Subs", group="videos")
def extract_subtitles():
    """Extract subtitles from selected MKV files"""
    from shared_data import get_shared
    from utils import log_error
    from utils.text_helpers import tb_update
    
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    
    if not selected:
        log_error("⚠️ No files selected.")
        return
    
    mkv_files = [f for f in selected if f.lower().endswith(".mkv")]
    
    if not mkv_files:
        log_error("⚠️ No MKV files selected")
        return
    
    # Check if mkvextract is available
    mkvextract_path = get_mkvextract_path()
    if not mkvextract_path:
        log_error("❌ mkvextract not found. Please:")
        log_error("   1. Install MKVToolNix, OR")
        log_error("   2. Set path in Settings/tools_cfg.json")
        return
    
    tb_update('tb_info', f"🎯 Extract Subs - {len(mkv_files)} file(s)", "normal")
    
    # Update progress bar
    if hasattr(s.app, 'progress_bar'):
        s.app.progress_bar.set(0)
    
    for idx, mkv_file in enumerate(mkv_files):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        output_dir = os.path.dirname(mkv_file)  # Same directory as video
        extract_subtitles_from_mkv(mkv_file, output_dir, mkvextract_path)
        
        # Update progress bar
        if hasattr(s.app, 'progress_bar'):
            progress = (idx + 1) / len(mkv_files)
            s.app.progress_bar.set(progress)
    
    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ Extract Subs complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")
    
    # Refresh the listbox to show extracted subtitle files
    from utils.scan_helpers import reload
    reload(s.app)

def extract_subtitles_from_mkv(mkv_file, output_dir, mkvextract_path):
    """Extract subtitles from a single MKV file"""
    from utils import log_error
    from utils.text_helpers import tb_update
    
    info = MediaInfo.parse(mkv_file)
    
    # Show which file we're processing
    tb_update('tb_info', f"📂 Processing: {os.path.basename(mkv_file)}", "normal")

    for track in info.tracks:
        if track.track_type == "Text":
            lang_short2 = (track.language or "und")[:2]
            lang_short3 = ISO6392_TO_ISO6393.get(lang_short2, "und")
            if lang_short3 == "und":
                log_error(f"⚠️ Unknown language: {track.language}")
                continue

            track_id = track.track_id - 1
            base = os.path.splitext(os.path.basename(mkv_file))[0]
            out_file = os.path.join(output_dir, f"{base}-{lang_short3}.srt")

            try:
                with open(os.devnull, 'w') as devnull:
                    subprocess.run([mkvextract_path, "tracks", mkv_file,
                                    f"{track_id}:{out_file}"],
                                   check=True, stdout=devnull, stderr=devnull)
                tb_update('tb_info', f"✅ Extracted: {os.path.basename(out_file)}", "normal")
            except subprocess.CalledProcessError as e:
                error_msg = f"⚠️ Failed to extract track {track_id}: {e}"
                log_error(error_msg)

def extract_subtitles_from_directory(directory, out_folder="subs"):
    out_dir = os.path.join(directory, out_folder)
    os.makedirs(out_dir, exist_ok=True)

    mkv_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(directory)
        for f in files if f.endswith(".mkv")
    ]

    print(f"🎯 Found {len(mkv_files)} MKV files.")
    mkvextract_path = get_mkvextract_path()
    if not mkvextract_path:
        print("❌ mkvextract not found")
        return
    
    for mkv_file in mkv_files:
        extract_subtitles_from_mkv(mkv_file, out_dir, mkvextract_path)

def validate_mkvextract():
    if not shutil.which("mkvextract"):
        print("🚫 mkvextract not found in PATH.")
        sys.exit(1)

# ========== MKV CONVERSION (fast) ==========

def extract_size(line):
    match = re.search(r"size=\s*(\d+)(KiB|MiB|GiB)", line)
    if match:
        val = int(match.group(1))
        factor = {"KiB": 1024, "MiB": 2**20, "GiB": 2**30}
        return val * factor[match.group(2)]
    return None

def convert_to_mkv_cli(input_file, output_file):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-c:v", "libx265", "-preset", "fast", "-crf", "28",
        "-c:a", "aac", "-threads", "8",
        "-loglevel", "info", "-stats", output_file
    ]

    print(f"🎬 Converting {input_file} → {output_file}")
    total = os.path.getsize(input_file)
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    bar = tqdm(total=total, unit="B", unit_scale=True, desc="Converting")

    for line in proc.stderr:
        if "size=" in line:
            new_size = extract_size(line)
            if new_size:
                bar.update(new_size - bar.n)

    proc.wait()
    bar.close()

def backup_original(input_file, backup_dir):
    parent = os.path.basename(os.path.dirname(input_file))
    dest_dir = os.path.join(backup_dir, parent)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(input_file))
    shutil.move(input_file, dest)
    print(f"💾 Backup: {dest}")
    return dest

def process_file(input_file, backup_dir):
    try:
        backed = backup_original(input_file, backup_dir)
        output_file = os.path.splitext(input_file)[0] + ".mkv"
        convert_to_mkv_cli(backed, output_file)

        s = get_shared()
        if s.gui_queue:
            from utils.text_helpers import update_tbinfo
            s.gui_queue.put(lambda: update_tbinfo(f"✅ Converted: {input_file}", "groen"))
    except Exception as e:
        print(f"❌ Error: {input_file}\n{e}")

def process_directory(root, backup_dir):
    tasks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for subdir, _, files in os.walk(root):
            for f in files:
                if f.endswith((".mp4", ".avi", ".mov", ".webm", ".m4v")):
                    path = os.path.join(subdir, f)
                    tasks.append(executor.submit(process_file, path, backup_dir))

        for t in tasks:
            t.result()