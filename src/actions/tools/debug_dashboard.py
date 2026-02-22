#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     02/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import tkinter as tk
import customtkinter as ctk
import pyperclip
import sys
import os
from decorators.decorators import menu_tag

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "widgets")))

def entry_color_report(shared, output_widget=None):
    lines = ["🎨 Entry Color Report:"]
    for name, data in shared.entry_data.items():
        entry = data.get("entry")
        try:
            fg = entry.widget.cget("fg_color")
            txt = entry.widget.cget("text_color")
            inverted = entry.is_inverted
            lines.append(f"{name}: fg={fg}, text={txt}, inverted={inverted}")
        except Exception as e:
            lines.append(f"{name}: ⚠️ Error - {e}")
    dump_text(lines, output_widget)

def show_bindings(binding_manager, output_widget=None):
    """Show bindings and related popup actions for each registered widget."""
    from menus.popup import MENU_COMPOSITIONS, build_items_from_composition
    from menus.menu_registry import global_menu_registry
    # Also surface potential bindings from handlers
    from binding import handlers as binding_handlers

    lines = ["🔗 Binding Summary:"]
    # Show potential binding handlers first (helpful when no live bindings exist)
    lines.append("\n🔎 Potential Bindings (from binding.handlers):")
    try:
        lines.append(" - CTkEntry -> <FocusIn>, <Tab> => on_focus; <Double-Button-1> => on_browse")
        lines.append(" - BaseTBox -> <Button-3> => on_right_click; <ButtonRelease-1> => on_release")
        lines.append(" - CTkListbox -> <Button-3> => on_right_click")
    except Exception:
        pass

    if not binding_manager:
        lines.append("⚠️ No BindingManager available (shared.binding_manager is None).")
        lines.append("→ Ensure the app initialized the binding manager before opening this dashboard.")
        dump_text(lines, output_widget)
        return

    if not getattr(binding_manager, 'widget_menu_map', None):
        lines.append("(no registered widgets or bindings found)")
        dump_text(lines, output_widget)
        return

    # Aggregate by popup/group name so duplicates (multiple widgets with same name)
    # are merged and entries with bound events are shown first.
    aggregated = {}
    for widget, name in binding_manager.widget_menu_map.items():
        try:
            events = binding_manager.bindings.get(widget, [])
            bound_events = [e[0] for e in events]
        except Exception:
            bound_events = []

        entry = aggregated.setdefault(name, {"events": set(), "widgets": [], "menu_parts": None, "menu_items": None})
        entry["widgets"].append(widget)
        for ev in bound_events:
            entry["events"].add(ev)

    # Populate menu info per name (once) and filter out names with neither events nor menu
    names = list(aggregated.keys())
    for name in names:
        has_menu = False
        menu_parts = []
        menu_items = []
        try:
            if name in MENU_COMPOSITIONS:
                menu_parts = MENU_COMPOSITIONS.get(name, [])
                menu_items = build_items_from_composition(menu_parts, global_menu_registry)
                action_items = [it for it in menu_items if it.get("type") == "action"]
                has_menu = bool(action_items)
                menu_items = action_items
            else:
                labels = global_menu_registry.grouped().get(name, [])
                if labels:
                    collected = []
                    for label in labels:
                        entry_def = global_menu_registry.get(label)
                        if not entry_def:
                            continue
                        func = entry_def.get("func")
                        fname = func.__name__ if callable(func) else str(func)
                        collected.append((label, fname))
                    if collected:
                        has_menu = True
                        menu_items = collected
        except Exception as e:
            lines.append(f"  ⚠️ Error retrieving actions for '{name}': {e}")

        aggregated[name]["menu_parts"] = menu_parts
        aggregated[name]["menu_items"] = menu_items
        aggregated[name]["has_menu"] = has_menu

        # Remove entries with neither bound events nor menu/actions
        if not aggregated[name]["events"] and not has_menu:
            del aggregated[name]

    # Sort names so those with events appear first
    sorted_names = sorted(aggregated.keys(), key=lambda n: (0 if aggregated[n]["events"] else 1, n))

    for name in sorted_names:
        info = aggregated[name]
        bound_events = list(info["events"]) if info["events"] else []

        if bound_events:
            lines.append(f"{name}: {bound_events}")
        else:
            lines.append(f"{name}: []  (no bound events)")

        try:
            if info["menu_parts"]:
                lines.append(f"  Menu composition: {info['menu_parts']}")
                for it in info["menu_items"]:
                    func = it.get("func")
                    fname = func.__name__ if callable(func) else str(func)
                    lines.append(f"    • {it.get('label')} → {fname}")
            elif isinstance(info["menu_items"], list) and info["menu_items"] and isinstance(info["menu_items"][0], tuple):
                lines.append(f"  Actions in group '{name}':")
                for label, fname in info["menu_items"]:
                    lines.append(f"    • {label} → {fname}")
        except Exception as e:
            lines.append(f"  ⚠️ Error retrieving actions: {e}")

    dump_text(lines, output_widget)

def entry_state_to_clipboard(shared):
    lines = ["📋 Entry State:"]
    for name, data in shared.entry_data.items():
        entry = data.get("entry")
        try:
            fg = entry.widget.cget("fg_color")
            txt = entry.widget.cget("text_color")
            inverted = entry.is_inverted
            lines.append(f"{name}: fg={fg}, text={txt}, inverted={inverted}")
        except Exception as e:
            lines.append(f"{name}: ⚠️ {e}")
    pyperclip.copy("\n".join(lines))
    print("✅ Entry state copied to clipboard")

def show_color_preview(shared):
    preview = ctk.CTkToplevel()
    preview.title("SmartEntry Colors")
    preview.geometry("320x240")
    for name, data in shared.entry_data.items():
        entry = data["entry"]
        try:
            fg = entry.widget.cget("fg_color")
            txt = entry.widget.cget("text_color")
            label = ctk.CTkLabel(
                preview,
                text=name,
                fg_color=fg,
                text_color=txt
            )
            label.pack(fill="x", padx=6, pady=2)
        except Exception as e:
            ctk.CTkLabel(preview, text=f"{name}: ⚠️ {e}").pack()

def dump_text(lines, output_widget):
    text = "\n".join(lines)
    if output_widget:
        try:
            output_widget.delete("0.0", "end")
            output_widget.insert("0.0", text)
            output_widget.see("0.0")
        except Exception as e:
            print(f"⚠️ Failed to write to output widget: {e}")
    else:
        print(text)

def open_debug_dashboard(app, shared, binding_manager):
    dash = ctk.CTkToplevel()
    dash.title("🔗 Bindings Dashboard")
    dash.geometry("720x520")

    # Text area for output (theme-aware)
    try:
        from customtkinter import get_appearance_mode
        theme = get_appearance_mode()
    except Exception:
        theme = "Dark"

    output = ctk.CTkTextbox(dash, wrap="word", height=24)
    output.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    # Controls - refresh, copy, and attempt live scan/create BindingManager
    btn_frame = tk.Frame(dash)
    btn_frame.pack(fill="x", padx=10, pady=6)

    tk.Button(btn_frame, text="🔄 Refresh", command=lambda: show_bindings(shared.binding_manager, output)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="📋 Copy", command=lambda: copy_output(output)).pack(side="left", padx=5)
    def create_and_scan():
        try:
            from binding.manager import BindingManager
            mgr = None
            try:
                mgr = BindingManager.get_instance()
            except Exception:
                pass
            if mgr is None:
                mgr = BindingManager(app, shared.pop_menu)
                shared.binding_manager = mgr
            # Run scan phases to populate bindings
            try:
                mgr.scan_and_register(scan_known=True, build_tree=True, auto_register=False)
                mgr._bind_events()
            except Exception:
                pass
            show_bindings(shared.binding_manager, output)
        except Exception as e:
            output.insert("end", f"⚠️ Failed to create/scan BindingManager: {e}\n")

    tk.Button(btn_frame, text="⚙️ Create/Scan Bindings", command=create_and_scan).pack(side="left", padx=5)

    # If no binding manager yet, attempt to create and scan automatically
    if not getattr(shared, 'binding_manager', None):
        create_and_scan()
    else:
        show_bindings(shared.binding_manager, output)

def copy_output(widget):
    try:
        txt = widget.get("1.0", "end")
        pyperclip.copy(txt)
        print("✅ Bindings copied to clipboard")
    except Exception as e:
        print(f"⚠️ Copy failed: {e}")

@menu_tag(label="Bindings Dashboard",icon="🔗",group=["tb_debug"])
def launch_debug_tools(event=None):
    from shared_data import get_shared
    shared = get_shared()
    app = shared.app
    binding_manager = shared.binding_manager
    open_debug_dashboard(app, shared, binding_manager)

if __name__ == "__main__":
    import tkinter as tk
    from shared_utils import get_shared
    from binding.core import BindingManager  # Adjust if BindingManager is elsewhere

    root = tk.Tk()
    root.title("Debug Dashboard Launcher")
    root.geometry("300x100")

    shared = get_shared()
    app = root  # use root as your dummy 'app'
    binding_manager = BindingManager(app, popup_menu=None)  # you can pass None if not needed

    tk.Button(root, text="🧪 Launch Dashboard", command=lambda: open_debug_dashboard(app, shared, binding_manager)).pack(pady=20)

    root.mainloop()


