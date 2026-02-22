#-------------------------------------------------------------------------------
# Name:        handlers.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding/handlers.py

from utils.scan_helpers import browse_folder, focusin_handler

# Widget-type specific binding functions
def bind_ctk_entry(bindings, widget, name, on_focus, on_browse):
    widget.custom_name = name
    bindings[widget] = [
        ("<FocusIn>", on_focus),
        ("<Tab>", on_focus),
        ("<Double-Button-1>", on_browse)
    ]

def bind_basetbox(bindings, wrapper, name, on_right_click=None, on_release=None):
    textbox = getattr(wrapper, "textbox", None)

    if not textbox:
        print(f"⚠️ No textbox found in wrapper: {wrapper}")
        return

    # Assign name to the inner textbox directly
    textbox.custom_name = name
    bindings[textbox] = []

    # Attach event bindings if provided
    if on_right_click:
        bindings[textbox].append(("<Button-3>", on_right_click))
    if on_release:
        bindings[textbox].append(("<ButtonRelease-1>", on_release))

    # Debug log for manual right-click test
    #print(f"🧬 Binding BaseTBox inner textbox '{name}': {textbox}")
    textbox.bind("<Button-3>", lambda e: print(f"📢 Right-click inside '{name}'!"))

def bind_listbox(bindings, widget, name, on_right_click):
    widget.custom_name = name
    bindings[widget] = [("<Button-3>", on_right_click)]

"""
def bind_all_right_clicks(widget):
    widget.bind("<Button-3>", lambda e: print(f"👉 Right-click hit: {widget}"))
    for child in widget.winfo_children():
        bind_all_right_clicks(child)
"""