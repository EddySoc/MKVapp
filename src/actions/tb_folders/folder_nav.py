"""
Folder navigation actions for tb_folders textbox
"""
import os
import tkinter as tk
from decorators.decorators import menu_tag
from shared_data import get_shared

def open_selected_folder():
    """Navigate into the selected folder in tb_folders"""
    from utils import log_error
    s = get_shared()
    
    try:
        # Get selected text from tb_folders
        tb = s.app.tb_folders.textbox
        try:
            # Try to get selected text first
            selected_text = tb.get("sel.first", "sel.last").strip()
        except tk.TclError:
            # If no selection, use current line
            selected_text = tb.get("insert linestart", "insert lineend").strip()
        
        if not selected_text:
            log_error("⚠️ No folder selected")
            return
        
        # Extract folder name (remove "📁 " if present)
        selected_folder = selected_text.replace("📁 ", "").strip("/").strip()
        
        if not selected_folder or selected_folder == ".." or selected_text.startswith("⬆️ [..]"):
            return
        
        # Construct full path
        current_base = getattr(s, 'base_path', None)
        if not current_base:
            log_error("⚠️ No base path set")
            return
        
        selected_path = os.path.join(current_base, selected_folder)
        if not os.path.isdir(selected_path):
            log_error(f"⚠️ Not a directory: {selected_folder}")
            return

        # Haal BaseDir uit config
        base_dir = s.config_mgr.get_all()["persistent_cfg"].get("BaseDir", None)
        if not base_dir:
            log_error("⚠️ BaseDir niet gevonden in config")
            return
        base_dir_norm = os.path.normpath(base_dir)
        selected_path_norm = os.path.normpath(selected_path)

        # Limiet: niet boven BaseDir
        if os.path.commonpath([selected_path_norm, base_dir_norm]) != base_dir_norm:
            log_error("⚠️ Je mag niet boven BaseDir navigeren")
            return

        # Update base_path naar de nieuwe folder
        s.base_path = selected_path

        # Dynamisch: update actieve SmartEntry
        last_entry_name = getattr(s, "last_entry_name", "source")  # Fallback to "source"
        if last_entry_name in s.entry_data:
            entry_obj = s.entry_data[last_entry_name]["entry"]
            if entry_obj:
                if hasattr(entry_obj, "set_value"):
                    entry_obj.set_value(selected_path)
                elif hasattr(entry_obj, "var") and entry_obj.var:
                    entry_obj.var.set(selected_path)
                # Sync naar config
                s.config_mgr.get_all()["persistent_cfg"][last_entry_name] = selected_path
            else:
                print("DEBUG: entry_obj is None")
        else:
            print(f"DEBUG: {last_entry_name} not in entry_data")

        # Rescan de nieuwe folder
        from utils.scan_helpers import fast_scandir
        fast_scandir(s.app, selected_path)

        print(f"✅ Navigated to: {selected_path}")
        
    except Exception as e:
        log_error(f"❌ Error opening folder: {e}")


def go_to_parent_folder():
    """Navigate to parent directory"""
    from utils import log_error
    s = get_shared()
    
    try:
        current_base = getattr(s, 'base_path', None)
        if not current_base:
            log_error("⚠️ No base path set")
            return
        

        # Haal BaseDir uit config
        base_dir = s.config_mgr.get_all()["persistent_cfg"].get("BaseDir", None)
        if not base_dir:
            log_error("⚠️ BaseDir niet gevonden in config")
            return
        base_dir_norm = os.path.normpath(base_dir)
        current_base_norm = os.path.normpath(current_base)
        # Derive parent from the normalized current base to avoid cases where
        # a trailing slash makes dirname return the same folder.
        parent_path = os.path.dirname(current_base_norm)
        parent_path_norm = os.path.normpath(parent_path)

        print(f"🔍 Current base: '{current_base_norm}'")
        print(f"🔍 Parent path: '{parent_path_norm}'")
        print(f"🔍 BaseDir: '{base_dir_norm}'")

        # Limiet: niet boven BaseDir
        if os.path.commonpath([parent_path_norm, base_dir_norm]) != base_dir_norm:
            log_error("⚠️ Je mag niet boven BaseDir navigeren")
            return

        # Update base_path naar parent
        s.base_path = parent_path_norm

        # Dynamisch: update actieve SmartEntry
        last_entry_name = getattr(s, "last_entry_name", "source")  # Fallback to "source"
        if last_entry_name in s.entry_data:
            entry_obj = s.entry_data[last_entry_name]["entry"]
            if entry_obj:
                if hasattr(entry_obj, "set_value"):
                    entry_obj.set_value(parent_path_norm)
                elif hasattr(entry_obj, "var") and entry_obj.var:
                    entry_obj.var.set(parent_path_norm)
                # Sync naar config
                s.config_mgr.get_all()["persistent_cfg"][last_entry_name] = parent_path_norm
            else:
                print("DEBUG: entry_obj is None")
        else:
            print(f"DEBUG: {last_entry_name} not in entry_data")

        # Rescan de parent folder
        from utils.scan_helpers import fast_scandir
        fast_scandir(s.app, parent_path_norm)

        print(f"✅ Navigated to parent: {parent_path_norm}")

    except Exception as e:
        log_error(f"❌ Error going to parent: {e}")


@menu_tag(label="🔄 Refresh", icon="🔄", group="tb_folders")
def refresh_current_folder():
    """Refresh the current folder view"""
    from utils import log_error
    s = get_shared()
    
    try:
        current_base = getattr(s, 'base_path', None)
        if not current_base:
            log_error("⚠️ No base path set")
            return
        
        # Rescan current folder
        from utils.scan_helpers import fast_scandir
        fast_scandir(s.app, current_base)
        
        print(f"✅ Refreshed: {current_base}")
        
    except Exception as e:
        log_error(f"❌ Error refreshing: {e}")
