#-------------------------------------------------------------------------------
# Name:        shared_utils.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# shared_utils.py

import os, json, inspect
from pathlib import Path
from collections import namedtuple
import tkinter as tk
import customtkinter as ctk
from widgets.smart_entry import SmartEntry
import threading

# ───────────────────────────────────────────────
# SHARED STATE ACCESS
# ───────────────────────────────────────────────

def get_shared_snapshot():
    """Returns key parts of shared state as a namedtuple proxy."""
    Shared = namedtuple("Shared", [
        "app", "entry_data", "manager", "last_entry", "pop_menu",
        "gui_queue", "segbut_var", "inc_subs_var",
        "dirtree_lst", "files_lst", "vids_lst", "subs_lst", "upd_lst",
        "TK_FONT", "CTK_FONT"
    ])

    def safe(attr, fallback=None):
        return getattr(shared_data, attr, fallback)

    return Shared(*[safe(field) for field in Shared._fields])

def register_shared(**kwargs):
    from shared_data import get_shared
    shared = get_shared()  # ✅ This hits your proper SharedState instance

    assert shared.__class__.__name__ == "SharedState", f"☠️ Got {shared.__class__.__name__} instead!"
    for key, value in kwargs.items():
        try:
            setattr(shared, key, value)
        except AttributeError as e:
            print(f"❌ Failed to set '{key}': {e}")

# ───────────────────────────────────────────────
# WIDGET INTROSPECTION
# ───────────────────────────────────────────────

def find_widget_name(widget):
    """Safely resolve the closest custom_name up the widget tree."""
    while widget is not None:
        name = getattr(widget, "custom_name", None)
        if isinstance(name, str):
            return name
        widget = widget.master
    return "unknown"

# ───────────────────────────────────────────────
# FILESYSTEM + PATH UTILS
# ───────────────────────────────────────────────

def get_settings_file(name):
    """Return full path to a JSON config file under Settings/"""
    base = f"{name}.json"
    if base.endswith(".json.json"):
        base = base.replace(".json.json", ".json")

    root = Path(__file__).resolve().parent.parent
    return root / "Settings" / base

def get_app_name():
    """Return base config filename derived from this module."""
    path = Path(__file__)
    return path.stem + ".json"

class fils:
    """Filename parser & metadata extractor."""
    def __init__(self, fullpath):
        self.fullpath = fullpath
        self.f_path = os.path.dirname(fullpath)
        self.b_name = os.path.basename(fullpath)
        self.f_name = Path(fullpath).stem
        self.f_ext = Path(fullpath).suffix
        self.f_ext2 = self.b_name.split('.', 1)[1] if '.' in self.b_name else ""
        self.f_parent = Path(fullpath).parent.name
        self.f_drv = Path(fullpath).drive

    def show(self):
        for attr in vars(self):
            print(f"{attr}: {getattr(self, attr)}")

# ───────────────────────────────────────────────
# CLEANING + DISPLAY HELPERS
# ───────────────────────────────────────────────

def clean_value(value):
    if isinstance(value, (tk.StringVar, ctk.StringVar)):
        return value.get()
    elif isinstance(value, dict):
        return {k: clean_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return type(value)(clean_value(v) for v in value)
    elif hasattr(value, "get"):  # e.g., CTkEntry
        return value.get()
    return value

def show_dict(app, data, label="Dictionary"):
    tb_debug = app.tb_debug
    tb_debug.update_content(f"\n{label.upper()} content:\n", "geel")

    lines = []
    for k, v in data.items():
        cleaned = clean_value(v)
        formatted = json.dumps(cleaned, indent=4) if isinstance(cleaned, (dict, list)) else str(cleaned)
        lines.append(f"\nkey = {k},\nval = {formatted}\n")

    tb_debug.update_content("".join(lines), "normal")

def show_json_file(app, name):
    tb_debug = app.tb_debug
    path = get_settings_file(name)
    tb_debug.update_content(f"\nCONFIG_DATA: {path} content:\n", "geel")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            tb_debug.update_content(f"{k}: {v}\n", "normal")
    except Exception as e:
        tb_debug.update_content(f"⚠️ Failed to load: {e}", "rood")

# ───────────────────────────────────────────────
# MISC
# ───────────────────────────────────────────────

def log_current_function():
    """Prints the name of the calling function (one level up)."""
    print(f"🔍 Executing: {inspect.currentframe().f_back.f_code.co_name}")

def sync_all_entries_to_config():
    for label, entry in s.entry_data.items():
        value = get_config_manager().get["persistent_cfg"].get(label, "")
        entry["var"].set(value)

def audit_entry_data():
    for label, data in s.entry_data.items():
        var = data.get("var")
        val = var.get() if var else "🚫 No var"
        print(f"🔍 {label}: {val}")

def audit_entries():
    from rich import print
    print("[bold underline]🔍 SmartEntry Audit[/]")

    for name, smart in SmartEntry.registry.items():
        bound_var = getattr(smart, "var", None)
        widget_val = smart.widget.get()
        var_val = bound_var.get() if bound_var else "🚫 No StringVar"
        synced = "✅" if var_val == widget_val else "⚠️"

        print(f"[bold]{name}[/]: {synced} widget = '{widget_val}' | var = '{var_val}'")

def inspect_widget_tree(widget, indent=0):
    print("  " * indent + f"{widget.winfo_class()} - {widget.winfo_name()}")
    for child in widget.winfo_children():
        inspect_widget_tree(child, indent + 1)

def run_in_gui(callback):
    from shared_data import get_shared
    app = get_shared().app

    if threading.current_thread() == threading.main_thread():
        callback()
    else:
        app.after(0, callback)
