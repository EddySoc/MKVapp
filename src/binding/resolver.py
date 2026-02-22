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
# Lazy import to avoid circular dependency
# from shared_data import get_shared
from config.smart_config_manager import config_mgr

SCAN_MODES = {
    "all": lambda widget: hasattr(widget, "winfo_class") and not isinstance(widget, type),
    "interactive_only": lambda widget: hasattr(widget, "winfo_class") and not isinstance(widget, type)
                                    and widget.winfo_ismapped(),
    "debug_elements": lambda widget: hasattr(widget, "debug_tag") and not isinstance(widget, type),
}


class WidgetNameResolver:
    def __init__(self, root_widget,config_data,scan_mode="all", widget_name_map=None, menus=None):
        self.root = root_widget

        # 👇 Scan Mode Setup
        self.scan_filter = SCAN_MODES.get(scan_mode, SCAN_MODES["all"])

        self.config_data = config_data
        self.config_mgr = config_mgr
        self.anchor_map = self.learn_anchor_map_from_cfg

        # 👇 Registry Setup
        self.widget_name_map = widget_name_map or {}      # Allows external map or fresh one

        # 👇 Menu Data
        self.menus = menus or {}                          # Optional menus for context/popup use

    def auto_register_from(self, app):
        from binding import get_all_children
        for attr_name in dir(app):
            if attr_name.startswith("__"):
                continue

            widget = getattr(app, attr_name, None)
            if not self.scan_filter(widget):
                continue

            # 🌲 Traverse into children as well
            for child in get_all_children(widget) + [widget]:
                widget_id = str(child)
                widget_name = getattr(child, "custom_name", None) or child.winfo_name()

                self.widget_name_map[widget_id] = widget_name

                #print(f"📌 Registered widget: {widget_name} → {widget_id}")

    def resolve_registered_name(self, widget_id):
        """
        Return the attribute name for the most specific registered widget
        whose ID is a prefix of widget_id.
        """
        # 1) Exact hit
        if widget_id in self.widget_name_map:
            return self.widget_name_map[widget_id]

        # 2) Find all registered IDs that prefix the clicked ID
        candidates = [
            (wid, name)
            for wid, name in self.widget_name_map.items()
            if widget_id.startswith(wid + ".")
        ]
        if not candidates:
            return None

        # 3) Pick the longest‐ID (most specific)
        best_wid, best_name = max(candidates, key=lambda t: len(t[0]))
        return best_name

    def recursive_scan(self, widget):
        for child in widget.winfo_children():
            widget_id = str(child)
            self.recursive_scan(child)  # Dive deeper

    def full_scan(self, app_root):
        # Scan attributes exposed by your App
        self.auto_register_from(app_root)

        # Recursively dive into the widget tree
        self.recursive_scan(app_root)


    def resolve_menu_from_path(self, widget_path):
        """
        Attempt to resolve popup menu key by scanning ancestors in widget_path.
        """
        parts = widget_path.split(".")
        cleaned_parts = [p.lstrip("!@#") for p in parts if p]

    def resolve_registered_name_by_hierarchy(self, widget_path):
        parts = widget_path.split(".")
        while parts:
            current = ".".join(parts)
            parts.pop()  # Move one level up
        return None

    def resolve_popup_key_from_path(self, widget_path):
        menu_cfg = self.config_mgr.get("popmenu_cfg", {})
        known_keys = list(menu_cfg.keys())

        # STEP 1 — Direct match: exact widget names like tb_debug, tb_info
        for key in known_keys:
            if key in widget_path.split("."):
                print(f"🎯 Direct key match: {key}")
                return key

        # STEP 2 — Partial anchor match: anchor is substring of widget_path
        anchor_map = {
            ".!ctktabview.!ctkframe.!myframe2.!filterlistbox": "lb_files",
            ".!ctktabview.!ctkframe.!myframe2.!basetbox": "tb_info",
            ".!ctktabview.!ctkframe.!myframe2.!basetbox2": "tb_folders",
            ".!ctktabview.!ctkframe2.!basetbox": "tb_settings",

            ".!ctktabview.!ctkframe4.!basetbox": "tb_debug"
        }

        for anchor, menu_key in sorted(anchor_map.items(), key=lambda x: -len(x[0])):
            if anchor in widget_path:
                #print(f"🧭 Partial anchor match: {anchor} → {menu_key}")
                return menu_key

        print(f"🚫 No popup menu match for widget path: {widget_path}")
        return None

    def build_path_to_name_map(root_widget):
        path_name_map = {}

        def walk(widget):
            custom_name = getattr(widget, "custom_name", None)
            if not custom_name:
                return  # ⛔️ Skip unnamed widgets

            widget_path = str(widget)
            path_name_map[widget_path] = custom_name

            for child in widget.winfo_children():
                walk(child)

        walk(root_widget)
        return path_name_map

    def learn_anchor_map_from_cfg():
        anchor_map = {}
        popmenu_cfg = config.get("popmenu_cfg", {})

        for key, cfg in popmenu_cfg.items():
            # Look for a distinctive anchor keyword in the widget path
            path = cfg.get("widget_path", "")  # or wherever the widget path lives
            segments = path.split(".")
            for segment in segments:
                if segment and segment not in anchor_map:
                    anchor_map[segment] = key
                    print(f"🔍 Learned anchor: {segment} → {key}")
                    break  # Stop at first unique match
        return anchor_map

    def get_root_widget(self):
        return self.root

    def collect_named_widgets(self):
        root = self.get_root_widget()
        named_widgets = {}

        def recurse(widget):
            custom_name = getattr(widget, "custom_name", None)
            if custom_name:
                named_widgets[custom_name] = widget
            for child in widget.winfo_children():
                recurse(child)

        recurse(root)
        return named_widgets

    def _is_valid_widget(self, widget):
        return hasattr(widget, "winfo_class")  # or customize this for your app