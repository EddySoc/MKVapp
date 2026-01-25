#-------------------------------------------------------------------------------
# Name:        core.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding_manager.py

import customtkinter as ct
from CTkListbox import CTkListbox
from widgets import BaseTBox
from binding.widget_scan import get_all_children
from binding.handlers import bind_ctk_entry, bind_basetbox, bind_listbox
from shared_data import get_shared
from utils.scan_helpers import update_files_from_selected_folder, browse_folder
import time

def resolve_widget_name(widget):
    name = getattr(widget, "custom_name", None)
    if not name:
        # Try smarter fallback
        name = widget.winfo_class().lower()
        if hasattr(widget.master, "custom_name"):
            name = f"{widget.master.custom_name}_{name}"
        else:
            name = widget.winfo_name().lower()
    widget.custom_name = name
    return name

# 🔀 Map widget classes to their binders
BINDING_HANDLERS = {
    ct.CTkEntry: bind_ctk_entry,
    BaseTBox: bind_basetbox,
    CTkListbox: bind_listbox
}

class BindingManager:
    _instance = None
    _initialized = False

    def __init__(self, app, popup_menu, resolver=None):
        self.app = app
        self.popup = popup_menu
        self.bindings = {}
        self.widget_menu_map = {}
        self.shared = get_shared()
        self.known_widgets = {}
        self.widget_tree = {}
        self.widget_resolver = resolver  # 🔌 Optional Resolver
        self.__class__._instance = self
        self.__class__._initialized = True



        self.scan_and_register()  # 🔗 Two-phase handshake

        self._register_widgets()
        self._bind_events()

    @classmethod
    def get_instance(cls):
        if cls._instance is not None:
            return cls._instance

        # Fallback to shared state
        from shared_data import get_shared
        shared = get_shared()
        if hasattr(shared, "binding_manager"):
            cls._instance = shared.binding_manager
            cls._initialized = True
            return cls._instance

        raise RuntimeError("BindingManager not initialized and not found in shared state.")

    def scan_and_register(self, scan_known=True, build_tree=True, auto_register=True):
        """Run scanning and registration phases with granular control."""

        if scan_known:
            self.scan_known_widgets()

        if build_tree:
            self.build_widget_tree()

        if auto_register and self.widget_resolver:
            print("🔄 Handing structure to WidgetResolver...")
            self.widget_resolver.auto_register_from(self.app)
            print("✅ WidgetResolver registration complete.")

    def build_widget_tree(self):
        def recurse(widget, trail):
            name = resolve_widget_name(widget)  # Or self.resolve_name(widget) if it's a method
            self.widget_tree[widget] = "_".join(trail + [name])
            for child in widget.winfo_children():
                recurse(child, trail + [name])
        recurse(self.app, [])

    def scan_known_widgets(self):
        self.known_widgets = {}
        self.widget_subtrees = {}
        for attr_name in dir(self.app):
            widget = getattr(self.app, attr_name, None)
            if not self._is_valid_widget(widget):
                continue
            self.known_widgets[attr_name] = widget
            # store the set of all descendants (including the widget itself)
            #print(f"🧪 Scanning widget: {widget}")

            try:
                all_nodes = set(get_all_children(widget))
                all_nodes.add(widget)
            except Exception as ex:
                print(f"🚫 Skipping widget: {widget} → {type(widget)} due to error: {ex}")
                all_nodes = set()
            all_nodes.add(widget)
            self.widget_subtrees[attr_name] = all_nodes
            #print(f"📌 Registered widget: {attr_name} → {widget}")

    def _is_valid_widget(self, widget):
        # Skip anything that’s not an instance (e.g., class objects)
        if isinstance(widget, type):
            return False

        # Skip None, strings, ints, etc.
        if not hasattr(widget, "winfo_class"):
            return False

        # Optionally skip hidden or disabled widgets
        # Example: widget must be mapped to the screen
        try:
            if widget.winfo_ismapped() is False:
                return False
        except Exception:
            pass  # Some widgets may not support this method

        return True

    def _register_widgets(self):
        def on_focus(event):
            from utils.scan_helpers import update_entry_styles
            from utils.scan_helpers import focusin_handler
            focusin_handler(event, self.app)
            update_entry_styles(self.shared)

        for widget in get_all_children(self.app):
            widget_type = type(widget)
            name = resolve_widget_name(widget)
            self.widget_menu_map[widget] = name

            if widget_type in BINDING_HANDLERS:
                #print(f"🔗 Binder found for: {widget_type.__name__} → '{name}'")
                binder = BINDING_HANDLERS[widget_type]
                extra_args = {}
                # Apply binder logic here
            else:
                #print(f"⚠️ No binder found for: {widget_type.__name__} → '{name}'")
                continue  # Or skip logic safely

            if widget_type is ct.CTkEntry:
                var = self.shared.entry_data.get(name, {}).get("var")
                extra_args = {
                    "on_focus": on_focus,
                    "on_browse": lambda e, key=name: browse_folder(key)
                }

            elif widget_type is BaseTBox:
                extra_args = {
                    "on_right_click": self._debug_right_click,
                    "on_release": update_files_from_selected_folder if name == "tb_folders" else None
                }

            elif widget_type is CTkListbox:
                extra_args = {
                    "on_right_click": self.popup.on_right_click
                }

            binder(self.bindings, widget, name, **extra_args)

    def _bind_events(self):

        #print(f"[{time.strftime('%H:%M:%S')}] 🎯 _bind_events() triggered")
        #print(f"🔍 Bindings available: {len(self.bindings)}")

        for widget, event_list in self.bindings.items():
            for event, callback in event_list:
                try:
                    widget.unbind(event)
                    widget.bind(event, callback)
                    #print(f"🔗 Binding {event} to {widget}")
                except Exception as e:
                    print(f"❌ Failed to bind {event} to {widget}: {e}")
        #print("🎯 Running _bind_events with", len(self.bindings), "bindings")

    def list_registered_widgets(self):
        for widget, name in self.widget_menu_map.items():
            print(f"📎 {name}: {widget}")

    def summary(self):
        print("\n📊 Widget Diagnostics")
        for widget, name in self.widget_menu_map.items():
            print(f"🔹 {name}: {type(widget).__name__}")
            for event, _ in self.bindings.get(widget, []):
                print(f"   ↪ bound: {event}")

    # 🎯 Instance-aware handlers
    def _debug_right_click(self, event):
        #print("Right-click triggered")
        self.popup.on_right_click(event)

    def bind_right_click(self, widget):
        try:
            name = resolve_widget_name(widget)
            widget.bind("<Button-3>", lambda e: self.popup.on_right_click(e))
            print(f"✅ Bound right-click to widget: {name}")
        except Exception as ex:
            print(f"⚠️ Failed to bind right-click to {widget}: {ex}")

    def bind_all_right_clicks(self, parent):
        try:
            for child in parent.winfo_children():
                if child.winfo_class() not in ["Frame", "PanedWindow", "Canvas"]:
                    self.bind_right_click(child)
                self.bind_all_right_clicks(child)
        except Exception as ex:
            print(f"⚠️ Error scanning widget tree: {ex}")

    def bind_all_widgets(self, widget_map):
        for name in dir(self.app):
            widget = getattr(self.app, name, None)
            for widget_type, binder in widget_map.items():
                if isinstance(widget, widget_type):
                    binder(self.bindings, widget, name)