#-------------------------------------------------------------------------------
# Name:        debug_console_launcher.py
# Purpose:
#
# Author:      EddyS
#
# Created:     08/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct
from tkinter.scrolledtext import ScrolledText
import datetime
import traceback
import json
import os

class DebugConsole(ct.CTkToplevel):
    def __init__(
        self, master=None, title="Debug Console", width=800, height=400,
        emoji_file="assets/emoji_styles.json", log_file="debug_log.txt", **kwargs
    ):
        super().__init__(master=master, **kwargs)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color="#1a1a1a")

        # Emblems & Event Tracking
        self.emblems = self._load_emblems(emoji_file)
        self.event_counter = {}
        self.active_keywords = []

        # Config & Flags
        self.verbose_var = ct.BooleanVar(value=True)
        self.print_only_var = ct.BooleanVar(value=False)
        self.trace_enabled_var = ct.BooleanVar(value=True)
        self.log_file = log_file
        self._recursing = False

        # Layout
        self._build_ui()

    def _load_emblems(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _build_ui(self):
        # Search
        self.search_frame = ct.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        self.search_frame.grid_columnconfigure((0, 1), weight=1)

        self.search_entry = ct.CTkEntry(self.search_frame, placeholder_text="Search log...")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.search_button = ct.CTkButton(self.search_frame, text="Find", command=self.search_logs)
        self.search_button.grid(row=0, column=1)

        # Options
        self.option_frame = ct.CTkFrame(self)
        self.option_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 2))
        self.option_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.keyword_entry = ct.CTkEntry(self.option_frame, placeholder_text="Comma-separated keywords")
        self.keyword_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.verbose_check = ct.CTkCheckBox(self.option_frame, text="Verbose", variable=self.verbose_var)
        self.verbose_check.grid(row=0, column=1)

        self.trace_check = ct.CTkCheckBox(self.option_frame, text="Stack Trace", variable=self.trace_enabled_var)
        self.trace_check.grid(row=0, column=2)

        self.clear_button = ct.CTkButton(self.option_frame, text="🧹 Clear", command=self.clear_console)
        self.clear_button.grid(row=0, column=3)

        # Textbox
        self.textbox = ScrolledText(self, bg="#111", fg="white", font=("Consolas", 10), wrap="none")
        self.textbox.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.textbox.config(state="disabled")
        self.textbox.tag_config("highlight", background="#444", foreground="#ff0")

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def log(self, message, key_hint=None):
        if self._recursing:
            return
        self._recursing = True

        try:
            time_str = datetime.datetime.now().strftime("[%H:%M:%S]")
            emoji = self._match_emblem(key_hint)

            if key_hint:
                count = self.event_counter.get(key_hint, 0) + 1
                self.event_counter[key_hint] = count
                message += f" #{count}"

            full_msg = f"{time_str} {emoji} {message}"

            if self.verbose_var.get() or any(k in message for k in self.active_keywords):
                full_msg += f"\n"

            print(full_msg)

            if not self.print_only_var.get():
                self.textbox.config(state="normal")
                self.textbox.insert("end", full_msg + "\n")
                self.textbox.see("end")
                self.textbox.config(state="disabled")

            if self.log_file:
                try:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(full_msg + "\n")
                except Exception as e:
                    print(f"{time_str} ❌ File log failed: {e}")

        finally:
            self._recursing = False

    def log_trace(self, message, key_hint=None):
        if self.trace_enabled_var.get():
            stack = "".join(traceback.format_stack(limit=4))
            message += f"\n🔍 Stack trace:\n{stack}"
        self.log(message, key_hint=key_hint)

    def _match_emblem(self, key_hint):
        if not key_hint:
            return "🔧"
        key = key_hint.lower().strip()
        for emoji, description in self.emblems.items():
            if key in description.lower():
                return emoji
        return "🔧"

    def clear_console(self):
        self.textbox.config(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.config(state="disabled")

    def search_logs(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        self.textbox.tag_remove("highlight", "1.0", "end")
        self.textbox.config(state="normal")

        start = "1.0"
        while True:
            start = self.textbox.search(keyword, start, stopindex="end")
            if not start:
                break
            end = f"{start}+{len(keyword)}c"
            self.textbox.tag_add("highlight", start, end)
            start = end

        self.textbox.config(state="disabled")

    def update_keywords(self):
        raw = self.keyword_entry.get()
        self.active_keywords = [kw.strip() for kw in raw.split(",") if kw.strip()]
        self.log(f"📌 Keywords updated: {', '.join(self.active_keywords)}", key_hint="Config log")

""" usage
from utils.debug_console import DebugConsole

ctx.debug_console.log("Something happened", key_hint="info")
ctx.debug_console.log_trace("Something with trace", key_hint="debug")
"""