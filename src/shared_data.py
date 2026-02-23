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

# Avoid importing the entire `utils` package at module-import time to prevent
# triggering package-level side-effects that can cause circular imports.
import logging
logger = logging.getLogger("mkvapp")
# Lazy import: from config.smart_config_manager import config_mgr

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

        # Defer loading the config manager to avoid circular imports during module init
        self._config_mgr = None

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

    @property
    def config_mgr(self):
        if getattr(self, '_config_mgr', None) is None:
            from config.smart_config_manager import config_mgr as _cfg
            self._config_mgr = _cfg
        return self._config_mgr

    @config_mgr.setter
    def config_mgr(self, value):
        self._config_mgr = value

# Singleton accessor
def get_shared() -> SharedState:
    if SharedState._instance is None:
        SharedState._instance = SharedState()
    return SharedState._instance


# ✅ Public config accessor using config_mgr directly
def get_config(section=None, key=None, default=None):
    from config.smart_config_manager import config_mgr
    if section and key:
        return config_mgr.get(section, key, default)
    elif section:
        return config_mgr.get(section, default)
    return config_mgr.data

# 🔍 Safe nested accessor
def get_config_value(section, key=None, default=None):
    from config.smart_config_manager import config_mgr
    try:
        if key:
            return config_mgr.get(section, key, default)
        return config_mgr.get(section, default)
    except Exception as e:
        logger.warning(f"⚠️ Config access failed: {section}.{key} → {e}")
        return default

# Optional: Legacy compatibility - use get_shared() instead
class _SharedProxy:
    """Compatibility proxy that delegates attribute access to the real
    SharedState returned by `get_shared()`. This avoids creating the
    singleton at module import time while keeping the old `shared`
    variable name available for legacy code (e.g. `from shared_data import shared`).
    """
    def __getattr__(self, name):
        return getattr(get_shared(), name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(get_shared(), name, value)

    def __dir__(self):
        return dir(get_shared())

# Provide module-level `shared` name for backward compatibility.
shared = _SharedProxy()