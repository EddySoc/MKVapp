#-------------------------------------------------------------------------------
# Name:        base_textbox.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import shared_data,os,re
# Lazy import: from shared_data import get_shared, get_config

import tkinter as tk
from tkinter import ttk

# Attempt to read CTk theme mode; fall back to Dark if not available
try:
    from customtkinter import get_appearance_mode
except Exception:
    def get_appearance_mode():
        return "Dark"

class BaseTBox(tk.Frame):
    instances = {}
    counter = 0

    def __init__(self, master=None, name="default", show_scrollbar=False, tag_config=None, config_mgr=None, **kwargs):
        super().__init__(master)
        from shared_data import get_shared
        self.name = name
        self.s = get_shared()
        self.config_mgr = config_mgr or self.s.config_mgr  # ✅ fallback to shared if not passed
        self.config = self.config_mgr.data if self.config_mgr else {}

        #self.highlight_words = self.s.config_mgr.get("highlight_cfg", default={})
        self.highlight_words = self.config.get("highlight_words", {})
        #print("🔍 highlight_words:", self.highlight_words)
        BaseTBox.instances[name] = self
        BaseTBox.counter += 1
        from utils.debug_logger import debug_print
        debug_print(f"🆕 BaseTBox instance #{BaseTBox.counter} created with name: {name}", "instantie")


        # Shared font
        s = get_shared()
        font = getattr(s, "TK_FONT", ("Consolas", 10))

        # Create textbox with theme-aware colors
        theme = get_appearance_mode() or "Dark"
        if str(theme).lower().startswith("dark"):
            tb_bg = "black"
            tb_fg = "white"
            insert_bg = "white"
            highlight_bg = "cyan"
            border_color = "cyan"
        else:
            tb_bg = "white"
            tb_fg = "black"
            insert_bg = "black"
            highlight_bg = "gray"
            border_color = "gray"

        self.textbox = tk.Text(
            self,
            font=font,
            bg=tb_bg,
            fg=tb_fg,
            insertbackground=insert_bg,
            highlightbackground=border_color,
            highlightthickness=2,
            bd=2,
            relief="solid",
            **kwargs
        )
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.bind("<Button-1>", self.on_mouse_click)

        # Optional scrollbar
        if show_scrollbar:
            self.scrollbar = ttk.Scrollbar(self, command=self.textbox.yview)
            self.scrollbar.grid(row=0, column=1, sticky="ns")
            self.textbox.configure(yscrollcommand=self.scrollbar.set)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Allow room for search_frame or controls
        self.grid_columnconfigure(0, weight=1)

        # Load tag config from shared config
        self.config = self.config_mgr.data
        self.tagcfg = self.config.get("tags_cfg", {})
        self._register_tags()

    def _register_tags(self):
        # Ensure fallback tag exists
        theme = get_appearance_mode() or "Dark"
        default_fg = "white" if str(theme).lower().startswith("dark") else "black"
        if "normal" not in self.tagcfg:
            self.tagcfg["normal"] = {"foreground": default_fg}

        for tag, style in self.tagcfg.items():
            try:
                self.textbox.tag_config(tag, **style)
                # Optional debug log
                # print(f"✅ Registered tag '{tag}' with style {style}")
            except Exception as e:
                from utils.debug_logger import debug_print
                debug_print(f"⚠️ Failed to register tag '{tag}': {e}", "instantie")

    def _load_tag_config(self, cfg):
        # Step 1: Attempt to load tags_cfg from config_mgr.data
        config = get_config()
        tags_cfg = config.get("tags_cfg")

        # Optional: Only print if missing or in debug mode
        if tags_cfg is None:
            # You can comment this out or control it with a debug flag
            # print(f"[{self.__class__.__name__}] No 'tags_cfg' found in config_mgr.data")
            pass

        # Step 2: If cfg is missing, skip applying styles
        if not cfg:
            return

        # Step 3: Apply tag config
        self.tagcfg = cfg
        for tag, style in cfg.items():
            self.textbox.tag_config(tag, **style)

    def update_content(self, msg, default_tag="normal"):
        try:
            highlight_map = self.config.get("highlight_words", {})
            tag_styles = self.config.get("tags_cfg", {})
            smart_tags = self.config.get("smarttag_cfg", {})
            current_tag = default_tag

            for line in msg.split("\n"):
                current_tag = default_tag  # Reset per line
                words = line.split(" ")

                for word in words:
                    clean_word = word.strip(".,:;")

                    # Inline tag override like [error]
                    if word.startswith("[") and word.endswith("]"):
                        override_tag = word[1:-1]
                        if override_tag in tag_styles:
                            current_tag = override_tag
                        continue

                    # Step 1: Resolve tag from highlight_words
                    tag_from_word = highlight_map.get(clean_word, current_tag)

                    # Step 2: Get emoji from smarttag_cfg
                    emoji = smart_tags.get(tag_from_word, {}).get("icon", "")

                    # Step 3: Compose display word
                    display_word = f"{emoji} {word}" if emoji else word

                    # Step 4: Insert with resolved tag
                    self.textbox.insert("end", display_word + " ", tag_from_word)

                self.textbox.insert("end", "\n")

            self.textbox.see("end")

        except Exception as e:
            from utils.debug_logger import debug_print
            debug_print(f"⚠️ BaseTBox '{self.name}' update_content failed: {e}", "instantie")

    def insert_with_tags(self, msg, tag="normal"):
        self.update_content(msg, tag)

    def set_text(self, text, tag="normal"):
        self.textbox.delete("1.0", "end")
        self.textbox.insert("end", text, tag)
        self.textbox.see("end")

    def append_text(self, msg, tag="normal"):
        self.update_content(msg, default_tag=tag)

    def clear(self):
        #print(" clear initiated")
        try:
            current_state = self.textbox.cget("state")
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.configure(state=current_state)
        except Exception as e:
            from utils.debug_logger import debug_print
            debug_print(f"⚠️ Clear failed: {e}", "instantie")
            self.textbox.delete("1.0", "end")

    def clear_textbox(self, keep_search_controls=False):
        try:
            tb_name = getattr(self, "custom_name", self.winfo_name())
            # Remove search_frame only if not keeping controls
            if hasattr(self, 'search_frame') and not keep_search_controls:
                self.search_frame.destroy()
                delattr(self, 'search_frame')
            # Voorkom statusmelding bij clearen
            if tb_name == "tb_info":
                try:
                    from shared_data import clear_statusbar
                    clear_statusbar()
                except Exception:
                    pass
                self.show_status_on_empty = False
            self.clear_text(tb_name)
        except Exception as ex:
            from utils.debug_logger import debug_print
            debug_print(f"⚠️ Failed to clear textbox: {ex}", "instantie")

    def get(self, *args, **kwargs):
        return self.textbox.get("1.0", "end").strip()

    def on_mouse_click(self, event):
        widget = event.widget

        # Ensure shared accessor is available locally (prevents NameError later)
        from shared_data import get_shared
        s = get_shared()

        # 🔍 Get the index of the mouse click
        index = widget.index(f"@{event.x},{event.y}")
        if not index:
            from utils.debug_logger import debug_print
            debug_print("⚠️ No valid index found at click location.", "scan")
            return

        try:
            line_number = int(index.split(".")[0])
        except Exception as e:
            from utils.debug_logger import debug_print
            debug_print(f"💥 Failed to parse line number from index '{index}': {e}", "scan")
            return


        # 🔍 Get full line text
        line_text = widget.get(f"{line_number}.0", f"{line_number}.end").rstrip()
        from utils.debug_logger import debug_print
        debug_print(f"line_test = {line_text}", "scan")
        if not line_text.strip():
            debug_print("⚠️ Clicked line is empty or whitespace.", "scan")
            return

        # Check if clicked on [..] parent folder navigation (first line with up arrow)
        if "[..]" in line_text or (line_text.strip().startswith("⬆️") and line_number == 1):
            debug_print("⬆️ Clicked on parent folder navigation", "scan")
            try:
                from actions.tb_folders.folder_nav import go_to_parent_folder
                go_to_parent_folder()
            except Exception as e:
                debug_print(f"❌ Error navigating to parent: {e}", "scan")
            return

        # 🧹 Clean current line
        cleaned_line = re.sub(r"^[📁\s⬆️]*", "", line_text)
        cleaned_line = re.sub(r"/+$", "", cleaned_line).strip()

        # 🎯 Highlight clicked line
        widget.tag_remove("highlight", "1.0", "end")
        widget.tag_add("highlight", f"{line_number}.0", f"{line_number}.end")
        widget.tag_config("highlight", background="darkcyan", foreground="white")

        # 📂 Get base path from shared object
        base_path = getattr(s, "base_path", None)
        if not base_path:
            debug_print("⚠️ base_path is not set.", "scan")
            return

        # Normalize and validate base_path; try to auto-correct common duplicate-folder issue
        base_path = os.path.normpath(base_path)
        if not os.path.isdir(base_path):
            parts = base_path.split(os.sep)
            if len(parts) >= 2 and parts[-1] == parts[-2]:
                candidate = os.sep.join(parts[:-1])
                if os.path.isdir(candidate):
                    base_path = candidate
                    debug_print(f"🔧 Corrected base_path to: {base_path}", "scan")

        if not os.path.isdir(base_path):
            debug_print(f"🚫 base_path does not exist: {base_path}", "scan")
            return

        debug_print("📁 Folders in base_path:", "scan")
        try:
            for entry in os.listdir(base_path):
                debug_print(f"   - {entry}", "scan")
        except Exception as e:
            debug_print(f"⚠️ Error listing base_path '{base_path}': {e}", "scan")
            return

        # 🧠 Indentation-based parent detection
        def get_indent_level(text):
            return len(text) - len(text.lstrip(" "))

        clicked_indent = get_indent_level(line_text)
        parent_path = ""

        for i in range(line_number - 1, 0, -1):
            parent_line = widget.get(f"{i}.0", f"{i}.end").rstrip()

            if "📁" in parent_line:
                parent_indent = get_indent_level(parent_line)

                if parent_indent < clicked_indent:
                    # Clean the folder name
                    parent_clean = parent_line.strip()
                    parent_clean = re.sub(r"^[\s\-]*📁?\s*", "", parent_clean)
                    parent_clean = re.sub(r"/+$", "", parent_clean).strip()

                    # Skip if it's the base folder name
                    if parent_clean == os.path.basename(base_path):
                        continue

                    parent_path = parent_clean
                    break

        # 🧱 Build full path
        # First try to use folder_path_map for accurate mapping
        folder_key = line_text.strip()
        full_path = None
        
        if hasattr(s, 'folder_path_map'):
            # Try exact match first
            if folder_key in s.folder_path_map:
                full_path = s.folder_path_map[folder_key]
                debug_print(f"✅ Using folder_path_map (exact): '{folder_key}' -> '{full_path}'", "scan")
        
        # If no exact match, try to find in actual directory
        if not full_path:
            search_dir = os.path.join(base_path, parent_path) if parent_path else base_path
            search_dir = os.path.normpath(search_dir)
            
            if os.path.isdir(search_dir):
                print(f"🔍 Searching in directory: {search_dir}")
                # Look for folders that match the cleaned_line
                try:
                    best_match = None
                    best_match_score = 0
                    
                    for entry in os.listdir(search_dir):
                        entry_path = os.path.join(search_dir, entry)
                        if os.path.isdir(entry_path):
                            # Exact match - highest priority
                            if entry == cleaned_line:
                                full_path = entry_path
                                debug_print(f"✅ Found exact match: '{cleaned_line}'", "scan")
                                break
                            
                            # Fuzzy match - check if entry contains all the key parts
                            # Remove brackets and split into words
                            cleaned_words = cleaned_line.replace('[', ' ').replace(']', ' ').replace('(', ' ').replace(')', ' ').split()
                            entry_lower = entry.lower()
                            
                            # Count how many words from cleaned_line appear in entry
                            matches = sum(1 for word in cleaned_words if len(word) > 2 and word.lower() in entry_lower)
                            match_ratio = matches / len(cleaned_words) if cleaned_words else 0
                            
                            # If most words match and starts similarly, it's likely the right folder
                            if match_ratio > 0.7 and entry.startswith(cleaned_line[:15]):
                                if match_ratio > best_match_score:
                                    best_match = entry_path
                                    best_match_score = match_ratio
                    
                    if best_match and not full_path:
                        full_path = best_match
                        debug_print(f"✅ Found fuzzy match (score {best_match_score:.2f}): '{cleaned_line}' -> '{os.path.basename(best_match)}'", "scan")
                        
                except Exception as e:
                    debug_print(f"⚠️ Error searching directory: {e}", "scan")
        
        # Fallback to constructing path manually if no match found
        if not full_path:
            if parent_path:
                full_path = os.path.normpath(os.path.join(base_path, parent_path, cleaned_line))
            else:
                full_path = os.path.normpath(os.path.join(base_path, cleaned_line))

        debug_print(f"🔍 line_text: '{line_text}'", "scan")
        debug_print(f"🔍 base_path: '{base_path}'", "scan")
        debug_print(f"🔍 cleaned_line: '{cleaned_line}'", "scan")
        debug_print(f"🔍 parent_path: '{parent_path}'", "scan")
        debug_print(f"🔍 full_path: '{full_path}'", "scan")

        if not os.path.exists(full_path):
            debug_print(f"🚫 Path does not exist: {full_path}", "scan")
            return

        debug_print(f"📂 Scanning: {full_path}", "scan")

        # 🚀 Use fast_scandir to scan and update lb_files
        try:
            from utils import fast_scandir
            
            # Update base_path to the new folder location
            if os.path.isdir(full_path):
                s.base_path = full_path
                debug_print(f"✅ Updated base_path to: {full_path}", "scan")
                
                # 🔄 Update SmartEntry with the new path (same logic as folder_nav.py)
                last_entry_name = getattr(s, "last_entry_name", "source")  # Fallback to "source"
                if last_entry_name in s.entry_data:
                    entry_obj = s.entry_data[last_entry_name]["entry"]
                    if entry_obj:
                        if hasattr(entry_obj, "set_value"):
                            entry_obj.set_value(full_path)
                        elif hasattr(entry_obj, "var") and entry_obj.var:
                            entry_obj.var.set(full_path)
                        # Sync naar config
                        s.config_mgr.get_all()["persistent_cfg"][last_entry_name] = full_path
                        debug_print(f"✅ Updated SmartEntry '{last_entry_name}' to: {full_path}", "scan")
                    else:
                        debug_print("⚠️ entry_obj is None", "scan")
                else:
                    debug_print(f"⚠️ {last_entry_name} not in entry_data", "scan")

            fast_scandir(s.app, full_path)

            from utils import update_lb
            update_lb(s.app)

            debug_print(f"✅ fast_scandir completed for: {full_path}", "scan")
            debug_print(f"📦 {len(s.upd_lst)} files ready for display.", "scan")
        except Exception as e:
            debug_print(f"💥 Failed to scan files with fast_scandir: {e}", "scan")

    @classmethod
    def update_text(cls, name, msg, tags="normal"):
        if name in cls.instances:
            cls.instances[name].insert_with_tags(msg, tag=tags)
            cls.instances[name].textbox.see("end")

    @classmethod
    def clear_text(cls, name):
        if name in cls.instances:
            tb = cls.instances[name]
            try:
                current_state = tb.textbox.cget("state")
                tb.textbox.configure(state="normal")
                tb.textbox.delete("1.0", "end")
                tb.textbox.configure(state=current_state)
                from utils.debug_logger import debug_print
                debug_print(f"🧹 Cleared {name} (state: {current_state})", "instantie")
            except Exception as e:
                from utils.debug_logger import debug_print
                debug_print(f"⚠️ Clear failed for {name}: {e}", "instantie")
                tb.textbox.delete("1.0", "end")