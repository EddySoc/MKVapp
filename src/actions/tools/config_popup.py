#-------------------------------------------------------------------------------
# Name:        actions_config_popup.py
# Purpose:
#
# Author:      EddyS
#
# Created:     03/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct
import tkinter as tk
import json, os, re
from decorators.decorators import menu_tag

class ConfigPopup(ct.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("🛠️ Configuration Editor")
        self.geometry("580x560+120+120")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.match_results = []
        self.match_index = -1
        self.view_all_active = False

        from shared_data import get_shared
        self.shared = get_shared()
        config = self.shared.config
        self.option_menu_main = ct.CTkOptionMenu(
            self,
            values=list(config.keys()),
            command=self.update_subkey_menu
        )
        self.option_menu_main.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.option_menu_sub = ct.CTkOptionMenu(self, values=[], command=self.update_textbox)
        self.option_menu_sub.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.entry_filter = ct.CTkEntry(self, placeholder_text="Search keyword, hit Enter")
        self.entry_filter.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.entry_filter.bind("<Return>", self.apply_filter)

        self.tb_config = tk.Text(
            self,
            wrap="word",
            bg="#1a1a1a",
            fg="#eaeaea",
            insertbackground="#ffffff",
            font=("Consolas", 10)
        )
        self.tb_config.grid(row=4, column=0, padx=10, pady=5, sticky="nsew")
        self.tb_config.tag_config("readonly", foreground="#80aaff")  # blue keys
        self.tb_config.tag_config("value", foreground="#ffffff")     # white values
        self.tb_config.tag_bind("readonly", "<Key>", lambda e: "break")

        # Lijn 1: Allow Save, Previous, Next
        line1_frame = ct.CTkFrame(self)
        line1_frame.grid(row=5, column=0, padx=10, pady=(0, 4), sticky="ew")
        line1_frame.grid_columnconfigure(1, weight=1)

        self.allow_save = ct.CTkCheckBox(line1_frame, text="Allow Save")
        self.allow_save.grid(row=0, column=0, sticky="w", padx=(5, 15))

        self.label_match_count = ct.CTkLabel(line1_frame, text="Matches: 0")
        self.label_match_count.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ct.CTkButton(line1_frame, text="⏮ Prev", width=80, command=self.goto_prev_match).grid(row=0, column=2, padx=5)
        ct.CTkButton(line1_frame, text="⏭ Next", width=80, command=self.goto_next_match).grid(row=0, column=3, padx=5)

        # Lijn 2: View All, Delete en Add op één lijn
        self.line2_frame = ct.CTkFrame(self)
        self.line2_frame.grid(row=6, column=0, padx=10, pady=(0, 4), sticky="ew")
        self.line2_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.btn_view_all = ct.CTkButton(self.line2_frame, text="👀 View All (Off)", command=self.toggle_view_all)
        self.btn_view_all.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ct.CTkButton(self.line2_frame, text="❌ Delete", command=self.delete_key).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ct.CTkButton(self.line2_frame, text="➕ Add", command=self.add_key).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Lijn 3: Default template dropdown
        line3_frame = ct.CTkFrame(self)
        line3_frame.grid(row=7, column=0, padx=10, pady=(0, 4), sticky="ew")
        
        ct.CTkLabel(line3_frame, text="Template:").grid(row=0, column=0, sticky="w", padx=(5, 10))
        self.add_template = ct.CTkOptionMenu(line3_frame, values=["Default", "MenuItem", "Theme", "API"])
        self.add_template.set("Default")
        self.add_template.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        line3_frame.grid_columnconfigure(1, weight=1)

        # Restore Backup button
        ct.CTkButton(self, text="♻️ Restore Backup", command=self.restore_config).grid(
            row=8, column=0, padx=10, pady=(0, 5), sticky="ew"
        )
        ct.CTkButton(self, text="❌ Close", command=self.on_close).grid(
            row=9, column=0, padx=10, pady=(0, 5), sticky="ew"
        )
        config = self.shared.config
        default_key = list(config.keys())[0]
        self.option_menu_main.set(default_key)
        self.update_subkey_menu(default_key)

    def update_subkey_menu(self, key):
        config = self.shared.config
        section = config.get(key, {})
        
        # Als View All actief is, toon alles en disable de 2e dropdown
        if self.view_all_active:
            self.option_menu_sub.configure(values=["All"], state="disabled")
            self.option_menu_sub.set("All")
            self.show_all_items_for_section(key)
            return
        
        # Normale werking
        self.option_menu_sub.configure(state="normal")
        if isinstance(section, dict):
            subkeys = list(section.keys())
            self.option_menu_sub.configure(values=subkeys or ["<empty>"])
            self.option_menu_sub.set(subkeys[0] if subkeys else "<empty>")
            self.update_textbox(subkeys[0] if subkeys else "<empty>")
        else:
            self.option_menu_sub.configure(values=["<root>"])
            self.option_menu_sub.set("<root>")
            self.update_textbox("<root>")

    def update_textbox(self, subkey):
        config = self.shared.config
        main_key = self.option_menu_main.get()
        section = config.get(main_key, {})
        target = section if subkey == "<root>" else section.get(subkey, {})
        config_str = json.dumps(target, indent=4)
        self.tb_config.delete("1.0", "end")
        self.tb_config.insert("1.0", config_str)
        self.apply_readonly_tags()

    def apply_readonly_tags(self):
        self.tb_config.tag_remove("readonly", "1.0", "end")
        self.tb_config.tag_remove("value", "1.0", "end")

        key_pattern = re.compile(r'^(\s*)"([^"]+)":\s')
        lines = self.tb_config.get("1.0", "end-1c").splitlines()

        for i, line in enumerate(lines, start=1):
            match = key_pattern.match(line)
            if match:
                indent, key = match.groups()
                key_start = f"{i}.{len(indent)}"
                key_end = f"{i}.{len(indent) + len(key) + 2}"
                self.tb_config.tag_add("readonly", key_start, key_end)

                colon_index = line.find(":")
                value_start = f"{i}.{colon_index + 2}"
                self.tb_config.tag_add("value", value_start, f"{i}.end")

    def apply_filter(self, event=None):
        keyword = self.entry_filter.get().strip().lower()
        self.match_results = []
        self.match_index = -1

        if not keyword:
            self.label_match_count.configure(text="Matches: 0")
            return

        config = self.shared.config
        for main_key, section in config.items():
            try:
                if isinstance(section, dict):
                    for subkey, data in section.items():
                        flat = json.dumps(data).lower()
                        if keyword in flat:
                            self.match_results.append((main_key, subkey))
                else:
                    flat = json.dumps(section).lower()
                    if keyword in flat:
                        self.match_results.append((main_key, "<root>"))
            except Exception as e:
                print(f"⚠️ Skipped {main_key} due to error: {e}")

        total = len(self.match_results)
        self.label_match_count.configure(text=f"Matches: {total}")

        if total > 0:
            self.match_index = 0
            self.load_match_at_index(0)
        else:
            print(f"⚠️ No match found for '{keyword}'")

    def load_match_at_index(self, idx):
        main_key, subkey = self.match_results[idx]
        self.option_menu_main.set(main_key)
        self.update_subkey_menu(main_key)
        self.option_menu_sub.set(subkey)
        self.update_textbox(subkey)

    def goto_next_match(self):
        if not self.match_results:
            return
        self.match_index = (self.match_index + 1) % len(self.match_results)
        self.load_match_at_index(self.match_index)

    def goto_prev_match(self):
        if not self.match_results:
            return
        self.match_index = (self.match_index - 1) % len(self.match_results)
        self.load_match_at_index(self.match_index)

    def toggle_view_all(self):
        self.view_all_active = not self.view_all_active
        
        if self.view_all_active:
            # Activeer View All mode
            self.btn_view_all.configure(text="👀 View All (On)", border_color="orange", border_width=2)
            main_key = self.option_menu_main.get()
            self.update_subkey_menu(main_key)
        else:
            # Deactiveer View All mode - reset border naar default
            self.btn_view_all.configure(text="👀 View All (Off)", border_color=("#3B8ED0", "#1F6AA5"), border_width=0)
            main_key = self.option_menu_main.get()
            self.update_subkey_menu(main_key)
    
    def show_all_items_for_section(self, main_key):
        """Toon alle items van de gekozen configuratie sectie"""
        config = self.shared.config
        section = config.get(main_key, {})
        
        if isinstance(section, dict):
            display = section
        else:
            display = {main_key: section}
        
        config_str = json.dumps(display, indent=4)
        self.tb_config.delete("1.0", "end")
        self.tb_config.insert("1.0", config_str)
        self.apply_readonly_tags()

    def add_key(self):
        config = self.shared.config
        section_key = self.option_menu_main.get()
        subkey = self.option_menu_sub.get()
        section_data = config.get(section_key, {})
        target = section_data if subkey == "<root>" else section_data.get(subkey, {})

        # Ensure it's a list of dicts
        if not isinstance(target, list):
            print("🚫 Target is not a list. Cannot insert.")
            return
        if not target or not isinstance(target[0], dict):
            keys = ["new_key"]
        else:
            keys = list(target[0].keys())

        # Construct new object using detected keys
        new_block = {}
        for key in keys:
            new_block[key] = None if key == "event" else ""

        # Append to config_mgr.data
        target.append(new_block)
        self.update_textbox(subkey)  # Refresh display

        print(f"✅ Inserted new block into '{subkey}' with keys: {keys}")

    def delete_key(self):
        # Determine current cursor line
        line_index = self.tb_config.index("insert").split(".")[0]
        current_line = int(line_index)

        # Delete current line and apply updated tagging
        self.tb_config.delete(f"{current_line}.0", f"{current_line + 1}.0")
        self.apply_readonly_tags()
        print(f"❌ Deleted line {current_line}")

    def save_config(self):
        if not self.allow_save.get():
            print("🛑 Save blocked — Allow Save is off")
            return

        self.backup_config()

        main_key = self.option_menu_main.get()
        subkey = self.option_menu_sub.get()
        raw_text = self.tb_config.get("1.0", "end").strip()

        try:
            updated_data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON: {e}")
            return

    def backup_config(self):
        config = self.shared.config
        main_key = self.option_menu_main.get()
        subkey = self.option_menu_sub.get()
        section = config.get(main_key, {})
        target = section if subkey == "<root>" else section.get(subkey, {})

        try:
            with open("config_backup.json", "w", encoding="utf-8") as f:
                json.dump(target, f, indent=4)
            print("📥 Backup written to config_backup.json")
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")

    def restore_config(self):
        if not self.allow_save.get():
            print("🛑 Restore blocked — Allow Save is off")
            return

        try:
            with open("config_backup.json", "r", encoding="utf-8") as f:
                restored = json.load(f)
            self.tb_config.delete("1.0", "end")
            self.tb_config.insert("1.0", json.dumps(restored, indent=4))
            self.apply_readonly_tags()
            print("♻️ Restored backup into editor")
        except Exception as e:
            print(f"⚠️ Restore failed: {e}")

    def on_close(self):
        self.save_config()
        self.destroy()

@menu_tag(label="Check Config",icon="🔍",group=["tb_debug"])
def show_config_popup(master=None):
    ConfigPopup(master).grab_set()


