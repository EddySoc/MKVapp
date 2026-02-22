#-------------------------------------------------------------------------------
# Name:        events.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding/events.py

def handle_focus_in(shared, event):
    widget = event.widget
    for name, data in shared.entry_data.items():
        if widget._name == data["name"]:
            print(f"✅ Focus detected on: {name}")
            shared.invert_entries(widget)
            return

def handle_focus_out(event, label):
    print(f"🌘 FocusOut detected on {label} -> {event.widget}")

def print_all_widget_bindings(app):
    for widget in app.winfo_children():
        bindings = widget.bind_class(widget.winfo_class())
        bindings = bindings[0] if isinstance(bindings, tuple) and bindings else bindings
        print(f"{widget}:")
        print(bindings or "⛔ No bindings")
        print("-" * 40)

def track_focus(event):
    import customtkinter as ct
    widget = event.widget
    entry_like = widget.master if isinstance(widget.master, ct.CTkEntry) else widget
    print(f"👁️ Focused: {entry_like}")
    return entry_like