# Utility: statusbalk wissen
def clear_statusbar():
    s = get_shared()
    if hasattr(s, 'bottomrow_label'):
        s.bottomrow_label.show_message("")
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     29/05/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import tkinter as tk
from tkinter import font as tkFont
import customtkinter as ct
import queue

from logger_singleton import logger
from config.smart_config_manager import config_mgr  # ✅ Use the singleton popup_key directly

# Singleton SharedState for cross-module data sharing
class SharedState:
    _instance = None

    def __init__(self):
        # GUI-independent fields
        self.gui_queue: queue.Queue = queue.Queue()
        self.app = None
        self.binding_manager = None
        self.pop_menu = None
        self.all_filterboxes: list = []

        self.config_mgr = config_mgr  # ✅ Use the shared instance

        self.last_entry: str = "source"
        self.base_path = None

        # UI-aware (but not yet tk-bound)
        self.segbut_var = None
        self.inc_subs_var = None

        # Fonts
        self.TK_FONT: tkFont.Font | None = None
        self.CTK_FONT: ct.CTkFont | None = None

        # Entry management
        self.entry_data: dict = {
            "source": {"var": None, "name": None, "widget": None, "entry": None, "orig_fg": None, "orig_bg": None},
            "target": {"var": None, "name": None, "widget": None, "entry": None, "orig_fg": None, "orig_bg": None},
            "backup": {"var": None, "name": None, "widget": None, "entry": None, "orig_fg": None, "orig_bg": None}
        }

        self.entry_colors: dict = {
            "normal_bg": "white",
            "normal_fg": "black",
            "inverted_bg": "black",
            "inverted_fg": "white"
        }

        # Shared data lists
        self.subfol_lst: list = []
        self.dirtree_lst: list = []
        self.files_lst: list = []
        self.vids_lst: list = []
        self.subs_lst: list = []
        self.upd_lst: list = []

    def init_fonts(self):
        family = self.config_mgr.get("persistent_cfg", "Font_family", "Arial")
        size = int(self.config_mgr.get("persistent_cfg", "Font_size", 12))
        weight = self.config_mgr.get("persistent_cfg", "Font_weight", "normal")

        self.TK_FONT = tkFont.Font(family=family, size=size, weight=weight)
        self.CTK_FONT = ct.CTkFont(family=family, size=size, weight=weight)

        #logger.info(f"🎨 Fonts initialized → {family}, {size}px, weight={weight}")

    def update_base_path_from_last_entry(self):
        if hasattr(self.last_entry, "get"):
            self.base_path = self.last_entry.get()
            print(f"🔄 base_path updated from last_entry → {self.base_path}")
        else:
            print("⚠️ last_entry is missing or invalid")

# Singleton accessor
def get_shared() -> SharedState:
    if SharedState._instance is None:
        SharedState._instance = SharedState()
    return SharedState._instance

# ✅ Public config accessor using config_mgr directly
def get_config(section=None, key=None, default=None):
    if section and key:
        return config_mgr.get(section, key, default)
    elif section:
        return config_mgr.get(section, default)
    return config_mgr.data

# 🔍 Safe nested accessor
def get_config_value(section, key=None, default=None):
    try:
        if key:
            return config_mgr.get(section, key, default)
        return config_mgr.get(section, default)
    except Exception as e:
        logger.warning(f"⚠️ Config access failed: {section}.{key} → {e}")
        return default

# Optional popup_key
shared = get_shared()