#-------------------------------------------------------------------------------
# Name:        all_actions.py
# Purpose:     Actions for lb_files All menu
#
# Author:      EddyS
#
# Created:     14/01/2026
# Copyright:   (c) EddyS 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import sys
from decorators.decorators import menu_tag
from shared_data import get_shared

@menu_tag(label="Show LogFile", icon="🔍", group=["All"])
def show_logfile_all():
    """Show logfile in tb_info textbox"""
    app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    log_file = os.path.join(app_dir, "Logs", f"{app_name}_log.json")

    from utils.text_helpers import update_tbdebug
    update_tbdebug(f"{app_name}_log.json content:", "geel")

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                update_tbdebug(line.strip())
    except Exception as e:
        update_tbdebug(f"⚠️ Could not read log: {e}", "rood")

@menu_tag(label="Show TextFile", icon="🔍", group=["All"])
def show_textfile_all():
    """Show selected text file in tb_info textbox"""
    from shared_data import shared
    s = get_shared()
    listbox = s.app.lb_files.listbox
    selection = listbox.curselection()
    if not selection:
        print("⚠️ No file selected.")
        return

    filename = listbox.get(selection[0])
    path = s.app.file_path_map.get(filename)
    if not path or not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        from utils.text_helpers import update_tbdebug, clear_tbdebug
        clear_tbdebug()
        update_tbdebug(f"{filename} content:", "geel")
        update_tbdebug(content + "\n", "normal")
    except Exception as e:
        print(f"🚨 Could not read file: {e}")
