
# Let op: import shared/get_shared alleen binnen functies waar nodig (lazy import)
# Herstel oorspronkelijke imports
import tkinter as tk
#-------------------------------------------------------------------------------
# Name:        scanner.py
# Purpose:      - Directory scanning (fast_scandir)
#               - File filtering & categorization
#               - Updating your listboxes
#               - Queue processing
#
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
__all__ = ["apply_segment_filter","browse_folder","fast_scandir","focusin_handler",
            "get_shared","on_toggle", "process_gui_queue","safe_update_tblb",
            "test_scandir_lists","update_entry_styles", "update_files_from_selected_folder",
            "update_tblb","wait_for_widget_attr"]

# gui_control/scanner.py


import os, threading, queue,utils
from tkinter import END
from tkinter import filedialog as fd
from .logger_singleton import logger
from utils.app_context import ctx
from utils.shared_utils import run_in_gui
# Lazy import: from widgets.base_textbox import BaseTBox
import time

# Lazy import shared/get_shared only inside functions to avoid circular import


# Remove global s, always use local get_shared() inside functions

def fast_scandir(app,path):

    # Lazy import to avoid circular import
    from shared_data import get_shared
    s = get_shared()

    # Set base_path to the scanned path
    s.base_path = path

    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
    subtitle_exts = {".srt", ".sub", ".ass", ".vtt"}

    # Clear shared lists
    s.subfol_lst.clear()
    s.dirtree_lst.clear()
    s.files_lst.clear()
    s.vids_lst.clear()
    s.subs_lst.clear()
    s.upd_lst.clear()

    app.file_path_map = {}
    s.folder_path_map = {}
    # Ordered list of (display_string, full_path) for building line->path mapping
    s.dirtree_entries = []

    create_dir_tree(path)

    recursive = bool(s.inc_subs_var.get())


    def file_generator(root_dir):
        for root, dirs, files in os.walk(root_dir):
            if not recursive and root != root_dir:
                continue
            for fname in files:
                yield os.path.join(root, fname)

    def process_files():
        for file_path in file_generator(path):
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower()

            s.files_lst.append(file_path)
            app.file_path_map[file_name] = file_path
            if ext in video_exts:
                s.vids_lst.append(file_path)
            elif ext in subtitle_exts:
                s.subs_lst.append(file_path)

        # ✅ Only now, when lists are fully ready, trigger UI updates
        run_in_gui(lambda: apply_segment_filter())
        run_in_gui(lambda: update_tblb(get_shared().app))

    threading.Thread(target=process_files, daemon=True).start()

def create_dir_tree(path, indent=0, is_root=True):
    from shared_data import get_shared
    s = get_shared()
    prefix = " " * indent

    if not is_root:
        folder_display_name = f"{prefix}📁 {os.path.basename(path)}/"
        s.dirtree_lst.append(folder_display_name)
        # Keep an ordered list of entries (display, path). We will build a
        # reliable line->path mapping after rendering the textbox so that
        # identical basenames at the same indentation do not collide.
        s.dirtree_entries.append((folder_display_name, path))

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    create_dir_tree(entry.path, indent + 4, is_root=False)
    except PermissionError:
        s.dirtree_lst.append(" " * (indent + 4) + "🚫 [Access Denied]")
    except Exception as e:
            print(f"⚠️ Failed to scan {path}: {e}")  # This line remains unchanged

def process_gui_queue():
    from shared_data import get_shared
    s = get_shared()
    try:
        while True:
            task = s.gui_queue.get_nowait()
            task()
    except queue.Empty:
        pass
    except Exception as e:
        print(f"💥 Error while processing GUI task: {e}")
    finally:
        try:
            # Only reschedule if the app is still alive
            if s.app.winfo_exists():
                s.app.after(100, process_gui_queue)
        except Exception as e:
            print(f"🛑 GUI shutdown detected, stopping queue loop: {e}")

def update_segbut_colors():
    from shared_data import get_shared
    s = get_shared()
    app = s.app

    # Check if lists are empty
    videos_empty = not s.vids_lst
    subs_empty = not s.subs_lst
    
    # Get current selection
    current_value = s.segbut_var.get() if s.segbut_var else "Videos"

    # Set colors and borders for all buttons
    if hasattr(app, 'segbut_videos'):
        is_active = (current_value == "Videos")
        app.segbut_videos.configure(
            text_color="red" if videos_empty else "white",
            border_width=2 if is_active else 0,
            border_color="orange" if is_active else "gray"
        )
    
    if hasattr(app, 'segbut_subs'):
        is_active = (current_value == "Subtitles")
        app.segbut_subs.configure(
            text_color="red" if subs_empty else "white",
            border_width=2 if is_active else 0,
            border_color="orange" if is_active else "gray"
        )
    
    if hasattr(app, 'segbut_all'):
        is_active = (current_value == "All")
        app.segbut_all.configure(
            text_color="white",
            border_width=2 if is_active else 0,
            border_color="orange" if is_active else "gray"
        )

def apply_segment_filter():
    from shared_data import get_shared
    s = get_shared()
    mode = s.segbut_var.get()

    if mode == "Videos":
        s.upd_lst = s.vids_lst.copy()
    elif mode == "Subtitles":
        s.upd_lst = s.subs_lst.copy()
    else:
        s.upd_lst = s.files_lst.copy()

    s.upd_lst = list(dict.fromkeys(s.upd_lst))
    s.app.lb_files.set_items(s.upd_lst)

    # Update segbut colors
    update_segbut_colors()

    # 👇 Optional: Refresh popup if it's visible
    if s.pop_menu and hasattr(s, "last_popup_event"):
        s.pop_menu.show_popup("lb_files", s.last_popup_event)

def update_tblb(app):
    update_tb(app)
    update_lb(app)

def update_tb(app):
    from shared_data import get_shared
    s = get_shared()

    # 📁 Update tb_folders
    tb = app.tb_folders
    folders = s.dirtree_lst
    
    # Add [..] parent folder navigation at the top (like Total Commander)
    # Always show it, even if there are no subfolders
    parent_nav = ["⬆️ [..]"]
    
    if folders:
        folders = parent_nav + folders
        msg = "\n".join(folders)
    else:
        msg = "\n".join(parent_nav + ["ℹ️ No subfolders"])
    
    tb.clear_textbox()
    tb.update_content(msg)
    # Build a stable mapping from visible line numbers to full paths.
    # The first line is the parent navigation entry; subsequent lines map
    # directly to the ordered `s.dirtree_entries` we collected during scan.
    try:
        s.folder_line_map = {}
        # line numbering in the Text widget starts at 1
        line_num = 1
        # parent navigation occupies the first line
        line_num += 1
        for display, fullpath in s.dirtree_entries:
            s.folder_line_map[line_num] = fullpath
            line_num += 1
    except Exception:
        s.folder_line_map = {}

def update_lb(app):
    from shared_data import get_shared
    s = get_shared()

    # 📦 Update lb_files met respect voor segment filter
    mode = s.segbut_var.get() if hasattr(s, 'segbut_var') else None
    
    if mode == "Videos":
        files = s.vids_lst
    elif mode == "Subtitles":
        files = s.subs_lst
    else:
        files = s.upd_lst
    
    unique_files = list(dict.fromkeys(files)) if files else []
    app.lb_files.set_items(unique_files)


def safe_update_tblb(app, tries=20):
    from shared_data import get_shared
    s = get_shared()
    if hasattr(s.app, "tb_folders"):
        update_tblb(app)
    elif tries > 0:
        app.after(100, lambda: safe_update_tblb(app, tries - 1))
    else:
        print("❌ tb_folders never became available.")

def on_toggle():
    from utils import log_settings
    from shared_data import get_shared
    s = get_shared()
    config = s.config
    config["persistent_cfg"]["Inc_subdirs"] = s.inc_subs_var.get()
    log_settings(f"\u2705 Include subdirs: {s.inc_subs_var.get()}")

    # Get scan path
    entry = getattr(s, "last_entry_widget", None) or s.entry_data["Source"]["entry"]
    path = entry.get()

    # Start a new scan
    fast_scandir(s.app,path)

def focusin_handler(event, app):
    widget = event.widget
    # print("[DEBUG] focusin_handler: last_entry_widget type:", type(widget), widget)
    from shared_data import get_shared
    s = get_shared()

    # Try to grab logical entry name from widget or its parent
    valid_names = {"source", "target", "backup"}
    entry_name = getattr(widget, "custom_name", None)

    # Fallback to parent if needed
    if not entry_name and hasattr(widget.master, "custom_name"):
        entry_name = getattr(widget.master, "custom_name")

    # Final fallback: strip '_entry' from internal name
    if entry_name not in valid_names:
        parent = widget.master
        entry_name = getattr(parent, "custom_name", None)

    if entry_name not in valid_names:
        print(f"⚠️ Unknown entry name: {entry_name}")
        return

    # Zorg dat alleen het widget-object wordt opgeslagen, nooit de stringwaarde
    s.last_entry_widget = widget
    # print("[DEBUG] last_entry_widget direct na toekenning (focusin_handler):", type(s.last_entry_widget), s.last_entry_widget)
    assert not isinstance(s.last_entry_widget, str), f"[FOUT] last_entry_widget is een string: {s.last_entry_widget}"
    s.last_entry_name = entry_name
    s.active_entry_widget = widget
    # Sla ook de huidige waarde van de entry op als string (via SmartEntry)
    smart = s.entry_data.get(entry_name, {}).get("entry")
    if smart:
        s.last_entry_value = smart.value
        path = smart.value
    else:
        s.last_entry_value = None
        path = widget.get() if hasattr(widget, "get") else ""

    if os.path.exists(path):
        fast_scandir(app, path)
    else:
        print(f"{path} not found, aborting scan")

    # 🔥 Highlight entry now that we hebben de juiste naam
    update_entry_styles(s)

def browse_folder(entry_key="source"):
    """
    Opens a folder dialog, updates the StringVar for the given entry,
    syncs the config, and optionally triggers a folder scan.
    """
    from shared_data import get_shared
    s = get_shared()
    config = s.config
    entry_info = s.entry_data.get(entry_key)
    if not entry_info or "var" not in entry_info:
        logger.warning(f"🛑 Missing entry data for key '{entry_key}'")
        return

    smart = entry_info["entry"]

    initial_folder = smart.value if os.path.isdir(smart.value) else None

    folder = fd.askdirectory(
        title=f"Select {entry_key.capitalize()} Folder",
        initialdir=initial_folder
    )
    if folder:
        # Update via SmartEntry wrapper
        smart.set_value(folder)
        smart.force_redraw()
        smart.widget.update_idletasks()
        smart.widget.focus_set()
        # Sync naar config
        config["persistent_cfg"][entry_key] = folder
        # Start scan
        fast_scandir(s.app, smart.value)

    smart = s.entry_data["source"]["entry"]

def update_entry(label, value):
    from shared_data import get_shared
    s = get_shared()
    if label in s.entry_data:
        s.entry_data[label]["var"].set(value)

def reload(app=None):
    """
    Reload the source path from the last_entry widget and trigger a fresh scan.
    """
    from shared_data import get_shared
    s = get_shared()
    app = app or s.app
    source_path = getattr(s, "last_entry_value", None)
    if not source_path and hasattr(s, "last_entry_widget") and s.last_entry_widget:
        try:
            source_path = s.last_entry_widget.get()
        except Exception:
            source_path = None

    if not source_path:
        print("⚠️ No source path set.")
        return

    print(f"🔄 Reloading: {source_path}")
    fast_scandir(app, source_path)

def update_folder_path(entry_key, new_path):
    from utils import log_settings
    from shared_data import get_shared
    s = get_shared()
    config = s.config
    smart = s.entry_data[entry_key]["entry"]
    smart.set_value(new_path)
    smart.force_redraw()
    config["persistent_cfg"][entry_key] = new_path
    log_settings(f"\u2705 {entry_key} path updated: {new_path}")
    fast_scandir(s.app, new_path)

def update_entry_styles(shared):
    """Reset highlight on all SmartEntries and highlight the last focused one."""
    entry_data = shared.entry_data
    last_name = getattr(shared, "last_entry_name", None)
    # Clear highlight from all entries
    for data in entry_data.values():
        smart = data.get("entry")
        if smart:
            smart.reset_highlight()

    # Decide which one gets the highlight
    last_name = last_name or "source"  # fallback to 'source' if None

    smart = entry_data.get(last_name, {}).get("entry")
    if smart:
        smart.highlight("orange")

def _update_tag_config(self, cfg=None):
    s = get_shared()
    config = s.config
    if cfg is None:
        cfg = config.get("tags_cfg", {})

    self.tagcfg = cfg
    for tag, style in cfg.items():
        try:
            self.tag_config(tag, **style)
            print(f"🎨 Registered tag: [{tag}] → {style}")
        except Exception as e:
            print(f"⚠️ Error applying tag [{tag}]: {e}")

def update_files_from_selected_folder(event):
    """Detects clicked folder in tb_folders and updates lb_files."""
    from shared_data import get_shared
    s = get_shared()
    # print("[DEBUG] update_files_from_selected_folder: last_entry_widget type:", type(getattr(s, "last_entry_widget", None)), getattr(s, "last_entry_widget", None))
    try:
        # Get the line number of the insert cursor to uniquely identify the
        # clicked line. This avoids collisions for identical basenames.
        tb = s.app.tb_folders.textbox
        insert_index = tb.index("insert")
        line_number = int(insert_index.split(".")[0])

        # Resolve via the line->path mapping created in update_tb
        selected_path = getattr(s, 'folder_line_map', {}).get(line_number)

        # Fallback: derive path from the visible text if mapping isn't available
        if not selected_path:
            selected_text = s.app.tb_folders.get("insert linestart", "insert lineend")
            selected_folder = selected_text.replace("📁 ", "").strip("/\n")
            selected_path = os.path.join(s.base_path, selected_folder)

        if selected_path and os.path.isdir(selected_path):
            s.app.lb_files.listbox.delete(0, tk.END)  # Clear previous files
            s.files_lst.clear()

            for file in os.listdir(selected_path):
                if os.path.isfile(os.path.join(selected_path, file)):
                    s.files_lst.append(file)
                    s.app.lb_files.listbox.insert(tk.END, file)  # Populate listbox

            # Update base_path en de laatst gefocuste smartentry met het gekozen pad
            # s.base_path = selected_path  # Already done in base_textbox.py
            # Update altijd via de SmartEntry wrapper zoals in browse_folder
            smart_name = getattr(s, "last_entry_name", "source")  # Fallback to "source"
            entry_info = s.entry_data.get(smart_name)
            if entry_info and "entry" in entry_info:
                smart = entry_info["entry"]
                smart.set_value(selected_path)
                smart.force_redraw()
                if hasattr(smart, "widget"):
                    smart.widget.update_idletasks()
                    smart.widget.focus_set()
                # Sync naar config zoals in browse_folder
                s.config["persistent_cfg"][smart_name] = selected_path

    except Exception as e:
        print(f"Error selecting folder: {e}")

def wait_for_widget_attr(app, attr_name, callback, tries=20, delay=100):
    if hasattr(app, attr_name):
        callback()
    elif tries > 0:
        app.after(delay, lambda: wait_for_widget_attr(app, attr_name, callback, tries - 1, delay))
    else:
        print(f"❌ Widget attribute '{attr_name}' not ready after retries.")

def register_widget(name, widget):
    from shared_data import get_shared
    s = get_shared()
    setattr(s.app, name, widget)



