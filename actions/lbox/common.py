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
import subprocess
import platform
from tkinter import messagebox
from decorators.decorators import menu_tag

# Try to import send2trash for recycle bin functionality
SEND2TRASH_AVAILABLE = False
USE_WINDOWS_NATIVE = False

try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except Exception as e:
    print(f"⚠️ send2trash import failed: {type(e).__name__}: {e}")
    # On Windows, use native API as fallback
    if platform.system() == "Windows":
        try:
            import ctypes
            from ctypes import windll, c_wchar_p, c_uint, Structure, POINTER, byref
            USE_WINDOWS_NATIVE = True
            print("✓ Using Windows native recycle bin API")
        except Exception as e2:
            print(f"⚠️ Windows native API also failed: {e2}")
            print("Files will be permanently deleted.")
    else:
        print("Files will be permanently deleted.")


def windows_recycle(path):
    """Move file to recycle bin using Windows native API"""
    if not USE_WINDOWS_NATIVE:
        raise RuntimeError("Windows native API not available")
    
    # SHFileOperation constants
    FO_DELETE = 0x0003
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004
    
    class SHFILEOPSTRUCT(Structure):
        _fields_ = [
            ("hwnd", ctypes.c_void_p),
            ("wFunc", c_uint),
            ("pFrom", c_wchar_p),
            ("pTo", c_wchar_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", ctypes.c_int),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", c_wchar_p)
        ]
    
    # Path must be double-null terminated
    path_normalized = os.path.abspath(path) + '\0'
    
    fileop = SHFILEOPSTRUCT()
    fileop.hwnd = None
    fileop.wFunc = FO_DELETE
    fileop.pFrom = path_normalized
    fileop.pTo = None
    fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
    fileop.fAnyOperationsAborted = 0
    fileop.hNameMappings = None
    fileop.lpszProgressTitle = None
    
    result = windll.shell32.SHFileOperationW(byref(fileop))
    if result != 0:
        raise RuntimeError(f"SHFileOperation failed with code {result}")


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
    """Delete selected files - moves to recycle bin if send2trash is available"""
    from shared_data import get_shared
    from utils import update_tbinfo
    s = get_shared()
    listbox = s.app.lb_files
    selected = listbox.get_selected_file_paths()
    
    if not selected:
        messagebox.showinfo("No Selection", "Please select one or more files to delete.")
        return
    
    # Ask for confirmation
    file_count = len(selected)
    file_word = "file" if file_count == 1 else "files"
    if not messagebox.askyesno("Confirm Deletion", 
                               f"Move {file_count} {file_word} to recycle bin?"):
        return

    import traceback
    
    for path in selected:
        try:
            if os.path.exists(path):
                # Try send2trash first
                if SEND2TRASH_AVAILABLE:
                    try:
                        send2trash(path)
                        update_tbinfo(f"♻️ Moved to recycle bin: {os.path.basename(path)}", "groen")
                        continue
                    except Exception as e:
                        update_tbinfo(f"⚠️ send2trash failed: {e}", "geel")
                
                # Try Windows native API as fallback
                if USE_WINDOWS_NATIVE:
                    try:
                        windows_recycle(path)
                        update_tbinfo(f"♻️ Moved to recycle bin: {os.path.basename(path)}", "groen")
                        continue
                    except Exception as e:
                        update_tbinfo(f"⚠️ Windows recycle failed: {e}", "geel")
                
                # Last resort: permanent deletion
                os.remove(path)
                update_tbinfo(f"🗑️ Permanently deleted: {os.path.basename(path)}", "geel")
            else:
                update_tbinfo(f"❓ File not found: {path}", "rood")
        except Exception as e:
            error_trace = traceback.format_exc()
            update_tbinfo(f"⚠️ Failed to delete {os.path.basename(path)}: {e}", "rood")
            update_tbinfo(f"Trace: {error_trace[:500]}", "rood")

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