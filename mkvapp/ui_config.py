#-------------------------------------------------------------------------------
# Name:        ui_config.py
# Purpose:      this file builds your full UI structure inside MyApp
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import customtkinter as ct
import tkinter as tk
from tkinter import StringVar
from widgets import MyFrame, BaseTBox, FilterListBox, Config_Frame, Debug_Frame
from widgets import ThemedEntry, SmartEntry
from utils.scan_helpers import apply_segment_filter, on_toggle, register_widget, update_entry_styles
from shared_data import get_shared
from customtkinter import get_appearance_mode
import os
from widgets.status_slot import StatusSlot
from widgets.reg_viewer import RegistryViewer
from config.smart_config_manager import get_config_manager

config_mgr = get_config_manager()
config     = config_mgr.get_all()





def build_layout(app,config_data,config_mgr):
    padding = {"padx": (5, 5), "pady": (5, 5)}
    border = {"border_color": "cyan", "border_width": 2}
    persistent = config.setdefault("persistent_cfg", {})
    # Voeg BaseDir toe als die nog niet bestaat
    if "BaseDir" not in persistent:
        persistent["BaseDir"] = r"C:\QBMedia"

    tabview = ct.CTkTabview(app)
    tabview.grid(row=0, column=0, **padding, sticky="nsew")
    tabview.configure(width=1225, height=675, **border)

    app.tabview = tabview

    app.last_row = setup_info_tab(app, tabview, padding,config)
    setup_settings_tab(app, tabview, padding,config)
    setup_debug_tab(app,tabview,padding)

def setup_info_tab(app, tabview, padding,config):
    tabview.add("Info")
    info_tab = tabview.tab("Info")

    app.info_tab = info_tab
    info_tab.custom_name = "info_tab"

    info_tab.rowconfigure((0, 2), weight=1)
    info_tab.rowconfigure(1, weight=30)
    info_tab.columnconfigure(0, weight=1)

    build_top_row(app, info_tab, padding,config_mgr)
    build_middle_row(app, info_tab, padding)
    last_row = build_bottom_row(app, info_tab, padding,config)
    return last_row

def build_top_row(app, tab, padding,config_mgr):
    from customtkinter import get_appearance_mode
    from customtkinter import CTkEntry

    # grab your config dict once
    config = config_mgr.get_all()
    folders = config["persistent_cfg"]

    row = MyFrame(master=tab)
    row.grid(row=0, column=0, sticky="nsew")
    row.grid_columnconfigure((0, 2, 4), weight=1)
    row.grid_columnconfigure((1, 3, 5), weight=3)
    app.first_row = row

    entry_data = {}

    theme = get_appearance_mode()
    default_fg = "#eaeaea" if theme == "Light" else "#1a1a1a"
    default_txt = "#1a1a1a" if theme == "Light" else "#eaeaea"

    for i, label in enumerate(["source", "target", "backup"]):
        initial_value = config["persistent_cfg"].get(label, "")
        var = StringVar(value=initial_value)

        entry = CTkEntry(master=row, textvariable=var)
        entry.custom_name = label.lower()

        entry.configure(
            fg_color=default_fg,
            text_color=default_txt,
            border_color="cyan",
            border_width=2,
            font=(
                config.get("Font_family", "Arial"),
                int(config.get("Font_size", 12)),
                config.get("Font_weight", "normal")
            )
        )

        smart_entry = SmartEntry(
            widget=entry,
            name=label.lower(),
            fg_color=default_fg,
            text_color=default_txt,
            config_mgr=config_mgr
        )
        smart_entry.var = var  # 💡 link the variable

        entry_data[label.lower()] = {
            "entry": smart_entry,
            "var": var
        }

        smart_entry.get_widget().grid(row=0, column=i * 2 + 1, sticky="ew", **padding)

        config_mgr.bind_var(var, label)

    source_entry = entry_data["source"]["entry"]
    def on_source_change(*_):
        new_path = source_entry.value
        from utils.debug_logger import debug_print
        if os.path.exists(new_path):
            s.base_path = new_path
            debug_print(f"✅ base_path set to existing path: {new_path}", "menu")
        else:
            debug_print(f"⚠️ Path does not exist: {new_path}", "menu")

    source_var = entry_data["source"]["var"]
    source_var.trace_add("write", on_source_change)

    from shared_data import get_shared
    update_entry_styles(get_shared())
    app.last_entry_widget = source_entry.get_widget()
    print("[DEBUG] app.last_entry_widget direct na toekenning:", type(app.last_entry_widget), app.last_entry_widget)

    s = get_shared()
    s.last_entry_widget = source_entry.get_widget()
    print("[DEBUG] s.last_entry_widget direct na toekenning (ui_config):", type(s.last_entry_widget), s.last_entry_widget)

    s.entry_data.update(entry_data)
    for label, data in s.entry_data.items():
            smart_entry = data["entry"]
            var = data["var"]
            smart_entry.var = var  # 🔄 Ensure linkage

    app.entry_data = entry_data

    for label in ["source", "target", "backup"]:
        value = config["persistent_cfg"].get(label, "")
        s.entry_data[label]["entry"].set_value(value)


def sync_from_config(self):
    from utils.debug_logger import debug_print
    if not self.name:
        debug_print(f"⚠️ No name assigned for sync", "menu")
        return

    new_value = config["persistent_cfg"].get(self.name, "")
    if self.var:
        self.var.set(new_value)
        debug_print(f"🔄 SmartEntry '{self.name}' synced to: {new_value}", "menu")
    else:
        # fallback direct text update
        self.widget.delete(0, "end")
        self.widget.insert(0, new_value)

def build_middle_row(app, tab, padding):
    row = MyFrame(master=tab)
    row.grid(row=1, column=0, sticky="nsew")
    row.columnconfigure(0, weight=2, minsize=400)
    row.columnconfigure(1, weight=1, minsize=200, uniform="group1")
    row.columnconfigure(2, weight=1, minsize=200, uniform="group1")
    row.rowconfigure(0, weight=1)
    app.mid_row = row

    app.tb_info = BaseTBox(master=row, name="tb_info",wrap="none")
    app.tb_info.custom_name = "tb_info"
    app.tb_info.grid(row=0, column=0, sticky="nsew")

    app.tb_folders = BaseTBox(master=row, name="tb_folders", wrap="none")
    app.tb_folders.custom_name = "tb_folders"
    app.tb_folders.grid(row=0, column=1, sticky="nsew")
    s = get_shared()
    s.app.tb_folders.textbox.insert("end", "🔍 test_tblb injected this line\n")

    lb_widget = FilterListBox(master=row, items=[], popup_menu=None)
    register_widget("lb_files", lb_widget)
    app.lb_files = lb_widget  # ✅ Now assigned correctly
    app.lb_files.custom_name = "lb_files"
    app.lb_files.grid(row=0, column=2, sticky="nsew")

def build_bottom_row(app, tab, padding, config):
    from customtkinter import CTkLabel, CTkSegmentedButton, CTkCheckBox
    row = MyFrame(master=tab)
    row.grid(row=2, column=0, sticky="nsew")
    row.columnconfigure(list(range(10)), weight=1, uniform="Silent_Creme")
    row.rowconfigure(0, weight=1)
    app.last_row = row

    # 🧠 Shared state reference
    s = get_shared()

    # Drive Info Text + Progress
    status_slot = StatusSlot(row)
    status_slot.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    s.bottomrow_label = status_slot  # ✅ Set shared label reference

    # Segmented Button: Extensions
    CTkLabel(master=row, text="Extensions:    ", anchor="e").grid(
        row=0, column=4, padx=10, pady=10, sticky="nsew"
    )

    if s.segbut_var is None:
        s.segbut_var = tk.StringVar(value="Videos")

    app.segbut = CTkSegmentedButton(
        master=row,
        values=["Videos", "Subtitles", "All"],
        variable=s.segbut_var,
        command=lambda value: apply_segment_filter()
    )
    app.segbut.grid(row=0, column=5, columnspan = 2, sticky="ew")
    app.segbut.set(s.segbut_var.get())
    apply_segment_filter()

    # Include Subdirectories
    #print("CONFIG:", config)
    #print("persistent_cfg:", config.get("persistent_cfg"))
    s.inc_subs_var = tk.BooleanVar(value=config["persistent_cfg"].get("Inc_subdirs", True))
    app.inc_subdirs_var = s.inc_subs_var
    app.inc_subdirs = CTkCheckBox(
        master=row,
        text="Include Subdirs",
        variable=app.inc_subdirs_var,
        command=on_toggle
    )
    app.inc_subdirs.grid(row=0, column=7, **padding, sticky="ew")

    # Author Label
    app.lblAuth = CTkLabel(master=row, text="Author: Eddy Smesman", anchor="e")
    app.lblAuth.grid(row=0, column=8, columnspan=2, **padding, sticky="ew")

    #for i in range(12):
    #    CTkLabel(row, text=f"Col {i}", fg_color="gray80").grid(row=1, column=i, padx=2, pady=2, sticky="ew")
    return row

def setup_settings_tab(app, tabview, padding, config):
    tabview.add("Settings")
    settings_tab = tabview.tab("Settings")

    app.setting_tab = settings_tab
    settings_tab.custom_name = "settings_tab"

    settings_tab.grid_columnconfigure(0, weight=1)
    settings_tab.grid_columnconfigure(1, weight=10)
    settings_tab.grid_rowconfigure(0, weight=1)

    from widgets.base_textbox import BaseTBox
    app.tb_settings = BaseTBox(settings_tab, name="tb_settings", show_scrollbar=False)
    app.tb_settings.custom_name = "tb_settings"
    app.tb_settings.grid(row=0, column=1, sticky="nsew")

    import customtkinter as ct
    left_scroll = ct.CTkScrollableFrame(master=settings_tab)
    left_scroll.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
    left_scroll.grid_rowconfigure(list(range(16)), weight=1)
    left_scroll.grid_columnconfigure((0, 1), weight=1)
    left_scroll.grid_columnconfigure(2, weight=10)

    app.config_frame = Config_Frame(left_scroll, config_data=config)
    app.config_frame.grid(row=0, column=0, sticky="nsew")



def setup_debug_tab(app, tabview, padding):
    tabview.add("Debug")
    debug_tab = tabview.tab("Debug")

    app.debug_tab = debug_tab
    debug_tab.custom_name = "debug_tab"

    debug_tab.grid_columnconfigure(0, weight=1)
    debug_tab.grid_columnconfigure(1, weight=10)
    debug_tab.grid_rowconfigure(0, weight=1)

    from widgets.base_textbox import BaseTBox
    app.tb_debug = BaseTBox(debug_tab, name="tb_debug", show_scrollbar=False)
    app.tb_debug.custom_name = "tb_debug"
    app.tb_debug.grid(row=0, column=1, sticky="nsew")

    app.debug_frame = Debug_Frame(master=debug_tab)
    app.debug_frame.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
    
    # Force instance registration for debug output
    from widgets.base_textbox import BaseTBox
    BaseTBox.instances['tb_debug'] = app.tb_debug

