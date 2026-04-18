#-------------------------------------------------------------------------------
# Name:        actions_lb_files.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# popup_actions/actions_lb_files.py

import os
import sys
import subprocess
import platform
from tkinter import messagebox
from decorators.decorators import menu_tag

# Subprocess worker for recycle-bin delete (avoids Intel DLL crashes in-process)
_DELETE_WORKER = os.path.join(os.path.dirname(__file__), "_delete_worker.py")


def _recycle_via_ps_direct(path: str) -> None:
    """Call PowerShell directly to move a file to the recycle bin.
    Used in frozen builds where sys.executable is the .exe, not Python."""
    safe = os.path.abspath(path).replace("'", "''")
    ps_cmd = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
        f"'{safe}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit {result.returncode}")




@menu_tag(label="Select All",icon="☑️",group=["lbox"])
def select_all_files():
    """Select all files in the listbox"""
    from shared_data import get_shared
    s = get_shared()
    listbox = s.app.lb_files
    
    # Select all items using CTkListbox activate method
    if hasattr(listbox, 'listbox'):
        count = len(listbox.current_items)
        for i in range(count):
            try:
                listbox.listbox.activate(i)
            except:
                pass
        print(f"☑️ Selected all {count} files")
        # Controleer of er een SRT geselecteerd is bij een video-actie
        selected_srts = [f for f in listbox.get_selected_file_paths() if f.lower().endswith('.srt')]
        selected_videos = [f for f in listbox.get_selected_file_paths() if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
        if selected_videos and selected_srts:
            from utils import update_tbinfo
            update_tbinfo("⚠️ Waarschuwing: Je hebt zowel een video als een SRT geselecteerd. Dit is een onjuiste combinatie.", "geel")
    else:
        print("⚠️ Could not select all files")


@menu_tag(label="Deselect All",icon="☐",group=["lbox"])
def deselect_all_files():
    """Deselect all files in the listbox"""
    from shared_data import get_shared
    s = get_shared()
    listbox = s.app.lb_files
    
    # Deselect all items using CTkListbox deactivate method
    if hasattr(listbox, 'listbox'):
        # Get all selected indices and deselect them
        selected = list(listbox.listbox.curselection())
        for idx in selected:
            try:
                listbox.listbox.deactivate(idx)
            except:
                pass
        print(f"☐ Deselected all files")
    else:
        print("⚠️ Could not deselect files")


@menu_tag(label="Delete Files",icon="🧹",group=["lbox"])
def delete_selected_files():
    """Delete selected files - moves to recycle bin via subprocess worker"""
    from shared_data import get_shared
    from utils import update_tbinfo
    s = get_shared()
    listbox = s.app.lb_files
    selected = listbox.get_selected_file_paths()

    if not selected:
        messagebox.showinfo("No Selection", "Please select one or more files to delete.")
        return

    file_count = len(selected)
    file_word = "file" if file_count == 1 else "files"
    if not messagebox.askyesno("Confirm Deletion",
                               f"Move {file_count} {file_word} to recycle bin?"):
        return

    existing = [p for p in selected if os.path.exists(p)]
    missing  = [p for p in selected if not os.path.exists(p)]

    for path in missing:
        update_tbinfo(f"❓ File not found: {os.path.basename(path)}", "rood")

    if existing:
        if getattr(sys, "frozen", False):
            # In frozen mode sys.executable is the .exe, not a Python interpreter.
            # Call PowerShell directly for each file without the intermediate worker.
            for path in existing:
                try:
                    _recycle_via_ps_direct(path)
                    name = os.path.basename(path)
                    update_tbinfo(f"♻️ Moved to recycle bin: {name}", "groen")
                except Exception as e:
                    name = os.path.basename(path)
                    update_tbinfo(f"❌ Delete failed ({name}): {e}", "rood")
        else:
            proc = subprocess.run(
                [sys.executable, _DELETE_WORKER] + existing,
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            for line in proc.stdout.splitlines():
                if line.startswith("OK:"):
                    name = os.path.basename(line[3:])
                    update_tbinfo(f"♻️ Moved to recycle bin: {name}", "groen")
                elif line.startswith("NOTFOUND:"):
                    name = os.path.basename(line[9:])
                    update_tbinfo(f"❓ Not found: {name}", "rood")
                elif line.startswith("ERROR:"):
                    rest = line[6:]
                    path_part, _, msg = rest.partition(":")
                    name = os.path.basename(path_part)
                    update_tbinfo(f"❌ Delete failed ({name}): {msg}", "rood")
            if proc.returncode != 0 and proc.stderr:
                print(f"[delete_worker stderr] {proc.stderr.strip()}")

    # Remove from all shared lists to prevent reappearing on filter change
    s.files_lst = [p for p in s.files_lst if p not in selected]
    s.vids_lst = [p for p in s.vids_lst if p not in selected]
    s.subs_lst = [p for p in s.subs_lst if p not in selected]
    s.upd_lst = [p for p in s.upd_lst if p not in selected]
    
    # Update listbox
    listbox.items = [p for p in listbox.items if p not in selected]
    listbox.current_items = listbox.items.copy()
    listbox.update_listbox(listbox.items)

@menu_tag(label="Reveal Files",icon="🧹",group=["lbox"])
def reveal_selected_in_explorer():
    from shared_data import get_shared
    s = get_shared()
    listbox = s.app.lb_files
    selected = listbox.get_selected_file_paths()

    for path in selected:
        if not os.path.exists(path):
            print(f"❓ Path does not exist: {path}")
            continue

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", os.path.normpath(path)])
            else:
                print(f"🌐 Reveal not implemented for {platform.system()}")
        except Exception as e:
            print(f"⚠️ Failed to reveal: {path}\n{e}")