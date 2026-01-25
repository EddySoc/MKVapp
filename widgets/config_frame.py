#-------------------------------------------------------------------------------
# Name:        config_frame.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct
import os
from shared_data import get_shared, get_config

class Config_Frame(ct.CTkFrame):
    def __init__(self, master, config_mgr=None, config_data=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_mgr = config_mgr or get_shared().config_mgr  # ✅ fallback to shared
        self.config_data = config_data or self.config_mgr.data
        #print(f"config_data: {config_data}")
        self.cfg = self.config_data.get("persistent_cfg", {})
        # [DEBUG] print verwijderd

        self.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self._load_config()
        self._create_vars()
        self._build_ui()
        self.after(0, self.update_preview)

    def _load_config(self):
        self.appear = self.config_data.get("appear_cfg", {})
        
        # Load tools config - try from config_data first, then from file
        self.tools_cfg = self.config_data.get("tools_cfg", {})
        
        # If not in config_data, load directly from file
        if not self.tools_cfg:
            import json
            config_file = os.path.join("Settings", "tools_cfg.json")
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        self.tools_cfg = json.load(f)
                    print(f"🔧 Loaded tools_cfg from file: {self.tools_cfg}")
            except Exception as e:
                print(f"⚠️ Error loading tools config: {e}")
                self.tools_cfg = {}
        else:
            print(f"🔧 Loaded tools_cfg from config_data: {self.tools_cfg}")
        
        # Access data directly from config_mgr.data
        lang_lst_data = self.config_mgr.data.get("lang_lst", {})
        freespace_data = self.config_mgr.data.get("freespace_cfg", {})
        
        # Extract the actual lists from the data
        self.langs = lang_lst_data.get("languages", []) if isinstance(lang_lst_data, dict) else []
        freespace_values = freespace_data.get("Min_Freespaces", []) if isinstance(freespace_data, dict) else []
        self.freespaces = [str(f) for f in freespace_values]
        
        # Fallback values if config loading fails
        if not self.langs:
            self.langs = ["dut", "eng", "fre", "ger", "spa", "ita", "por"]
        if not self.freespaces:
            self.freespaces = ["200", "150", "100", "90", "80", "70", "60", "50"]

        self.font_families = self.appear.get("font_families", [])
        self.font_sizes = self.appear.get("font_sizes", [])
        self.font_weights = self.appear.get("font_weights", [])
        self.themes = self.appear.get("themes", [])
        self.display_modes = self.appear.get("display_modes", ["windowed"])
        self.color_schemes = self.appear.get("color_schemes", [])
        self.font_styles = self.appear.get("font_styles", [])
        self.max_resolutions = ["720p", "1080p", "1440p", "2160p"]

    def _create_vars(self):
        self.family_var = ct.StringVar(value=self.cfg.get("Font_family", self._first(self.font_families)))
        self.size_var = ct.StringVar(value=str(self.cfg.get("Font_size", self._first(self.font_sizes))))
        self.weight_var = ct.StringVar(value=self.cfg.get("Font_weight", self._first(self.font_weights)))
        self.theme_var = ct.StringVar(value=self.cfg.get("Theme", "dark"))
        self.display_mode_var = ct.StringVar(value=self.cfg.get("Display_Mode", "windowed"))
        self.lang_var = ct.StringVar(value=self.cfg.get("Language", self._first(self.langs)))
        self.freespace_var = ct.StringVar(value=str(self.cfg.get("Min_Freespace", self._first(self.freespaces))))
        self.method_var = ct.StringVar(value=self.cfg.get("SubtitleMethod", "api"))
        self.max_resolution_var = ct.StringVar(value=self.cfg.get("Max_Resolution", "1080p"))
        
        # Tool paths
        ffmpeg_path = self.tools_cfg.get("ffmpeg_path", "")
        ffprobe_path = self.tools_cfg.get("ffprobe_path", "")
        mkvtoolnix_path = self.tools_cfg.get("mkvtoolnix_path", "")
        videoplayer_path = self.tools_cfg.get("videoplayer_path", "")
        
        print(f"🔍 Creating vars - ffmpeg: '{ffmpeg_path}', ffprobe: '{ffprobe_path}', mkv: '{mkvtoolnix_path}'")
        
        self.ffmpeg_path_var = ct.StringVar(value=ffmpeg_path)
        self.ffprobe_path_var = ct.StringVar(value=ffprobe_path)
        self.mkvtoolnix_path_var = ct.StringVar(value=mkvtoolnix_path)
        self.videoplayer_path_var = ct.StringVar(value=videoplayer_path)

    def _build_ui(self):
        self._build_option("Language", self.langs, self.lang_var, 0, "Language")
        ct.CTkLabel(self, text="").grid(row=1, column=0, columnspan=2)

        self._build_option("Font Family", self.font_families, self.family_var, 2, "Font_family")
        self._build_option("Font Size", self.font_sizes, self.size_var, 3, "Font_size")
        self._build_option("Font Weight", self.font_weights, self.weight_var, 4, "Font_weight")

        self.preview = ct.CTkTextbox(self, height=80)
        self.preview.insert("0.0", "The quick brown fox jumps over the lazy dog.")
        self.preview.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        ct.CTkLabel(self, text="").grid(row=6, column=0, columnspan=2)
        self._build_option("Theme", self.themes, self.theme_var, 7, "Theme")
        self._build_option("Display Mode", self.display_modes, self.display_mode_var, 8, "Display_Mode")

        ct.CTkLabel(self, text="").grid(row=9, column=0, columnspan=2)
        self._build_option("Min Free Space", self.freespaces, self.freespace_var, 10, "Min_Freespace")
        self._build_option("Max Resolution", self.max_resolutions, self.max_resolution_var, 11, "Max_Resolution")

        ct.CTkLabel(self, text="").grid(row=12, column=0, columnspan=2)
        self._build_subtitle_method_options(start_row=13)
        
        ct.CTkLabel(self, text="").grid(row=15, column=0, columnspan=2)

        # Voeg BaseDir widget toe vóór de externe tools
        self._build_basedir_row(row=16)
        self._build_tool_paths_section(start_row=17)

    def _build_basedir_row(self, row):
        import os, json
        from tkinter import filedialog
        # Altijd direct uit actuele persistent_cfg.json lezen
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        persistent_path = os.path.join(base_dir, "Settings", "persistent_cfg.json")
        persistent_path = os.path.normpath(persistent_path)
        basedir_val = r"C:/QBMedia"
        try:
            if os.path.exists(persistent_path):
                with open(persistent_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                basedir_val = data.get("BaseDir", r"C:/QBMedia")
        except Exception:
            pass
        # [DEBUG] print verwijderd
        self.basedir_var = ct.StringVar()

        ct.CTkLabel(self, text="BaseDir:", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        frame = ct.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        frame.columnconfigure(0, weight=1)

        entry = ct.CTkEntry(frame, width=300)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        entry.delete(0, "end")
        entry.insert(0, basedir_val)

        def update_entry(*args):
            entry.delete(0, "end")
            entry.insert(0, self.basedir_var.get())
        self.basedir_var.trace_add("write", update_entry)

        def browse():
            path = filedialog.askdirectory(title="Select BaseDir", initialdir=entry.get() or r"C:/QBMedia")
            if path:
                self.basedir_var.set(path)
                entry.update()
                save_basedir(path)

        def save_basedir(path):
            # Save to persistent_cfg.json in the correct project_root_portable/Settings folder
            try:
                if os.path.exists(persistent_path):
                    with open(persistent_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = {}
                data["BaseDir"] = path
                with open(persistent_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                # [DEBUG] print verwijderd
            except Exception as e:
                print(f"⚠️ Kan BaseDir niet opslaan: {e}")

        browse_btn = ct.CTkButton(frame, text="📁", width=40, command=browse)
        browse_btn.grid(row=0, column=1)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)

    def _build_option(self, label, values, var, row, key, width=150):
        ct.CTkLabel(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)

        def on_change(value):
            from utils import log_settings
            self.cfg[key] = value
            log_settings(f"✅ {label}: {value}")

            if label.startswith("Font"):
                self.update_preview()
                try:
                    self.master.filter_listbox.apply_shared_font()
                except AttributeError:
                    pass
            elif label == "Theme":
                ct.set_appearance_mode(value)
            elif label == "Display Mode":
                self._apply_display_mode(value)

        dropdown = ct.CTkOptionMenu(
            self,
            values=values,
            variable=var,
            width=width,
            command=on_change
        )
        dropdown.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        
        # Ensure the current value is in the list
        if var.get() not in values and values:
            var.set(values[0])

    def _build_subtitle_method_options(self, start_row):
        ct.CTkLabel(self, text="Subtitle Method").grid(row=start_row, column=0, sticky="w", padx=5, pady=5)

        def save_method():
            from utils import log_settings
            method = self.method_var.get()
            self.cfg["SubtitleMethod"] = method
            method_name = "FileBot" if method == "filebot" else "OpenSubtitles API"
            log_settings(f"✅ Subtitle method: {method_name}")

        ct.CTkRadioButton(
            self, text="FileBot", variable=self.method_var,
            value="filebot", command=save_method
        ).grid(row=start_row, column=1, sticky="w", padx=5)

        ct.CTkRadioButton(
            self, text="OpenSubtitles API", variable=self.method_var,
            value="api", command=save_method
        ).grid(row=start_row + 1, column=1, sticky="w", padx=5)
    
    def _build_tool_paths_section(self, start_row):
        """Build the external tools configuration section"""
        import os
        from tkinter import filedialog
        
        ct.CTkLabel(self, text="External Tools", font=("Arial", 12, "bold")).grid(
            row=start_row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5)
        )
        
        def build_path_row(label, var, row, config_key, is_directory=True):
            ct.CTkLabel(self, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=2
            )
            
            frame = ct.CTkFrame(self, fg_color="transparent")
            frame.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            frame.columnconfigure(0, weight=1)
            
            entry = ct.CTkEntry(frame, width=300)
            entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
            
            # Set initial value explicitly
            initial_value = var.get()
            if initial_value:
                entry.delete(0, "end")
                entry.insert(0, initial_value)
            
            # Bind var to entry for updates
            def update_entry(*args):
                entry.delete(0, "end")
                entry.insert(0, var.get())
            
            var.trace_add("write", update_entry)
            
            def browse():
                from utils import log_settings
                if is_directory:
                    path = filedialog.askdirectory(title=f"Select {label} Directory")
                else:
                    path = filedialog.askopenfilename(
                        title=f"Select {label}",
                        filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
                    )
                
                if path:
                    var.set(path)
                    entry.update()  # Force update
                    save_tool_path(config_key, path, label)
            
            def save_tool_path(key, path, label_text):
                from utils import log_settings
                import json
                
                self.tools_cfg[key] = path
                
                # Save to file
                config_file = os.path.join("Settings", "tools_cfg.json")
                try:
                    with open(config_file, 'w') as f:
                        json.dump(self.tools_cfg, f, indent=4)
                    log_settings(f"✅ {label_text}: {path}")
                except Exception as e:
                    print(f"❌ Error saving tools config: {e}")
            
            browse_btn = ct.CTkButton(frame, text="📁", width=40, command=browse)
            browse_btn.grid(row=0, column=1)
        
        build_path_row("FFmpeg", self.ffmpeg_path_var, start_row + 1, "ffmpeg_path")
        build_path_row("FFprobe", self.ffprobe_path_var, start_row + 2, "ffprobe_path")
        build_path_row("MKVToolNix", self.mkvtoolnix_path_var, start_row + 3, "mkvtoolnix_path")
        build_path_row("Video Player", self.videoplayer_path_var, start_row + 4, "videoplayer_path", is_directory=False)

    def _apply_display_mode(self, value):
        self.cfg["Display_Mode"] = value
        print(f"✅ Display Mode set to {value}")

        root = self.winfo_toplevel()
        if value == "fullscreen":
            root.overrideredirect(False)
            root.attributes("-fullscreen", True)
        elif value == "borderless":
            root.attributes("-fullscreen", False)
            root.overrideredirect(True)
            root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        else:
            root.attributes("-fullscreen", False)
            root.overrideredirect(False)
            root.geometry("1250x700")

    def update_preview(self, *_):
        s = get_shared()
        family = self.family_var.get()
        size_str = self.size_var.get()
        if size_str.isdigit():
            size = int(size_str)
        else:
            size = 12  # or any sensible default
        weight = self.weight_var.get().strip().lower()
        if weight not in ("normal", "bold"):
            weight = "normal"  # fallback to safe default

        s.TK_FONT.configure(family=family, size=size, weight=weight)
        s.CTK_FONT.configure(family=family, size=size, weight=weight)

        for flb in s.all_filterboxes:
            flb.apply_shared_font()

        self.preview.configure(font=s.CTK_FONT)
        ct.set_appearance_mode(self.theme_var.get())

    def _first(self, lst):
        return lst[0] if lst else ""