#-------------------------------------------------------------------------------
# Name:        settings.py
# Purpose:      This module takes care of:
#               - Language switching
#               - Themes and color schemes
#               - Font & icon style updates
#               - Display modes and appearance behavior
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# gui_control/settings.py

import customtkinter as ct

class WatchedDict(dict):
    def __init__(self, *args, on_change=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_change = on_change

    def __setitem__(self, key, value):
        if self.get(key) != value:
            super().__setitem__(key, value)
            if self._on_change:
                self._on_change(key, value)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self.__setitem__(k, v)

def set_language(_app, new_language):
    from utils import log_settings
    config = shared.config
    config["persistent_cfg"]["Language"] = new_language
    log_settings(f"✅ Language changed to: {new_language}")

def set_appearance_mode(_app, new_theme):
    from utils import log_settings
    config = shared.config
    ct.set_appearance_mode(new_theme)
    config["persistent_cfg"]["Theme"] = new_theme
    update_entry_styles(get_shared())
    color_debug(get_shared())
    log_settings(f"✅ Theme changed to: {new_theme}")

def set_color_scheme(_app, new_color_scheme):
    from utils import log_settings
    config = shared.config
    ct.set_default_color_theme(new_color_scheme)
    config["persistent_cfg"]["Color_scheme"] = new_color_scheme
    log_settings(f"✅ Color scheme changed to: {new_color_scheme}")

def set_font_styles(_app, new_font_style):
    from utils import log_settings
    get_config()["persistent_cfg"]["font_style"] = new_font_style
    log_settings(f"✅ Font style changed to: {new_font_style}")

def set_icon_styles(_app, new_icon_style):
    from utils import log_settings
    config = shared.config
    config["persistent_cfg"]["icon_style"] = new_icon_style
    log_settings(f"✅ Icon style changed to: {new_icon_style}")

def set_min_freespace(_app, new_min_freespace):
    from utils import log_settings
    config = shared.config
    min_freespace = int(new_min_freespace)
    config["persistent_cfg"]["min_freespace"] = min_freespace
    log_settings(f"✅ Minimum free space set to: {min_freespace} GB")


def set_display_mode(_app, mode):
    from utils import log_settings
    if mode == "fullscreen":
        _app.attributes('-fullscreen', True)
    elif mode == "windowed":
        _app.attributes('-fullscreen', False)
    elif mode == "borderless":
        _app.overrideredirect(True)
    elif mode == "compact":
        _app.geometry("400x300")
        _app.attributes('-fullscreen', False)
    else:
        log_settings(f"❌ Invalid display mode: {mode}", tag="rood")
        return

    config = shared.config
    config["persistent_cfg"]["Display_mode"] = mode
    log_settings(f"✅ Display mode changed to: {mode}")



