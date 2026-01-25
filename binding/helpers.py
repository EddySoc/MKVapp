#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     28/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding/helpers.py

import tkinter as tk
from shared_data import get_shared

def bind_widget(widget, name=None, popup=None, bindings=None, font=True, tooltip=None):
    shared = get_shared()

    if name:
        widget.custom_name = name

    if popup:
        widget.bind("<Button-3>", popup.on_right_click)

    if bindings:
        for event, handler in bindings:
            widget.bind(event, handler)

    if font and hasattr(shared, "CTK_FONT"):
        try:
            widget.configure(font=shared.CTK_FONT)
        except Exception as e:
            print(f"⚠️ Couldn't set font on {widget}: {e}")

    if tooltip:
        add_tooltip(widget, tooltip)

def add_tooltip(widget, text):
    def show_tip(event):
        widget.tooltip_window = tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{event.x_root + 8}+{event.y_root + 8}")
        label = tk.Label(tw, text=text, background="lightyellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tip(event):
        if hasattr(widget, "tooltip_window"):
            widget.tooltip_window.destroy()
            del widget.tooltip_window

    widget.bind("<Enter>", show_tip)
    widget.bind("<Leave>", hide_tip)