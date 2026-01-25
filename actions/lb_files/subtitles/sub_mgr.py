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
from decorators.decorators import menu_tag
from utils.text_helpers import tb_update

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

    tb_update('tb_info', f"🧹 Cleaning {len(srt_files)} subtitle file(s)...", "normal")

    for file_path in srt_files:
        clean_single_subtitle(file_path)

    tb_update('tb_info', "✅ Subtitle cleaning completed", "normal")


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

    tb_update('tb_info', f"   📝 Cleaning: {filename}", "normal")

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

        tb_update('tb_info', f"   ✅ Saved: {filename}", "normal")

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
    language = get_config_manager().get["Language"]
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

@menu_tag(label="Translate", group="subtitles")
def sub_translate(fil):
    """Translate subtitle file"""
    from shared_data import get_shared
    s = get_shared()

    # Controleer of er een video geselecteerd is
    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
    if video_files:
           tb_update('tb_info', f"⚠️ Error: You selected a video for an SRT action: {', '.join([os.path.basename(v) for v in video_files])}. Please select only SRT files.", "geel")

    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    if not selected:
           tb_update('tb_info', "⚠️ No file selected for this action.", "geel")
    tb_update('tb_info', "⚠️ Translate: Feature needs configuration", "normal")
    print("⚠️ This function needs: fils, get_config_manager, transsubs module")
    print("⚠️ Please implement these dependencies first")
    return
    file = fils(fil)
    trgt = file.f_parent
    lang = get_config_manager().get["Language"]
    transsubs.main(src,trgt,lang)

@menu_tag(label="Synchronize", group="subtitles")
def sub_sync(fil):
    """Synchronize subtitle with video"""
    from shared_data import get_shared
    s = get_shared()

    # Controleer of er een video geselecteerd is
    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    video_files = [f for f in selected if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
    if video_files:
           tb_update('tb_info', f"⚠️ Error: You selected a video for an SRT action: {', '.join([os.path.basename(v) for v in video_files])}. Please select only SRT files.", "geel")

    selected = s.app.lb_files.get_selected_file_paths() if hasattr(s.app, 'lb_files') else []
    if not selected:
           tb_update('tb_info', "⚠️ No file selected for this action.", "geel")
    tb_update('tb_info', "⚠️ Synchronize: Feature needs configuration", "normal")
    print("⚠️ This function needs: fils, get_config_manager, autosubsync module")
    print("⚠️ Please implement these dependencies first")
    return
    print("srtname = " + srtname)
    synchronized_srt = srtname+".srt"
    print("sync = " + synchronized_srt)
    # rename unsyncronised
    unsynchronized_srt = srtname + ".unsync.srt"
    print("unsync = " + unsynchronized_srt)
    os.rename(synchronized_srt, unsynchronized_srt)
    #ffsubsync(fil,unsynchronized_srt,synchronized_srt)
    #subsync (fil -i unsynchronized.srt > synchronized.srt
    autosubsync.synchronize(fil,unsynchronized_srt,synchronized_srt)

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

def sub_extract(fil):
    # ffmpeg -i Movie.mkv -map 0:s:0 subs.srt
    # strCmd = "ffmpeg -loglevel panic -i " + f + " -map 0:s:0 " + o

    lang = get_config_manager().get["Language"]
    print("fil      = " + fil)

    o = fil + ".srt"
    print("o        = " + o)
    oo = o.replace("mkv",lang)
    print("oo       = " + oo)
    strCmd = "ffmpeg -loglevel panic -i " + fil + " -map 0:s:0 " + oo
    proc = runCmd(strCmd,"sub_extract")

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
    out = sp.run(['ffprobe','-loglevel','error','-select_streams','s','-show_entries','stream=index:stream_tags=language','-of','csv=p=0', fil],\
             stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    subs=out.stdout
    subs_list = subs.split("\n")

    last_sub = subs_list.pop(-2)
    subnum = last_sub.split(",").pop(0)
    return subnum, subs_list

@menu_tag(label="Resync")
def subs_resync():
    # Get the input and output directories from the user
    input_dir = filedialog.askdirectory() +"/"
    output_dir = input_dir + "/subs/"


    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            fil = input_dir + file
            sub_extract(fil)
            #mkv_NO_sub(fil)
            #sub_sync(fil)
            #mkv_embed_sub(fil)
            print("_____________________________________________________________")
            print("_____________________________________________________________")
            print("_____________________________________________________________")


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
        # Skip empty lines, numbers only, and timecodes
        if line and not line.isdigit() and not re.match(timecode_pattern, line):
            # Skip lines with arrows (timestamp separator)
            if '-->' not in line:
                text_lines.append(line)
    
    print(f"🔍 Found {len(text_lines)} text lines")
    if text_lines:
        print(f"   First line: '{text_lines[0][:100]}'")
    
    if not text_lines:
        return "xx", "xxx", "No Language", 0.0, "No text found"
    
    # Combine multiple text lines for better detection
    sample_text = ' '.join(text_lines[:10])  # Use first 10 text lines
    print(f"🔍 Sample text length: {len(sample_text)} chars")
    
    # detect language
    try:
        langs = detect_langs(sample_text)
        print(f"🔍 Detected languages: {langs}")
        
        for item in langs:
            # The first one returned is usually the one that has the highest probability
            short2 = item.lang
            short3 = Language.get(short2).to_alpha3(variant='B')
            naam = Language.get(short2).display_name()
            print(f"✅ Returning: {short2}, {short3}, {naam}, {item.prob}")
            return short2, short3, naam, item.prob, text_lines[0] if text_lines else ""
    except Exception as e:
        print(f"❌ Exception in lang_detect: {e}")
        return "xx", "xxx", "No Language", 0.0, f"Detection error: {str(e)}"
    
    # Fallback if no language detected
    return "xx", "xxx", "No Language", 0.0, "No detection result"

@menu_tag(label="Translate 2")
def translate():
    #input_file = filedialog.askopenfilename() +"/" # get file handle (open file)
    input_file = filedialog.askopenfilename() #get filename full path
    print(input_file)
    sub_translate(input_file)
