#-------------------------------------------------------------------------------
# Name:        core.py
# Purpose:      This module will define your MyApp class shell and delegate
#               its functionality to supporting modules like ui_config,
#               widget_logic, and lifecycle.
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# mkvapp/core.py

import customtkinter as ct
import tkinter as tk
from tkinter import font as tkFont
from tkinter import StringVar
import shared_data
from shared_data import shared, get_shared
from mkvapp.lifecycle import init_after_ui, setup_utils, setup_pop_menu, setup_binding_manager
from menus import Popup

class MyApp(ct.CTk):
    def __init__(self):
        super().__init__()
        s = get_shared()

        # ✍️ Register the app globally
        s.app = self
        config = shared.config

        # 🖋️ Style
        font_family = config.get("persistent_cfg", {}).get("Font_family", "Arial")
        font_size = int(config.get("persistent_cfg", {}).get("Font_size", 12))
        font_weight = config.get("persistent_cfg", {}).get("Font_weight", "normal")

        s.TK_FONT = tkFont.Font(family=font_family, size=font_size, weight=font_weight)
        s.CTK_FONT = ct.CTkFont(family=font_family, size=font_size, weight=font_weight)

        self.TK_FONT = s.TK_FONT
        self.CTK_FONT = s.CTK_FONT

        self.title("MKV Toolkit")
        self.geometry("1250x700")
        self.configure_grid()

        # Shared values
        self.widget_registry = {}
        self.entry_data = {}
        self.file_path_map = {}

        # Global theme
        theme = config.get("persistent_cfg", {}).get("Theme", "dark")
        ct.set_appearance_mode(theme)

        # UI setup (delegated)
        from mkvapp.ui_config import build_layout
        build_layout(self)

    def configure_grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def init_after_ui(self):
        setup_utils()
        setup_pop_menu(self)
        setup_binding_manager(self)
        init_after_ui(self)
