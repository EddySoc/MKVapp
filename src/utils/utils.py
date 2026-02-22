#-------------------------------------------------------------------------------
# Name:        utils.py
# Purpose:      This file contains convenient cross-cutting functions
#               — like color resets, descendant checks, text box management,
#                 and shared label updates:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
__all__ = ["get_shared","initialize_gui_vars","is_descendant",
            "register_widget", "refresh_fonts"]

# project_root/urils/utils.py

import customtkinter as ct
import tkinter as tk
# Lazy imports to avoid circular dependency:
# from widgets import BaseTBox
# from shared_data import shared,get_shared,get_config
import tkinter.font as tkFont
from customtkinter import CTkFont


def is_descendant(child, parent):
    while child is not None:
        if child == parent:
            return True
        child = child.master
    return False

def initialize_gui_vars():
    from shared_data import get_shared, get_config
    s = get_shared()
    config = get_config()
    cfg = config.get("persistent_cfg", {})

    # Fonts
    font_family = cfg.get("FontFamily", "Segoe UI")
    font_size = int(cfg.get("FontSize", 12))
    font_weight = cfg.get("FontWeight", "bold")

    s.TK_FONT = tkFont.Font(family=font_family, size=font_size, weight=font_weight)
    s.CTK_FONT = CTkFont(family=font_family, size=font_size, weight=font_weight)

    # GUI-bound shared vars
    s.segbut_var = tk.StringVar(value=cfg.get("Segbut", "Videos"))
    s.inc_subs_var = tk.BooleanVar(value=cfg.get("inc_subdirs", False))

    for key in s.entry_data:
        s.entry_data[key]["var"] = tk.StringVar()
    print("🔧 GUI variables initialized from config_mgr.data")

def refresh_fonts(cfg):
    from shared_data import get_shared
    s = get_shared()

    font_family = cfg.get("FontFamily", "Segoe UI")
    font_size = cfg.getint("FontSize", 12)
    font_weight = cfg.get("FontWeight", "bold")

    s.TK_FONT = tkFont.Font(family=font_family, size=font_size, weight=font_weight)
    s.CTK_FONT = CTkFont(family=font_family, size=font_size, weight=font_weight)

    # 🧩 Optionally update all registered widgets
    for flb in s.all_filterboxes:
        if hasattr(flb, "apply_shared_font"):
            flb.apply_shared_font()


