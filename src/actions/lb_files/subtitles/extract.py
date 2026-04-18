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

def get_mediainfo_library_path():
    """Resolve MediaInfo.dll path for normal and frozen (PyInstaller) runs."""
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        dll_path = os.path.join(base_path, 'MediaInfo.dll')
        if os.path.exists(dll_path):
            return dll_path

    try:
        import pymediainfo
        dll_path = os.path.join(os.path.dirname(pymediainfo.__file__), 'MediaInfo.dll')
        if os.path.exists(dll_path):
            return dll_path
    except Exception:
        pass

    return None

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

_VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".webm"}

def get_ffmpeg_path():
    """Return ffmpeg executable path from tools_cfg or PATH."""
    import json
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        config_path = os.path.join("Settings", "tools_cfg.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = json.load(f)
            p = cfg.get("ffmpeg_path", "")
            if p and os.path.exists(p):
                return p
    except Exception:
        pass
    return None

def extract_subtitles_ffmpeg(video_path, output_dir, ffmpeg_path, ffprobe_path):
    """Extract text subtitles from a non-MKV video using ffmpeg/ffprobe."""
    from utils import log_error
    from utils.text_helpers import tb_update

    tb_update('tb_info', f"📂 Processing: {os.path.basename(video_path)}", "normal")

    # Probe subtitle streams
    cmd_probe = [
        ffprobe_path, "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=index,codec_name:stream_tags=language",
        "-of", "json",
        video_path
    ]
    try:
        result = subprocess.run(cmd_probe, capture_output=True, text=True)
        import json
        streams = json.loads(result.stdout).get("streams", [])
    except Exception as e:
        log_error(f"❌ ffprobe failed for {os.path.basename(video_path)}: {e}")
        return

    if not streams:
        log_error(f"ℹ️ Geen ondertitels gevonden in: {os.path.basename(video_path)}")
        return

    base = os.path.splitext(os.path.basename(video_path))[0]
    _IMAGE_CODECS = {"hdmv_pgs_subtitle", "dvd_subtitle", "pgssub", "vobsub"}

    for local_idx, stream in enumerate(streams):
        codec = stream.get("codec_name", "")
        if codec in _IMAGE_CODECS:
            tb_update('tb_info', f"⏭️  Skipping image sub (codec={codec})", "normal")
            continue

        lang2 = stream.get("tags", {}).get("language", "und")[:2]
        lang3 = ISO6392_TO_ISO6393.get(lang2, lang2 if len(lang2) == 3 else "und")
        out_file = os.path.join(output_dir, f"{base}-{lang3}.srt")

        cmd_ext = [
            ffmpeg_path, "-y",
            "-i", video_path,
            "-map", f"0:s:{local_idx}",
            "-c:s", "srt",
            out_file
        ]
        try:
            r = subprocess.run(cmd_ext, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(out_file):
                tb_update('tb_info', f"✅ Extracted: {os.path.basename(out_file)}", "normal")
            else:
                log_error(f"⚠️ ffmpeg kon subtitle {local_idx} niet extraheren: {os.path.basename(video_path)}")
        except Exception as e:
            log_error(f"❌ Fout bij extractie: {e}")

@menu_tag(label="Extract Subs", group="videos")
def extract_subtitles():
    """Extract subtitles from selected video files (MKV via mkvextract, others via ffmpeg)"""
    from shared_data import get_shared
    from utils import log_error
    from utils.text_helpers import tb_update

    s = get_shared()

    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        log_error("⚠️ No files selected.")
        return

    video_files = [f for f in selected if os.path.splitext(f)[1].lower() in _VIDEO_EXTS]
    if not video_files:
        log_error("⚠️ No supported video files selected")
        return

    mkv_files     = [f for f in video_files if f.lower().endswith(".mkv")]
    non_mkv_files = [f for f in video_files if not f.lower().endswith(".mkv")]

    mkvextract_path = get_mkvextract_path() if mkv_files else None
    if mkv_files and not mkvextract_path:
        log_error("❌ mkvextract not found. Please:")
        log_error("   1. Install MKVToolNix, OR")
        log_error("   2. Set path in Settings/tools_cfg.json")
        mkv_files = []  # skip MKV files gracefully

    ffmpeg_path  = get_ffmpeg_path() if non_mkv_files else None
    ffprobe_path = shutil.which("ffprobe") or ""
    if non_mkv_files and not ffmpeg_path:
        log_error("❌ ffmpeg not found — cannot extract subs from non-MKV files.")
        non_mkv_files = []

    all_files = mkv_files + non_mkv_files
    if not all_files:
        return

    tb_update('tb_info', f"🎯 Extract Subs - {len(all_files)} file(s)", "normal")

    total = len(all_files)
    status_slot = getattr(s, 'bottomrow_label', None)
    if status_slot:
        status_slot.show_progress(mode="determinate")
        status_slot.update_progress(0, "0%")

    import threading

    def worker():
        s.batch_step_done = False
        for idx, video_file in enumerate(all_files):
            if idx > 0:
                s.app.after(0, lambda: tb_update('tb_info', "· " * 25, "normal"))
            output_dir = os.path.dirname(video_file)
            if video_file.lower().endswith(".mkv"):
                extract_subtitles_from_mkv(video_file, output_dir, mkvextract_path)
            else:
                extract_subtitles_ffmpeg(video_file, output_dir, ffmpeg_path, ffprobe_path)
            progress = float(idx + 1) / float(total)
            if status_slot:
                s.app.after(0, lambda p=progress: status_slot.update_progress(p))

        s.app.after(0, lambda: tb_update('tb_info', "· " * 25, "normal"))
        s.app.after(0, lambda: tb_update('tb_info', "✅ Extract Subs complete", "normal"))
        s.app.after(0, lambda: tb_update('tb_info', "─" * 50, "normal"))
        if status_slot:
            s.app.after(0, lambda: status_slot.reset())
        from utils.scan_helpers import reload
        s.app.after(0, lambda: reload(s.app))
        s.app.after(0, lambda: setattr(s, 'batch_step_done', True))

    threading.Thread(target=worker, daemon=True).start()

def extract_subtitles_from_mkv(mkv_file, output_dir, mkvextract_path):
    """Extract subtitles from a single MKV file"""
    from utils import log_error
    from utils.text_helpers import tb_update

    media_info_dll = get_mediainfo_library_path()
    if media_info_dll:
        info = MediaInfo.parse(mkv_file, library_file=media_info_dll)
    else:
        info = MediaInfo.parse(mkv_file)
    
    # Show which file we're processing
    tb_update('tb_info', f"📂 Processing: {os.path.basename(mkv_file)}", "normal")

    found_subtitle = False
    for track in info.tracks:
        if track.track_type == "Text":
            found_subtitle = True
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

    if not found_subtitle:
        log_error(f"ℹ️ Geen ondertitels gevonden in: {os.path.basename(mkv_file)}")

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