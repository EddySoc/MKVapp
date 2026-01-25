#-------------------------------------------------------------------------------
# Name:        popup.py
# Purpose:      This file contains your powerful Popup menu class
#               and dynamic menu execution system.
#               It depends on your config_mgr.data, dynamic imports,
#               and actions from other modules.
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# widgets/popup.py

import tkinter as tk
import importlib
import inspect
from logger_singleton import logger
from menus.menu_registry import global_menu_registry
from shared_data import shared
from pathlib import Path
import yaml,os
from menus.menu_yaml_exporter import generate_yaml_from_registry, write_yaml_to_settings
from menus.menu_yaml_exporter import load_menus_from_yaml

# Special menu layouts: order of items for each popup_key
# Keywords:
#   "__title__"  → insert the popup_key as a disabled title
#   "__sep__"    → insert a separator
#   any other string → treat as a registry group name
MENU_COMPOSITIONS = {
    "tb_info": ["__title__", "__sep__", "tb_info", "__sep__", "tbox", "help"],
    "tb_folders": ["__title__", "__sep__", "tb_folders", "__sep__", "tbox", "help"],
    "tb_debug": ["__title__", "__sep__", "tb_debug", "__sep__", "tools", "tbox", "help"],
    "tb_settings": ["__title__", "__sep__", "tb_settings", "__sep__", "tbox", "help"],
    # For lb_files we show videos and subtitles groups explicitly
    "lb_files": ["__title__", "__sep__", "videos", "__sep__", "subtitles", "__sep__", "lbox", "help"],

    # Add more popup_keys here as needed
}

def audit_menu_compositions(menu_compositions, registry, fail_on_error=False):
    print("\n📋 MENU COMPOSITION AUDIT")
    print("─────────────────────────")

    used_groups = set()
    errors_found = False

    for popup_key, parts in menu_compositions.items():
        print(f"\n🔍 Popup: {popup_key}")
        group_index = 0
        for part in parts:
            if part == "__title__":
                print(f"  🏷️  [TITLE] {popup_key}")
            elif part == "__sep__":
                print(f"  ────────────────")
            else:
                used_groups.add(part)
                labels = registry.grouped().get(part)

                # Handle missing group
                if labels is None:
                    if group_index == 0:
                        # Main group missing — create empty entry
                        print(f"  ⚠️ Group '{part}' is in composition but has no registered actions (main group — creating empty)")
                        registry.grouped()[part] = []
                    else:
                        print(f"  ❌ Group '{part}' is in composition but does NOT exist in registry")
                        errors_found = True
                    group_index += 1
                    continue

                # Handle empty group
                if not labels:
                    print(f"  ⚠️ Group '{part}' exists but has NO registered actions")
                    group_index += 1
                    continue

                print(f"  📂 Group '{part}':")
                seen_labels = set()
                for label in labels:
                    if label in seen_labels:
                        print(f"     ⚠️ Duplicate label '{label}' in group '{part}'")
                    seen_labels.add(label)

                    entry = registry.get(label)
                    if not entry:
                        print(f"     ❌ Missing registry entry for label '{label}'")
                        errors_found = True
                        continue
                    func_name = entry['func'].__name__
                    print(f"     • {label}  →  {func_name}")
                group_index += 1

    # Check for unused groups
    all_groups = set(registry.grouped().keys())
    unused_groups = all_groups - used_groups
    if unused_groups:
        print("\nℹ️ Unused groups in registry (not in any composition):")
        for g in sorted(unused_groups):
            print(f"   - {g}")

    print("\n✅ Menu composition audit complete.\n")

    if fail_on_error and errors_found:
        raise RuntimeError("Menu composition audit failed — see errors above.")

# Navigate up to project_root from current file (widgets/popup.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_DIR = PROJECT_ROOT / "Settings"
MENU_CONFIG_PATH = SETTINGS_DIR / "menus.yaml"

def get_validated_menu_config():
    if not os.path.exists(MENU_CONFIG_PATH):
        print(f"⚠️ menu_config.yaml not found at {MENU_CONFIG_PATH}")
        return {}

    with open(MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)
        #print(f"raw_cfg =  {raw_cfg}")

    try:
        return load_validated_menu_config(raw_cfg)
    except ValueError as e:
        print(f"❌ Invalid menu config: {e}")
        return {}

def load_validated_menu_config(cfg):
    keys = ["BASE_MENUS", "EXTRA_MENU_TARGETS", "EXTRA_SUBMENUS", "EXTRA_MENU_ACTIONS"]
    result = {}
    for key in keys:
        value = cfg.get(key, {})
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be a dictionary, got {type(value).__name__}")
        result[key] = value
    return result

def build_items_from_composition(parts, registry):
    items = []
    for part in parts:
        if part == "__title__":
            items.append({"type": "title"})
        elif part == "__sep__":
            items.append({"type": "separator"})
        else:
            group = registry.grouped().get(part, [])
            for label in group:
                entry = registry.get(label)
                if entry:
                    items.append({
                        "type": "action",
                        "label": label,
                        "func": entry["func"]
                    })
    return items

menu_cfg = get_validated_menu_config()
print("✅ Loaded EXTRA_MENU_TARGETS:", menu_cfg.get("EXTRA_MENU_TARGETS"))

BASE_MENUS = menu_cfg.get("BASE_MENUS", {})
EXTRA_MENU_TARGETS = menu_cfg.get("EXTRA_MENU_TARGETS", {})
EXTRA_SUBMENUS = menu_cfg.get("EXTRA_SUBMENUS", {})
EXTRA_MENU_ACTIONS = menu_cfg.get("EXTRA_MENU_ACTIONS", {})

def show_popmsg(message, event):
    popup = tk.Toplevel()
    popup.title("Message")
    popup.geometry(f"+{event.x_root}+{event.y_root}")
    popup.transient(event.widget.winfo_toplevel())
    popup.grab_set()

    tk.Label(popup, text=message, padx=10, pady=10).pack()
    tk.Button(popup, text="OK", command=popup.destroy).pack()

    popup.wait_window()

class Popup(tk.Menu):
    def __init__(self, master, resolver, action_lookup, **kwargs):
        self.s = kwargs.pop("shared_state", None)
        super().__init__(master, tearoff=0, **kwargs)
        self.resolver = resolver
        self.menus = {}                # Preloaded menu definitions
        self.action_lookup = action_lookup or {}
        self.action_metadata = {}      # Initialize action_metadata to prevent errors

        from shared_data import shared, get_shared,get_config
        self.s = get_shared()

    def on_right_click(self, event):
        widget = event.widget
        popup_key = getattr(widget, "custom_name", None)

        #  If widget has no custom_name, try to find a parent with one
        if not popup_key:
            current = widget
            max_depth = 10  # Prevent infinite loops
            while current and max_depth > 0:
                current = current.master if hasattr(current, 'master') else None
                if current and hasattr(current, 'custom_name'):
                    popup_key = current.custom_name
                    #  Skip internal frames with auto-generated names
                    #  Skip internal frames with auto-generated names
                    if popup_key and '_frame' not in popup_key and '_canvas' not in popup_key:
                        widget = current
                        break
                    else:
                        popup_key = None
                max_depth -= 1

        if not popup_key:
            print(f" Widget {widget} has no custom_name  skipping popup.")
            return

        self.show_popup(widget, event)

    def show_popup(self, widget, event):
        try:
            popup = tk.Menu(self.master, tearoff=0)
        except Exception as ex:
            print(f"❌ Could not create popup menu: {ex}")
            return

        # 🔍 Step 1: Resolve popup key from widget
        popup_key = getattr(widget, "custom_name", None)
        
        # If widget has no custom_name, try to find a parent with one
        if not popup_key:
            current = widget
            max_depth = 10  # Prevent infinite loops
            while current and max_depth > 0:
                current = current.master if hasattr(current, 'master') else None
                if current and hasattr(current, 'custom_name'):
                    popup_key = current.custom_name
                    # Skip internal frames with auto-generated names
                    if popup_key and '_frame' not in popup_key and '_canvas' not in popup_key:
                        widget = current
                        break
                    else:
                        popup_key = None
                max_depth -= 1
        
        # Fallback to widget name if no custom_name found
        if not popup_key:
            popup_key = widget.winfo_name()
        
        if popup_key not in MENU_COMPOSITIONS:
            print(f"⚠️ No MENU_COMPOSITIONS entry for '{popup_key}' — no popup shown")
            return

        # 💾 Store the right-clicked widget for menu actions
        from shared_data import get_shared
        s = get_shared()
        s.last_right_clicked_widget = widget

        print(f"✅ Popup key '{popup_key}' matched MENU_COMPOSITIONS — using custom layout")

        # 📦 Step 2: Build menu items from composition
        items = build_items_from_composition(MENU_COMPOSITIONS[popup_key], global_menu_registry)

        # 🍽 Step 3: Populate menu (header is already in MENU_COMPOSITIONS)
        self.current_menu_group = popup_key
        self.build_menu_entries(popup, items, self.action_metadata, popup_key)

        # ➕ Step 5: Inject flat extras
        if popup_key in EXTRA_MENU_TARGETS:
            popup.add_separator()
            for label, action_path in EXTRA_MENU_ACTIONS.items():
                try:
                    action = self.resolve_action(action_path)
                    popup.add_command(label=label, command=lambda a=action: a())
                    print(f"✅ Injected extra action: {label}")
                except Exception as ex:
                    print(f"⚠️ Skipped action '{label}': {ex}")

        # ➕ Step 6: Inject dynamic submenus (disabled for lb_files, uses __dynamic_filter__ instead)
        if popup_key != "lb_files":  # Skip submenu logic for lb_files
            submenu_prefix = f"{popup_key}/"
            
            # Get current extension filter mode
            s = shared
            current_mode = s.segbut_var.get() if hasattr(s, 'segbut_var') else "All"
            
            # First check MENU_COMPOSITIONS for submenus
            matching_submenus = {}
            for key in MENU_COMPOSITIONS:
                if key.startswith(submenu_prefix):
                    # Extract submenu name (e.g., "videos" from "lb_files/videos")
                    submenu_name = key.split("/")[-1].lower()
                    
                    # Filter based on current mode
                    if current_mode == "All":
                        matching_submenus[key] = MENU_COMPOSITIONS[key]
                    elif current_mode.lower() == submenu_name:
                        matching_submenus[key] = MENU_COMPOSITIONS[key]
            
            # Also check BASE_MENUS for backward compatibility
            for key in BASE_MENUS:
                if key.startswith(submenu_prefix) and key not in matching_submenus:
                    submenu_name = key.split("/")[-1].lower()
                    if current_mode == "All" or current_mode.lower() == submenu_name:
                        matching_submenus[key] = BASE_MENUS[key]

            if matching_submenus:
                popup.add_separator()
                for submenu_key, submenu_items in matching_submenus.items():
                    label = submenu_key.split("/")[-1].capitalize()
                    submenu = tk.Menu(popup, tearoff=0)
                    self.current_menu_group = submenu_key
                    self.build_menu_entries(submenu, submenu_items, global_menu_registry, popup_key=submenu_key)
                    popup.add_cascade(label=label, menu=submenu)
                    print(f"✅ Injected submenu: {submenu_key} → {label}")
            else:
                print(f"ℹ️ No submenus found for {popup_key}/...")

        # 🚀 Step 7: Display popup
        popup.post(event.x_root, event.y_root)
        
        # 🧹 Step 8: Schedule cleanup after menu action completes
        # Delay long enough for the callback to execute
        def cleanup_menu():
            try:
                popup.unpost()
                popup.destroy()
            except:
                pass
        
        # Wait 300ms before cleanup to allow menu action to complete
        self.master.after(300, cleanup_menu)

    def build_menu_entries(self, menu, entries, menu_registry, popup_key=None):
        # Check if we have a special composition for this popup_key
        if popup_key in MENU_COMPOSITIONS:
            registry = global_menu_registry

            def add_items_from_group(group_name):
                labels = registry.grouped().get(group_name, [])
                print(f"📦 Injecting group '{group_name}' with {len(labels)} labels")
                added = 0
                for label in labels:
                    entry = registry.get(label)
                    if not entry:
                        print(f"⚠️ No entry found for label '{label}' in group '{group_name}'")
                        continue
                    func = entry.get("func")
                    if not callable(func):
                        print(f"⚠️ Label '{label}' has non-callable func: {func}")
                        continue
                    print(f"✅ Adding menu item: {label}")
                    menu.add_command(label=label, command=func)
                    added += 1
                return added

            last_was_sep = False
            for part in MENU_COMPOSITIONS[popup_key]:
                if part == "__title__":
                    menu.add_command(
                        label=f"━━━ {popup_key.upper()} ━━━",
                        state="disabled",
                        foreground="#00BFFF",
                        font=("Segoe UI", 10, "bold")
                    )
                    last_was_sep = False
                elif part == "__sep__":
                    # Avoid adding consecutive separators
                    if not last_was_sep:
                        menu.add_separator()
                        last_was_sep = True
                    else:
                        # skip duplicate separator
                        continue
                elif part == "__dynamic_filter__":
                    # Add groups based on current extension filter
                    s = shared
                    current_mode = s.segbut_var.get() if hasattr(s, 'segbut_var') else "All"
                    
                    if current_mode == "Videos" or current_mode == "All":
                        add_items_from_group("videos")
                    
                    if current_mode == "Subtitles" or current_mode == "All":
                        if current_mode == "All":
                            menu.add_separator()
                        add_items_from_group("subtitles")
                else:
                    # adding a group may produce menu items; only reset sep flag if items were added
                    added = add_items_from_group(part)
                    if added:
                        last_was_sep = False

            return  # Skip generic builder for special layouts

        # --- fall back to your existing generic logic ---
        if hasattr(menu_registry, "all"):
            menu_registry = menu_registry.all()
        previous_section = None

        def validate_meta(meta, label, group):
            expected_types = {
                "tag": str,
                "symbol": str,
                "group": str,
                "icon": (str, type(None))
            }
            for key, expected in expected_types.items():
                value = meta.get(key)
                if not isinstance(value, expected):
                    print(f"⚠️ Unexpected meta type for '{key}' in group '{group}' (label: '{label}'): {type(value)}")

        for entry in entries:
            if isinstance(entry, dict):
                label = entry.get("label", "Unnamed")
                section = entry.get("section")

                if section and section != previous_section and previous_section is not None:
                    menu.add_separator()
                previous_section = section

                if "submenu" in entry:
                    submenu = tk.Menu(menu, tearoff=0)
                    self.build_menu_entries(submenu, entry["submenu"], menu_registry)
                    menu.add_cascade(label=label, menu=submenu)

                elif "action" in entry:
                    action_key = entry["action"]
                    callback = None
                    if isinstance(self.action_lookup, dict):
                        callback = self.action_lookup.get(action_key)
                    if not callback:
                        by_label = global_menu_registry.get(entry.get("label"))
                        if by_label:
                            callback = by_label.get("func")
                    if callback:
                        menu.add_command(label=label, command=callback)
                    else:
                        print(f"⚠️ No registered action for '{action_key}' (label: '{label}')")
                        menu.add_command(label=label, state="disabled")

            else:
                label = str(entry)
                group = getattr(self, "current_menu_group", None)
                entry_meta = global_menu_registry.get(label)
                if not entry_meta:
                    for lbl, e in global_menu_registry.all().items():
                        if e["func"].__name__ == label:
                            entry_meta = e
                            break
                if entry_meta and isinstance(entry_meta, dict):
                    validate_meta(entry_meta, label, group)
                    callback = entry_meta.get("func")
                else:
                    callback = None
                if callback:
                    menu.add_command(label=label, command=callback)
                else:
                    print(f"⚠️ No registered action for '{label}' in menu group '{group}'")
                    menu.add_command(label=label, command=lambda x=label: self.on_menu_select(x, "unknown"))

    def resolve_action(self, action_str):
        mod_path, func_name = action_str.rsplit('.', 1)
        mod = importlib.import_module(mod_path)
        return getattr(mod, func_name)

    def make_cb(self, entry):
        action_str = entry["action"]
        args = entry.get("args", [])
        try:
            func = self.resolve_action(action_str)
            def _inner():
                print(f"🚀 Executing {action_str}")
                func(*args)
            return _inner
        except Exception as ex:
            def _inner(ex=ex):
                print(f"❌ Failed to resolve '{action_str}': {ex}")
            return _inner
        # Optional: clean up references or visual elements
        self.s.pop_menu = None

    # 🎬 Selection handler
    def on_menu_select(self, label, popup_key):
        print(f"✅ Selected '{label}' from {popup_key} popup.")

    def merge_config_menus(self, config_menus):
        for popup_key, items in config_menus.items():
            static = BASE_MENUS.get(popup_key, [])
            dynamic = []

            if isinstance(items, list):
                dynamic = items
            elif isinstance(items, dict):
                dynamic = [{"label": label, "action": action} for label, action in items.items()]

            seen = set()
            combined = []
            for item in static + dynamic:
                label = item.get("label") if isinstance(item, dict) else item
                if label != "common" and label not in seen:
                    seen.add(label)
                    combined.append(item)

            BASE_MENUS[popup_key] = combined

    def build_action_registry(self,registry, menu_name):
        return {
            entry["func"].__name__: entry["func"]
            for entry in registry.get_entries_by_group(menu_name)
        }

    def inject_registry_actions(self, menu_registry):
        # Use the live registry
        shared_groups = menu_registry.discover_shared_groups()

        self.action_registry = {}
        for group in shared_groups:
            actions = menu_registry.build_action_registry(group)
            self.action_registry.update(actions)

        # Merge menu items into BASE_MENUS
        for group in shared_groups:
            labels = menu_registry.grouped().get(group, [])
            existing = BASE_MENUS.get(group, [])
            seen = {item.get("label") for item in existing if isinstance(item, dict)}

            for label in labels:
                if label in seen:
                    continue
                entry = menu_registry.get(label)
                if not entry:
                    continue
                existing.append({
                    "label": label,
                    "action": entry["func"].__name__,
                    "icon": entry.get("icon")
                })
            BASE_MENUS[group] = existing

        print(f"🔧 Injected shared actions from groups: {shared_groups}")

    def load_menus(self):
        print("📥 Merging static, config, and dynamic menus at startup...")

        # 1) menus.yaml → BASE_MENUS (structure only)
        #    If you want: keep your get_validated_menu_config() to load BASE_MENUS from config,
        #    or parse Settings/menus.yaml into BASE_MENUS directly.

        config_menus = shared.config.get("popmenu_cfg", {})
        self.merge_config_menus(config_menus)

        # 2) The registry is already populated by load_all_actions()
        # Build an action_lookup mapping from function name → func
        self.action_lookup = {
            entry["func"].__name__: entry["func"]
            for entry in global_menu_registry.all().values()
        }

        # 3) Inject shared groups from registry (use the actual registry)
        self.inject_registry_actions(global_menu_registry)

        # 4) Detect extra submenus
        #self.EXTRA_SUBMENUS = self.detect_extra_submenus()

        # 5) Finalize
        self.menus = BASE_MENUS
        self.action_metadata = global_menu_registry.all()

        print("✅ Menu system loaded with:")
        print(f" - {len(self.menus)} menu groups")
        print(f" - {len(self.action_metadata)} registered actions")

        print("📋 Loaded Menus:")
        for menu_name, items in self.menus.items():
            print(f" - {menu_name}:")
            for item in items:
                label = item.get("label") if isinstance(item, dict) else item
                print(f"    • {label}")

    def build_action_lookup(self, registry):
        lookup = {}
        for group in registry.grouped():
            for entry in registry.get_entries_by_group(group):
                func = entry.get("func")
                if not func:
                    continue
                func_name = func.__name__
                label = next((lbl for lbl, e in registry.all().items() if e is entry), None)
                lookup[func_name] = entry
                if label:
                    lookup[label] = entry
        return lookup

    # 📜 Registry diagnostic tool
    def show_widget_name_map(self):
        print("📜 Registered Widget Name Map:")
        for wid, name in self.resolver.widget_name_map.items():
            print(f"   - {name}: {wid}")

    # 🧭 Menu preview
    def show_available_menus(self):
        print("📦 Available popup menus:")
        for key, items in self.menus.items():
            print(f"  ▶ {key}: {items}")

    # 📣 Optional user feedback
    def show_popup_message(self, popup_key):
        print(f"📣 Popup activated for: {popup_key}")

    def show_menu_preview(self):
        preview_win = tk.Toplevel()
        preview_win.title("Popup Menu Preview")

        canvas = tk.Canvas(preview_win)
        scrollbar = tk.Scrollbar(preview_win, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas)

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        try:
            from customtkinter import get_appearance_mode
            theme = get_appearance_mode()
        except Exception:
            theme = "Dark"

        for popup_key, items in self.menus.items():
            label_fg = "#00BFFF" if str(theme).lower().startswith("dark") else "blue"
            label = tk.Label(frame, text=f"▶ {popup_key}", font=("Segoe UI", 10, "bold"), fg=label_fg)
            label.pack(anchor="w", pady=(10, 0))

            menu = tk.Menu(preview_win, tearoff=0)
            self.current_menu_group = popup_key
            self.build_menu_entries(menu, items, global_menu_registry)

            btn = tk.Button(frame, text="Show Menu", command=lambda m=menu: m.post(100, 100))
            btn.pack(anchor="w", padx=20)



