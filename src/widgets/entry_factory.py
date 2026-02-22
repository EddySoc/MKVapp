#-------------------------------------------------------------------------------
# Name:        entry_factory.py
# Purpose:
#
# Author:      EddyS
#
# Created:     02/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# widgets/themed_entry.py

import customtkinter as ct
from customtkinter import get_appearance_mode
import tkinter as tk

class ThemedEntry(ct.CTkEntry):
    def __init__(self, parent, textvariable=None, placeholder="", validate=None, tooltip_text=None, **kwargs):
        theme = get_appearance_mode()
        fg_color = "white" if theme == "Light" else "#1a1a1a"
        text_color = "black" if theme == "Light" else "white"
        border_color = "cyan"

        super().__init__(
            parent,
            fg_color=fg_color,
            text_color=text_color,
            placeholder_text=placeholder,
            border_color=border_color,
            textvariable=textvariable,
            **kwargs
        )

        self.default_border = border_color

        self.default_border = fg_color
        self.focus_border = "orange"
        self.validate_func = validate
        self.tooltip_text = tooltip_text

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        if validate:
            self.bind("<KeyRelease>", self._validate)

        if tooltip_text:
            self._add_tooltip(tooltip_text)

    def _on_focus_in(self, event):
        self.configure(border_color=self.focus_border)

    def _on_focus_out(self, event):
        self.configure(border_color=self.default_border)

    def _validate(self, event):
        value = self.get()
        if self.validate_func:
            valid = self.validate_func(value)
            self.configure(border_color="green" if valid else "red")

    def _add_tooltip(self, text):
        def show_tip(e):
            self.tip_window = tw = tk.Toplevel(self)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")
            label = tk.Label(tw, text=text, bg="lightyellow", relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()

        def hide_tip(e):
            if hasattr(self, "tip_window") and self.tip_window:
                self.tip_window.destroy()
                self.tip_window = None

        self.bind("<Enter>", show_tip)
        self.bind("<Leave>", hide_tip)