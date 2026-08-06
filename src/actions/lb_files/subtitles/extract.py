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
from pathlib import Path
from tqdm import tqdm
from pymediainfo import MediaInfo
from concurrent.futures import ThreadPoolExecutor
from langdetect import detect_langs
from decorators.decorators import menu_tag


def _no_console_subprocess_kwargs():
    """Hide console windows for CLI tools when the app runs without a console."""
    if os.name != 'nt':
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        'startupinfo': startupinfo,
        'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    }

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

LANG_NAME_TO_ISO6393 = {
    "arabic": "ara",
    "bulgarian": "bul",
    "chinese": "zho",
    "czech": "ces",
    "danish": "dan",
    "dutch": "nld",
    "english": "eng",
    "estonian": "est",
    "finnish": "fin",
    "french": "fra",
    "german": "deu",
    "greek": "ell",
    "hebrew": "heb",
    "hindi": "hin",
    "hungarian": "hun",
    "indonesian": "ind",
    "italian": "ita",
    "japanese": "jpn",
    "korean": "kor",
    "latvian": "lav",
    "lithuanian": "lit",
    "malay": "msa",
    "nederlands": "nld",
    "norwegian": "nor",
    "polish": "pol",
    "portuguese": "por",
    "russian": "rus",
    "slovak": "slk",
    "slovenian": "slv",
    "spanish": "spa",
    "swedish": "swe",
    "tamil": "tam",
    "telugu": "tel",
    "thai": "tha",
    "turkish": "tur",
    "ukrainian": "ukr",
    "vietnamese": "vie",
}

LEGACY_ONE_LETTER_TO_ISO6393 = {
    # Some files contain truncated tags such as "d" instead of "dut".
    "d": "nld",
    "e": "eng",
    "f": "fra",
    "g": "deu",
    "n": "nld",
    "s": "spa",
}

PREFERRED_SUBTITLE_LANGS = {"en", "nl", "fr", "es"}
PREFERRED_SUBTITLE_LANGS_6393 = {"eng", "nld", "fra", "spa"}


def normalize_track_language_to_iso6393(language):
    """Normalize MediaInfo language values to ISO639-3 code."""
    if not language:
        return "und"

    value = str(language).strip().lower()
    if not value:
        return "und"

    # Handle malformed 1-letter tags from older mux outputs.
    if len(value) == 1:
        return LEGACY_ONE_LETTER_TO_ISO6393.get(value, "und")

    # Common 2-letter ISO639-1
    if len(value) == 2:
        return ISO6392_TO_ISO6393.get(value, "und")

    # Already an ISO639-3 code
    if len(value) == 3 and value in ISO6392_TO_ISO6393.values():
        return value

    # Human-readable names
    if value in LANG_NAME_TO_ISO6393:
        return LANG_NAME_TO_ISO6393[value]

    # Some tags include region/script variants like "en-US"
    base = re.split(r"[-_\s]", value)[0]
    if base != value:
        return normalize_track_language_to_iso6393(base)

    return "und"


def _read_subtitle_sample_text(file_path, max_lines=50):
    """Read a small text sample from an extracted subtitle file."""
    lines = None
    for encoding in ["utf-8-sig", "utf-8", "utf-16", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            break
        except Exception:
            continue

    if lines is None:
        return ""

    text_lines = []
    timecode_pattern = r'^\d{2}:\d{2}:\d{2}'

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if '-->' in line:
            continue
        if re.match(timecode_pattern, line) and len(line) <= 8:
            continue
        text_lines.append(line)

    sample_text = ' '.join(text_lines[:max_lines])
    sample_text = re.sub(r'<[^>]+>', '', sample_text)
    sample_text = re.sub(r'\s+', ' ', sample_text).strip()
    return sample_text


def detect_preferred_subtitle_language_from_text(sample_text):
    """Detect a preferred subtitle language from subtitle text content."""
    if len(sample_text) < 50:
        return "und"

    try:
        langs = detect_langs(sample_text)
    except Exception:
        return "und"

    if not langs:
        return "und"

    best_lang = langs[0]
    dutch_detection = next((lang for lang in langs if lang.lang == "nl"), None)
    if dutch_detection:
        best_lang = dutch_detection

    if best_lang.lang not in PREFERRED_SUBTITLE_LANGS:
        return "und"

    return normalize_track_language_to_iso6393(best_lang.lang)


def detect_preferred_subtitle_language(file_path):
    """Detect a subtitle language when the track metadata says 'und'."""
    sample_text = _read_subtitle_sample_text(file_path)
    return detect_preferred_subtitle_language_from_text(sample_text)


def get_selected_extract_languages():
    """Read the persistent selection of subtitle languages to keep."""
    try:
        from config.smart_config_manager import get_config_manager

        cfg_mgr = get_config_manager()
        selected = cfg_mgr.get("persistent_cfg", "Extract_Languages", ["eng", "nld", "fra", "spa"])
    except Exception:
        selected = ["eng", "nld", "fra", "spa"]

    if isinstance(selected, str):
        selected = [item.strip() for item in selected.split(",") if item.strip()]

    normalized = set()
    for value in selected or []:
        normalized_value = normalize_track_language_to_iso6393(value)
        if normalized_value in PREFERRED_SUBTITLE_LANGS_6393:
            normalized.add(normalized_value)

    return normalized or set(PREFERRED_SUBTITLE_LANGS_6393)


def should_keep_subtitle_language(lang_short3, seen_languages, allowed_languages):
    """Keep only the first subtitle track for preferred languages."""
    if lang_short3 not in allowed_languages:
        return False

    if lang_short3 in seen_languages:
        return False

    seen_languages.add(lang_short3)
    return True


def unique_output_path(path):
    """Return a non-conflicting output path by appending -2, -3, ... when needed."""
    if not os.path.exists(path):
        return path

    root, ext = os.path.splitext(path)
    index = 2
    while True:
        candidate = f"{root}-{index}{ext}"
        if not os.path.exists(candidate):
            return candidate
        index += 1


def _resolve_tools_cfg_path():
    """Find tools_cfg.json regardless of whether app starts from repo root or src."""
    candidates = [
        Path.cwd() / "Settings" / "tools_cfg.json",
        Path.cwd() / "src" / "Settings" / "tools_cfg.json",
        Path(__file__).resolve().parents[3] / "Settings" / "tools_cfg.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None

def get_mkvextract_path():
    """Get mkvextract executable path from config or PATH"""
    import json
    
    # First check if it's in PATH
    if shutil.which("mkvextract"):
        return "mkvextract"
    
    # Check config file for custom path
    try:
        config_path = _resolve_tools_cfg_path()
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
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

    def _flush_ui():
        if hasattr(s, 'app') and s.app is not None:
            try:
                s.app.update_idletasks()
                s.app.update()
            except Exception:
                pass
    
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
    _flush_ui()
    
    # Update progress bar
    if hasattr(s.app, 'progress_bar'):
        s.app.progress_bar.set(0)
        _flush_ui()

    total_tracks = 0
    for mkv_file in mkv_files:
        try:
            info = MediaInfo.parse(mkv_file)
            total_tracks += sum(1 for track in info.tracks if track.track_type == "Text")
        except Exception as e:
            log_error(f"⚠️ Could not inspect subtitle tracks for {os.path.basename(mkv_file)}: {e}")

    if hasattr(s.app, 'progress_bar') and total_tracks == 0:
        s.app.progress_bar.set(1)
        _flush_ui()
        tb_update('tb_info', "⚠️ Geen subs gevonden", "normal")
        _flush_ui()
        return

    processed_tracks = 0

    def update_progress_bar():
        if hasattr(s.app, 'progress_bar') and total_tracks > 0:
            progress = min(processed_tracks / total_tracks, 1)
            s.app.progress_bar.set(progress)
            _flush_ui()

    def on_track_processed():
        nonlocal processed_tracks
        processed_tracks += 1
        update_progress_bar()
    
    for idx, mkv_file in enumerate(mkv_files):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
            _flush_ui()
        output_dir = os.path.dirname(mkv_file)  # Same directory as video
        extract_subtitles_from_mkv(
            mkv_file,
            output_dir,
            mkvextract_path,
            on_track_processed=on_track_processed,
            flush_ui=_flush_ui,
        )
    
    tb_update('tb_info', "· " * 25, "normal")
    _flush_ui()
    tb_update('tb_info', "✅ Extract Subs complete", "normal")
    _flush_ui()
    tb_update('tb_info', "─" * 50, "normal")
    _flush_ui()
    
    # Refresh the listbox to show extracted subtitle files
    from utils.scan_helpers import reload
    reload(s.app)

def extract_subtitles_from_mkv(mkv_file, output_dir, mkvextract_path, on_track_processed=None, flush_ui=None):
    """Extract subtitles from a single MKV file and return processed subtitle track count."""
    from utils import log_error
    from utils.text_helpers import tb_update
    
    info = MediaInfo.parse(mkv_file)
    seen_languages = set()
    allowed_languages = get_selected_extract_languages()
    processed_tracks = 0
    
    # Show which file we're processing
    tb_update('tb_info', f"📂 {os.path.basename(mkv_file)}", "normal")
    if flush_ui:
        flush_ui()

    for track in info.tracks:
        if track.track_type == "Text":
            lang_short3 = normalize_track_language_to_iso6393(track.language)
            if lang_short3 == "und":
                log_error(f"⚠️ Unknown language: {track.language} (using 'und')")
                if flush_ui:
                    flush_ui()

            track_id = track.track_id - 1
            base = os.path.splitext(os.path.basename(mkv_file))[0]
            preferred_out_file = os.path.join(output_dir, f"{base}-{lang_short3}.srt")
            out_file = unique_output_path(preferred_out_file)

            if out_file != preferred_out_file:
                tb_update('tb_info', f"ℹ️ Dup -> {os.path.basename(out_file)}", "normal")
                if flush_ui:
                    flush_ui()

            try:
                with open(os.devnull, 'w') as devnull:
                    subprocess.run([mkvextract_path, "tracks", mkv_file,
                                    f"{track_id}:{out_file}"],
                                   check=True, stdout=devnull, stderr=devnull,
                                   **_no_console_subprocess_kwargs())

                final_out_file = out_file
                final_lang_short3 = lang_short3
                if lang_short3 == "und":
                    final_lang_short3 = detect_preferred_subtitle_language(out_file)

                if final_lang_short3 == "und":
                    tb_update('tb_info', f"⏭️ Skip und: {os.path.basename(out_file)}", "geel")
                    if flush_ui:
                        flush_ui()
                    os.remove(out_file)
                    continue

                tb_update('tb_info', f"🌐 {final_lang_short3}", "normal")
                if flush_ui:
                    flush_ui()

                if not should_keep_subtitle_language(final_lang_short3, seen_languages, allowed_languages):
                    tb_update(
                        'tb_info',
                        f"⏭️ Skip uit: {os.path.basename(out_file)} ({final_lang_short3})",
                        "geel"
                    )
                    if flush_ui:
                        flush_ui()
                    os.remove(out_file)
                    continue

                if final_lang_short3 != lang_short3:
                    detected_out_file = unique_output_path(
                        os.path.join(output_dir, f"{base}-{final_lang_short3}.srt")
                    )
                    if detected_out_file != out_file:
                        os.replace(out_file, detected_out_file)
                        final_out_file = detected_out_file

                tb_update('tb_info', f"✅ {os.path.basename(final_out_file)}", "normal")
                if flush_ui:
                    flush_ui()
            except subprocess.CalledProcessError as e:
                error_msg = f"⚠️ Failed to extract track {track_id}: {e}"
                log_error(error_msg)
                if flush_ui:
                    flush_ui()
            finally:
                if on_track_processed:
                    on_track_processed()

    return processed_tracks

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
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, **_no_console_subprocess_kwargs())
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