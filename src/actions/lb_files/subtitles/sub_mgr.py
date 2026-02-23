#-------------------------------------------------------------------------------
# Name:        actions_subtitles.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# popup_actions/actions_subtitles.py

import os
import re
import shutil
import subprocess
from decorators.decorators import menu_tag
from utils.text_helpers import tb_update
from tkinter import filedialog
from config.smart_config_manager import get_config_manager

def runCmd(cmd, description=""):
    """Execute a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode != 0 and result.stderr:
            print(f"⚠️ Command error ({description}): {result.stderr}")
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        print(f"❌ Command failed ({description}): {e}")
        return None

@menu_tag(label="Show SRT File", group="subtitles")
def show_srt_file():
    """Show the contents of selected SRT file in tb_info"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    
    if not selected:
        tb_update('tb_info', "⚠️ No file selected for this action.", "geel")
        print("⚠️ No files selected")
        return
    

    # Get first selected file
    file_path = selected[0]

    # Check if it's an SRT file
    if not file_path.lower().endswith(".srt"):
        tb_update('tb_info', f"⚠️ Error: You did not select an SRT file, but '{os.path.basename(file_path)}'. Please select a valid SRT file.", "geel")
        return

    # Controleer of er ook een video geselecteerd is (foutcombinatie)
    selected_videos = [f for f in s.app.lb_files.get_selected_file_paths() if f.lower().endswith((".mp4", ".mkv", ".avi"))]
    if selected_videos:
        tb_update('tb_info', "⚠️ Waarschuwing: Je hebt een SRT geselecteerd en een video-actie uitgevoerd. Dit is een onjuiste combinatie.", "geel")

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    # Clear tb_info textbox first, maar behoud zoekbalk
    if hasattr(s.app, "tb_info"):
        s.app.tb_info.clear_textbox(keep_search_controls=True)
        s.app.tb_info.show_status_on_empty = True

    filename = os.path.basename(file_path)
    tb_update('tb_info', f"━━━━━ {filename} ━━━━━", "normal")
    tb_update('tb_info', "", "normal")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into lines and add to textbox
        for line in content.split('\n'):
            tb_update('tb_info', line, "normal")

        tb_update('tb_info', "", "normal")
        tb_update('tb_info', f"━━━━━ End of {filename} ━━━━━", "normal")

        # Enable special character search
        enable_special_char_search(s.app.tb_info, content)

        print(f"📄 Displayed: {filename}")

    except Exception as e:
        from utils import log_error
        log_error(f"❌ Error reading SRT file: {e}")


def enable_special_char_search(tb_info, content):
    """Enable special character search with navigation buttons"""
    import customtkinter as ctk
    from shared_data import get_shared
    
    # Define special characters to search for (excluding < and > to avoid timestamp arrows)
    special_chars = ['♪', '♫', '■', '●', '♦', '◆', '★', '☆', '※', '►', '◄', 
                     '[', ']', '(', ')', '{', '}']
    
    # Get content directly from textbox instead of file
    textbox_content = tb_info.textbox.get("1.0", "end-1c")
    
    # Find all positions and line/column info of special characters
    matches = []
    for line_idx, line in enumerate(textbox_content.split('\n'), start=1):
        for col_idx, char in enumerate(line):
            if char in special_chars:
                matches.append({'line': line_idx, 'col': col_idx, 'char': char})
    
    if not matches:
        # Alleen melding tonen als expliciet gevraagd
        if getattr(tb_info, "show_status_on_empty", True):
            try:
                from shared_data import get_shared
                s = get_shared()
                if hasattr(s, 'bottomrow_label'):
                    s.bottomrow_label.show_message("No Special Chars Found", color="yellow")
            except Exception:
                pass
        return
    
    print(f"🔍 Found {len(matches)} special characters")
    
    # Store search state
    search_state = {'current_index': 0, 'matches': matches}
    
    # Create search control frame if it doesn't exist
    if not hasattr(tb_info, 'search_frame'):
        tb_info.search_frame = ctk.CTkFrame(tb_info, fg_color="gray20")
        tb_info.search_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        
        # Label
        tb_info.search_label = ctk.CTkLabel(
            tb_info.search_frame, 
            text=f"Special chars: {len(matches)} found",
            text_color="yellow"
        )
        tb_info.search_label.pack(side="left", padx=5)
        
        # Previous button
        tb_info.prev_btn = ctk.CTkButton(
            tb_info.search_frame,
            text="◄ Prev",
            width=60,
            command=lambda: navigate_special_char(tb_info, search_state, -1)
        )
        tb_info.prev_btn.pack(side="left", padx=2)
        
        # Next button
        tb_info.next_btn = ctk.CTkButton(
            tb_info.search_frame,
            text="Next ►",
            width=60,
            command=lambda: navigate_special_char(tb_info, search_state, 1)
        )
        tb_info.next_btn.pack(side="left", padx=2)
        
        # Position label
        tb_info.pos_label = ctk.CTkLabel(
            tb_info.search_frame,
            text="1/1",
            text_color="white"
        )
        tb_info.pos_label.pack(side="left", padx=5)
        
        # Close button
        tb_info.close_btn = ctk.CTkButton(
            tb_info.search_frame,
            text="✕",
            width=30,
            fg_color="gray30",
            hover_color="red",
            command=lambda: close_search_controls(tb_info)
        )
        tb_info.close_btn.pack(side="right", padx=2)
        
        # Store search state in tb_info
        tb_info.search_state = search_state
        
        # Highlight all special characters first
        highlight_all_special_chars(tb_info, search_state)
        
        # Then highlight and navigate to first match
        navigate_special_char(tb_info, search_state, 0)


def highlight_all_special_chars(tb_info, search_state):
    """Highlight all special characters in the textbox"""
    textbox = tb_info.textbox
    matches = search_state['matches']
    
    # Ensure textbox is in normal state for highlighting
    current_state = textbox.cget("state")
    textbox.configure(state="normal")
    
    # Remove any existing highlights first
    textbox.tag_remove("all_special_chars", "1.0", "end")
    
    # Configure tag for all special chars with bright colors
    textbox.tag_config("all_special_chars", background="#00FFFF", foreground="black", font=("Consolas", 10, "bold"))
    
    # Highlight each special character using line/col info
    for match in matches:
        line = match['line']
        col = match['col']
        pos = f"{line}.{col}"
        end_pos = f"{line}.{col + 1}"
        textbox.tag_add("all_special_chars", pos, end_pos)
    
    # Restore original state
    textbox.configure(state=current_state)
    
    print(f"✅ Highlighted {len(matches)} special characters")


def navigate_special_char(tb_info, search_state, direction):
    """Navigate to previous/next special character"""
    matches = search_state['matches']
    if not matches:
        return
    
    # Update current index
    if direction != 0:
        search_state['current_index'] = (search_state['current_index'] + direction) % len(matches)
    
    current_idx = search_state['current_index']
    match = matches[current_idx]
    line = match['line']
    col = match['col']
    char = match['char']
    
    # Update position label
    if hasattr(tb_info, 'pos_label'):
        tb_info.pos_label.configure(text=f"{current_idx + 1}/{len(matches)} ({char})")
    
    # Scroll to and highlight the character
    textbox = tb_info.textbox
    
    # Ensure textbox is in normal state for highlighting
    current_state = textbox.cget("state")
    textbox.configure(state="normal")
    
    # Remove previous current highlight
    textbox.tag_remove("special_char_current", "1.0", "end")
    
    # Add current highlight at position (on top of the cyan highlight)
    pos = f"{line}.{col}"
    end_pos = f"{line}.{col + 1}"
    textbox.tag_add("special_char_current", pos, end_pos)
    textbox.tag_config("special_char_current", background="#FFFF00", foreground="red", font=("Consolas", 12, "bold"))
    
    # Raise the current highlight tag so it's visible on top
    textbox.tag_raise("special_char_current")
    
    # Restore original state
    textbox.configure(state=current_state)
    
    # Scroll to position
    textbox.see(pos)
    
    # Show context (3 lines before and after)
    context_start = max(1, line - 3)
    textbox.see(f"{context_start}.0")
    
    print(f"📍 Navigated to: Line {line}, Col {col} → '{char}'")


def close_search_controls(tb_info):
    """Close and remove search controls"""
    if hasattr(tb_info, 'search_frame'):
        tb_info.search_frame.destroy()
        delattr(tb_info, 'search_frame')
    
    # Remove all highlights
    tb_info.textbox.tag_remove("all_special_chars", "1.0", "end")
    tb_info.textbox.tag_remove("special_char_current", "1.0", "end")
    
    # Clear the textbox
    if hasattr(tb_info, 'clear_textbox'):
        tb_info.clear_textbox()
    
    print("🔍 Search controls closed and textbox cleared")

def copy_original(file_path, orig_folder):
    if not os.path.exists(orig_folder):
        os.makedirs(orig_folder)
    shutil.copy(file_path, os.path.join(orig_folder, os.path.basename(file_path)))

def clean_subtitle(file_path):
    from popup_actions import Subtitle, Config  # Assuming these are still defined somewhere
    sub = Subtitle(file_path)
    cfg = Config()
    rules = cfg.select_rules(tags={'ocr', 'no-sdh', 'tidy', 'no-style'})  # Sample tags
    if sub.clean(rules):
        sub.save()
        print(f"✅ Cleaned: {file_path}")
    else:
        print(f"ℹ️ No cleanup needed: {file_path}")

def clean_directory(directory):
    orig_folder = os.path.join(directory, "orig")
    for filename in os.listdir(directory):
        if filename.endswith(".srt"):
            file_path = os.path.join(directory, filename)
            copy_original(file_path, orig_folder)
            clean_subtitle(file_path)

@menu_tag(label="Clean & Fix", group="subtitles")
def clean_and_fix_subtitles():
    """
    Heuristically clean selected SRT files by removing SDH, formatting,
    renumbering blocks, and skipping minimal/no-content lines.
    """
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    
    if not selected:
        print("⚠️ No files selected")
        return
    
    # Filter for .srt files
    srt_files = [f for f in selected if f.lower().endswith(".srt")]
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi'))]

    if video_files:
        tb_update('tb_info', f"⚠️ Error: You selected a video for an SRT action: {', '.join([os.path.basename(v) for v in video_files])}. Please select only SRT files.", "geel")

    if not srt_files:
        tb_update('tb_info', "⚠️ No file selected for this action.", "geel")
        print("⚠️ No SRT files selected")
        return

    tb_update('tb_info', f"🧹 Clean & Fix - {len(srt_files)} file(s)", "normal")

    for idx, file_path in enumerate(srt_files):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        clean_single_subtitle(file_path)

    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ Clean & Fix complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")
    
    # Refresh the listbox to show cleaned files (NOK_ prefix removed/added)
    from utils.scan_helpers import reload
    reload(s.app)


def clean_single_subtitle(file_path):
    """Clean a single SRT file"""
    import unicodedata
    
    orig_path = file_path
    directory, filename = os.path.split(file_path)

    renamed = os.path.join(directory, f"NOK_{filename}")
    if os.path.exists(renamed):
        tb_update('tb_info', f"⚠️ Skipped: NOK file already exists for {filename}", "geel")
        return
    os.rename(file_path, renamed)

    tb_update('tb_info', f"📝 Cleaning: {filename}", "normal")

    try:
        with open(renamed, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cleaned_lines = []
        block = []
        count = 1

        for line in lines:
            if line.strip():
                block.append(line.strip())
            else:
                if block:
                    if re.match(r'^\d+$', block[0]):
                        block = block[1:]

                    # Remove SDH markers and HTML tags
                    cleaned = [re.sub(r'\[.*?\]|\(.*?\)|♪.*?♪|<[^>]+>', '', l) for l in block]
                    
                    # Remove accents and diacritics (café → cafe, één → een, naïef → naief)
                    cleaned = [remove_accents(l) for l in cleaned]
                    
                    # Normalize typographic characters
                    cleaned = [normalize_typography(l) for l in cleaned]
                    
                    # Remove empty lines and single dashes
                    cleaned = [l for l in cleaned if l.strip() and l.strip() != '-']

                    if len(cleaned) > 1:
                        cleaned_lines.append(str(count))
                        count += 1
                        cleaned_lines.extend(cleaned)
                        cleaned_lines.append("")

                block = []

        with open(orig_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cleaned_lines))

        tb_update('tb_info', f"✅ Saved: {filename}", "normal")

    except Exception as e:
        from utils import log_error
        log_error(f"   ❌ Error cleaning {filename}: {e}")


def remove_accents(text):
    """Remove accents and diacritics from text (café → cafe, één → een)"""
    import unicodedata
    
    # Normalize to NFD (decompose characters into base + diacritic)
    nfd = unicodedata.normalize('NFD', text)
    
    # Filter out combining diacritical marks
    without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    # Normalize back to NFC (composed form)
    return unicodedata.normalize('NFC', without_accents)


def normalize_typography(text):
    """Normalize typographic characters to basic ASCII"""
    replacements = {
        # Quotes
        '"': '"', '"': '"', ''': "'", ''': "'", '„': '"', '‟': '"',
        # Dashes
        '—': '-', '–': '-', '‐': '-', '‑': '-',
        # Ellipsis
        '…': '...',
        # Other common typographic characters
        '•': '*', '·': '*', '×': 'x', '÷': '/',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def subs_rename():
    # ⚠️ TODO: This function needs refactoring - uses undefined variables
    print("⚠️ Rename subs: Not yet implemented")
    return
    
    # OLD CODE - NEEDS FIXING:
    language = get_config_manager().get("persistent_cfg", "Language", "eng")
    # rename all srt files to .language.srt
    if messagebox.askyesno(title="RENAME ALL SUBS", message="Are You Sure to rename to ."+ language + ".srt"):
        # rename subs
        for fil in files_list:
            #if fil.endswith(".srt") and not fil.endswith("*.dut.srt"):
                #os.rename(fil, os.path.splitext(fil)[0] + ".dut.srt")

            if fil.endswith(".srt"):
                # detect language
                l = lang_detect(fil)
                ll="." + l[1]
                print(ll, fil)
                if not fil.endswith(l[1]+".srt"):
                    # rename with language code3
                    pos = len(fil)-4
                    print(len(fil),pos)
                    oo = insert_str(fil,ll,pos)
                    #oo = add_char_at_positions(fil,l[1],4)
                    #oo = insert_str(fil,"."+l[1],3)
                    print("oo = " + oo)
                    os.rename(fil, oo)

@menu_tag(label="Sync Srt", group="subtitles")
def sub_sync():
    """Synchronize subtitle with video"""
    from shared_data import get_shared
    s = get_shared()

    # Get selected files
    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    print(f"DEBUG: Selected files: {[os.path.basename(f) for f in selected]}")  # Debug info
    
    # Filter for SRT and video files
    srt_files = [f for f in selected if f.lower().endswith('.srt')]
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm'))]
    
    print(f"DEBUG: Found SRT files: {[os.path.basename(f) for f in srt_files]}")  # Debug info
    print(f"DEBUG: Found video files: {[os.path.basename(f) for f in video_files]}")  # Debug info
    
    if not srt_files:
        tb_update('tb_info', "⚠️ No SRT subtitle file selected for synchronization.", "geel")
        return
    
    if not video_files:
        tb_update('tb_info', "⚠️ No video file selected for synchronization.", "geel")
        return
    
    if len(srt_files) > 1:
        tb_update('tb_info', "⚠️ Please select only one SRT file for synchronization.", "geel")
        return
    
    if len(video_files) > 1:
        tb_update('tb_info', "⚠️ Please select only one video file for synchronization.", "geel")
        return
    
    srt_file = srt_files[0]
    video_file = video_files[0]
    
    # Parse the SRT file path
    from utils.shared_utils import fils
    srt_info = fils(srt_file)
    srt_dir = srt_info.f_path
    srt_base = srt_info.f_name
    
    # Create output filename
    synchronized_srt = os.path.join(srt_dir, f"{srt_base}.sync.srt")
    
    import threading

    def worker():
        status_slot = getattr(s, 'bottomrow_label', None)
        # show indeterminate progress for single-file sync
        if status_slot:
            s.app.after(0, lambda: status_slot.show_progress(mode="indeterminate"))

        try:
            s.app.after(0, lambda: tb_update('tb_info', f"🔄 Synchronizing {os.path.basename(srt_file)} with {os.path.basename(video_file)}...", "normal"))
            import subprocess
            cmd = [
                "ffsubsync",
                video_file,
                "-i", srt_file,
                "-o", synchronized_srt
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                s.app.after(0, lambda: tb_update('tb_info', f"✅ Synchronization completed: {os.path.basename(synchronized_srt)}", "groen"))
                from utils.scan_helpers import reload
                s.app.after(0, lambda: reload(s.app))
            else:
                s.app.after(0, lambda: tb_update('tb_info', f"❌ Synchronization failed: {result.stderr}", "rood"))

        except FileNotFoundError:
            s.app.after(0, lambda: tb_update('tb_info', "❌ ffsubsync not found. Please install it: pip install ffsubsync", "rood"))
        except Exception as e:
            s.app.after(0, lambda: tb_update('tb_info', f"❌ Synchronization failed: {str(e)}", "rood"))
            import traceback
            traceback.print_exc()
        finally:
            if status_slot:
                s.app.after(0, lambda: status_slot.reset())

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def sub_test(fil):
    # ⚠️ TODO: This function needs refactoring - uses undefined variables
    print("⚠️ Test sub: Not yet implemented")
    return
    
    # OLD CODE - NEEDS FIXING:
    # Sometimes a video contains multiple subtitle tracks.
    # To find out which one to extract, use ffprobe.
    strCmd = "ffprobe -loglevel error -select_streams s -show_entries stream=index:stream_tags=language -of csv=p=0" + fil

    proc = runCmd(strCmd,"sub_extract")
    print(proc)

    # extraxt all subs from mkv

    #strCmd = "ffmpeg -y -v error -stats -i " + fil + " -vn -an -dn -map 0:%%x "%%~ni."%%x".srt"



    # ffs reference.mkv -i 1.srt 2.srt 3.srt --overwrite-input
    return

def sub_extract(fil, add_sync_suffix=False):
    # ffmpeg -i Movie.mkv -map 0:s:0 subs.srt
    # Extract subtitle from video file with language code
    
    # Skip if not a video file
    if not fil.lower().endswith(('.mkv', '.mp4', '.avi', '.mov', '.m4v')):
        return
    
    lang = get_config_manager().get("persistent_cfg", "Language", "eng")
    
    # Generate output filename
    base, ext = os.path.splitext(fil)
    
    # Always add .sync suffix when resyncing
    if add_sync_suffix:
        output_file = f"{base}.{lang}.sync.srt"
        print(f"🔄 Re-extracting subtitle (sync) from: {os.path.basename(fil)}")
    else:
        output_file = f"{base}.{lang}.srt"
        print(f"📹 Extracting subtitle from: {os.path.basename(fil)}")
    
    print(f"💾 Output: {os.path.basename(output_file)}")
    
    # Check if this specific output already exists
    if os.path.exists(output_file):
        print(f"⚠️ Subtitle already exists: {os.path.basename(output_file)}")
        tb_update('tb_info', f"⚠️ Already exists: {os.path.basename(output_file)}", "geel")
        return
    
    strCmd = f'ffmpeg -loglevel panic -i "{fil}" -map 0:s:0 "{output_file}"'
    proc = runCmd(strCmd, "sub_extract")
    
    # Check if the file was created successfully
    if os.path.exists(output_file):
        print(f"✅ Extracted: {os.path.basename(output_file)}")
        tb_update('tb_info', f"✅ Created: {os.path.basename(output_file)}", "groen")
    else:
        print(f"⚠️ No subtitle found in {os.path.basename(fil)}")
        tb_update('tb_info', f"⚠️ No subtitle in {os.path.basename(fil)}", "geel")

def sub_all_extract(fil):
    # check if video has subtitles
    strCmd = "ffmpeg -i " + fil + " -c copy -map 0:s:0 -frames:s 1 -f null - -v 0 -hide_banner"
    subs = runCmd(strCmd,"check if subs")
    if subs:
        subnum = get_num_subs()
        print(subnum)
        for sub in range(subnum):

            proc = runCmd(strCmd,"sub_all_extract")
            print(proc)





def get_num_subs(fil):
    out = subprocess.run(['ffprobe','-loglevel','error','-select_streams','s','-show_entries','stream=index:stream_tags=language','-of','csv=p=0', fil],\
             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    subs=out.stdout
    subs_list = subs.split("\n")

    last_sub = subs_list.pop(-2)
    subnum = last_sub.split(",").pop(0)
    return subnum, subs_list

@menu_tag(label="Resync Folder")
def subs_resync():
    from shared_data import get_shared
    from utils import log_error
    import threading

    s = get_shared()

    # Get the active entry (source, target, or backup)
    last_entry_name = getattr(s, "last_entry_name", "source")

    if last_entry_name not in s.entry_data:
        log_error(f"⚠️ Entry '{last_entry_name}' not found")
        tb_update('tb_info', f"⚠️ Entry '{last_entry_name}' not found", "rood")
        return

    # Get the path from the active SmartEntry
    entry_obj = s.entry_data[last_entry_name]["entry"]
    input_dir = entry_obj.value

    if not input_dir:
        log_error("⚠️ No folder path set in active entry")
        tb_update('tb_info', "⚠️ No folder path set in active entry", "geel")
        return

    if not os.path.exists(input_dir):
        log_error(f"⚠️ Folder does not exist: {input_dir}")
        tb_update('tb_info', f"⚠️ Folder does not exist: {input_dir}", "rood")
        return

    tb_update('tb_info', f"🔄 Extracting subtitles from: {input_dir}", "groen")

    # Process only video files in the directory (not recursive)
    video_extensions = ('.mkv', '.mp4', '.avi', '.mov', '.m4v')
    video_files = [f for f in os.listdir(input_dir)
                   if os.path.isfile(os.path.join(input_dir, f))
                   and f.lower().endswith(video_extensions)]

    if not video_files:
        tb_update('tb_info', f"⚠️ No video files found in: {input_dir}", "geel")
        return

    total = len(video_files)

    def worker():
        # show determinate progress
        status_slot = getattr(s, 'bottomrow_label', None)
        if status_slot:
            s.app.after(0, lambda: status_slot.show_progress(mode="determinate"))

        for idx, file in enumerate(video_files):
            fil = os.path.join(input_dir, file)
            # update info textbox on main thread
            s.app.after(0, lambda f=file: tb_update('tb_info', f"Processing: {f}", "normal"))

            # perform extraction (runs blocking, but in worker thread)
            try:
                sub_extract(fil, add_sync_suffix=True)
            except Exception as e:
                s.app.after(0, lambda e=e, fn=file: tb_update('tb_info', f"❌ Error processing {fn}: {e}", "rood"))

            # update progress
            progress = float(idx + 1) / float(total)
            if status_slot:
                s.app.after(0, lambda p=progress: status_slot.update_progress(p))

        # finalize
        if status_slot:
            s.app.after(0, lambda: status_slot.reset())
        s.app.after(0, lambda: tb_update('tb_info', f"✅ Resync completed for folder: {input_dir}", "groen"))
        # Refresh the listbox to show newly extracted subtitle files
        from utils.scan_helpers import reload
        s.app.after(0, lambda: reload(s.app))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


# === SUB LANGUAGE RELATED =====================================================
@menu_tag(label="Check SRT Language")
def check_language():
    """Check language of selected .srt subtitle files"""
    from shared_data import get_shared
    from utils import log_error
    
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No file selected for this action.", "geel")
        log_error("⚠️ No files selected.")
        return

    srt_files = [f for f in selected if f.endswith(".srt")]
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi'))]

    if video_files:
        from utils import update_tbinfo
        update_tbinfo(f"⚠️ Error: You selected a video for an SRT action: {', '.join([os.path.basename(v) for v in video_files])}. Please select only SRT files.", "geel")

    if not srt_files:
        log_error("⚠️ No .srt files selected")
        return

    print(f"\n🔍 Checking language for {len(srt_files)} file(s):\n")

    for fil in srt_files:
        filename = os.path.basename(fil)
        print(f"📄 {filename}")

        lng = lang_detect(fil)
        short2, short3, naam, prob, line = lng

        # Format: 2-letter  3-letter  name  probability  sample_text
        msg = f"   🌐 {short2} | {short3} | {naam} | {prob:.2%} confidence"
        print(msg)

        from utils import update_tbinfo
        update_tbinfo(f"📄 {filename}", "normal")
        update_tbinfo(msg, "normal")
        update_tbinfo("─" * 50, "normal")

    print("\n✅ Language detection completed")


def random_line(fil):
    import random
    lines = open(fil).read().splitlines()
    line =random.choice(lines)
    return line

def lang_detect(fil):
    # Try to import detection libraries; if missing, notify user and return fallback
    try:
        from langdetect import detect_langs
        from langcodes import Language
    except Exception as e:
        # Notify via StatusSlot and tb_info, but don't crash the UI
        try:
            from shared_data import get_shared
            s = get_shared()
            if hasattr(s, 'bottomrow_label'):
                s.bottomrow_label.show_message("Missing package 'langdetect' or 'langcodes'", color="red")
        except Exception:
            pass
        try:
            from utils import update_tbinfo
            update_tbinfo("⚠️ Missing dependency: install 'langdetect' and 'langcodes' (pip install langdetect langcodes)", "geel")
        except Exception:
            pass
        return "xx", "xxx", "No Language", 0.0, "Missing dependency"
    import re

    # Read all lines and collect text lines (skip numbers, timecodes, empty lines)
    try:
        with open(fil, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        # Try with different encoding
        try:
            with open(fil, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except:
            return "xx", "xxx", "No Language", 0.0, "Could not read file"
    
    # Filter for actual subtitle text (not numbers, not timecodes, not empty)
    text_lines = []
    timecode_pattern = r'^\d{2}:\d{2}:\d{2}'
    
    for line in lines:
        line = line.strip()
        # Skip completely empty lines
        if not line:
            continue
        # Skip lines that are only digits (sequence numbers)
        if line.isdigit():
            continue
        # Skip timecode lines (contain -->)
        if '-->' in line:
            continue
        # Skip pure timecode lines (but allow text that might look like timecodes)
        if re.match(timecode_pattern, line) and len(line) <= 8:  # Only skip if it's just a timecode
            continue
        # Include all other lines as potential subtitle text
        text_lines.append(line)
    
    print(f"🔍 Found {len(text_lines)} text lines")
    if text_lines:
        print(f"   First few lines: {text_lines[:3]}")
    
    if not text_lines:
        return "xx", "xxx", "No Language", 0.0, "No text found"
    
    # Combine multiple text lines for better detection
    # Use more lines for better detection, but limit to reasonable length
    sample_text = ' '.join(text_lines[:50])  # Use first 50 text lines instead of 10
    
    # Clean the text - remove HTML tags and extra whitespace
    import re
    sample_text = re.sub(r'<[^>]+>', '', sample_text)  # Remove HTML tags
    sample_text = re.sub(r'\s+', ' ', sample_text).strip()  # Normalize whitespace
    
    print(f"🔍 Sample text length: {len(sample_text)} chars")
    
    if text_lines:
        print(f"   Sample text preview: '{sample_text[:200]}...'")
    
    # Minimum text length for detection
    if len(sample_text) < 50:
        return "xx", "xxx", "No Language", 0.0, "Text too short for detection"
    
    # detect language
    try:
        langs = detect_langs(sample_text)
        print(f"🔍 Detected languages: {langs}")
        print(f"🔍 Number of detected languages: {len(langs) if langs else 0}")
        
        if not langs:
            print("❌ No languages detected at all")
            return "xx", "xxx", "No Language", 0.0, "No languages detected"
        
        # Get the most confident detection
        best_lang = langs[0]
        print(f"🔍 Best language: {best_lang.lang} with probability {best_lang.prob}")
        
        # Special handling for Dutch vs Afrikaans
        # langdetect often confuses Dutch with Afrikaans, so prefer Dutch if detected
        dutch_detection = next((lang for lang in langs if lang.lang == 'nl'), None)
        if dutch_detection:
            print(f"🔍 Found Dutch detection: {dutch_detection.prob}, using it instead of {best_lang.lang}:{best_lang.prob}")
            best_lang = dutch_detection
        
        short2 = best_lang.lang
        try:
            short3 = Language.get(short2).to_alpha3(variant='B')
            naam = Language.get(short2).display_name()
        except Exception as lang_error:
            print(f"❌ Error getting language info for {short2}: {lang_error}")
            short3 = short2.upper()  # Fallback
            naam = short2.upper()    # Fallback
        print(f"✅ Returning: {short2}, {short3}, {naam}, {best_lang.prob}")
        return short2, short3, naam, best_lang.prob, text_lines[0] if text_lines else ""
    except Exception as e:
        print(f"❌ Exception in lang_detect: {e}")
        import traceback
        traceback.print_exc()
        return "xx", "xxx", "No Language", 0.0, f"Detection error: {str(e)}"
    
    # Fallback if no language detected
    return "xx", "xxx", "No Language", 0.0, "No detection result"

@menu_tag(label="Translate", group="subtitles")
def sub_translate():
    """Translate subtitle file"""
    from shared_data import get_shared
    from config.smart_config_manager import get_config_manager
    from utils.shared_utils import fils
    from utils import tb_update
    import os
    
    s = get_shared()
    
    # Close any open menus immediately
    s.app.update_idletasks()
    s.app.update()

    # Get selected files
    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    
    # Controleer of er een video geselecteerd is
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
    if video_files:
           tb_update('tb_info', f"⚠️ Error: You selected a video for an SRT action: {', '.join([os.path.basename(v) for v in video_files])}. Please select only SRT files.", "geel")
           return

    if not selected:
           tb_update('tb_info', "⚠️ No file selected for this action.", "geel")
           return
    
    # Filter for SRT files only
    srt_files = [f for f in selected if f.lower().endswith('.srt')]
    if not srt_files:
        tb_update('tb_info', "⚠️ No SRT files selected for translation.", "geel")
        return
    
    # Get target language from config
    try:
        config_mgr = get_config_manager()
        target_lang = config_mgr.get["Language"]  # e.g., "nl", "en", etc.
        if not target_lang:
            target_lang = "nl"  # default to Dutch
    except:
        target_lang = "nl"  # fallback
    
    # Import translation modules once
    try:
        import argostranslate.translate
        import argostranslate.package
        from .translate_srt_argos import load_translation_model, translate_srt
    except ImportError as e:
        tb_update('tb_info', f"❌ Translation failed: Missing argostranslate. Install with: pip install argostranslate", "rood")
        return
    
    # Process all selected SRT files
    translated_count = 0
    failed_count = 0
    status_slot = s.bottomrow_label
    
    for idx, fil in enumerate(srt_files, 1):
        try:
            # Parse the input file
            file_info = fils(fil)
            input_dir = file_info.f_path
            base_name = file_info.f_name
            
            # Create output filename with target language
            output_file = os.path.join(input_dir, f"{base_name}.{target_lang}.srt")
            
            # Detect source language from the file
            detected = lang_detect(fil)
            source_lang = detected[0]  # Get detected language code
            if source_lang == "xx":  # No language detected
                source_lang = "en"  # Default to English
            
            # Skip if source and target are the same
            if source_lang == target_lang:
                tb_update('tb_info', f"⚠️ {os.path.basename(fil)}: Source and target languages are the same ({source_lang}), skipping...", "geel")
                continue
            
            # Load translation model (will auto-download if needed)
            tb_update('tb_info', f"🔄 [{idx}/{len(srt_files)}] Preparing {source_lang}→{target_lang} translation for {os.path.basename(fil)}...", "normal")
            s.app.update_idletasks()
            
            translation = load_translation_model(from_code=source_lang, to_code=target_lang)
            
            # Show translating message and progress bar
            tb_update('tb_info', f"🔄 [{idx}/{len(srt_files)}] Translating {os.path.basename(fil)} ({source_lang}→{target_lang})...", "normal")
            status_slot.show_progress(mode="determinate")
            
            # Define progress callback
            def update_progress(current, total):
                progress = current / total
                status_slot.update_progress(progress, f"{current}/{total}")
                # Force GUI update to show progress in real-time
                s.app.update_idletasks()
            
            # Perform translation with progress updates
            translate_srt(fil, output_file, translation, progress_callback=update_progress)
            
            translated_count += 1
            
        except Exception as e:
            failed_count += 1
            tb_update('tb_info', f"❌ Failed to translate {os.path.basename(fil)}: {str(e)}", "rood")
            import traceback
            traceback.print_exc()
    
    # Reset progress bar and show final summary
    status_slot.reset()
    if failed_count == 0:
        tb_update('tb_info', f"✅ Translation completed: {translated_count} file(s) translated successfully", "groen")
    else:
        tb_update('tb_info', f"⚠️ Translation completed: {translated_count} succeeded, {failed_count} failed", "oranje")
    
    # Refresh the listbox to show newly translated files
    from utils.scan_helpers import reload
    reload(s.app)
