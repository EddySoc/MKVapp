#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     31/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# project_root/utils/decorator.py

import inspect,os

import os

def infer_group(filepath):
    print(f"\n🔍 Processing filepath: {filepath}")
    parts = os.path.normpath(filepath).split(os.sep)
    print(f"📂 Path parts: {parts}")

    known_roots = {
        "lb_files", "tb_info", "tb_debug", "tb_settings",
        "tb_folders", "tools", "test", "help"
    }

    for i, part in enumerate(parts):
        print(f"➡️ Inspecting part[{i}]: {part}")
        if part in known_roots:
            next_part = parts[i + 1] if i + 1 < len(parts) else None
            print(f"✅ Matched known root: {part}")
            if next_part:
                group = f"{part}/{next_part.replace('.py', '')}"
                print(f"📌 Inferred group: {group}")
                return group
            print(f"📌 Fallback group (no next part): {part}")
            return part

    print("⚠️ No known root matched. Returning 'unknown'")
    return "unknown"

def menu_tag(tag=None, label=None, icon=None, group=None):
    def decorator(func):
        from menus.menu_registry import global_menu_registry
        import inspect, os

        frame = inspect.getframeinfo(inspect.stack()[1][0])
        filepath = frame.filename
        folder_name = os.path.basename(os.path.dirname(filepath))

        if group is None:
            groups = [folder_name]
        elif isinstance(group, str):
            groups = [group]
        elif isinstance(group, (list, tuple, set)):
            groups = list(group)
        else:
            raise TypeError(f"Invalid group type: {type(group)}")

        menu_label = label or folder_name.replace("_", " ").title()
        tag_value = tag or func.__name__

        # Register under each group
        for g in groups:
            global_menu_registry.register(
                func=func,
                tag=tag_value,
                label=menu_label,
                icon=icon,
                group=g
            )

        # Attach metadata in both formats so either scanner works
        func._menu_meta = {
            "tag": tag_value,
            "label": menu_label,
            "icon": icon,
            "groups": groups,
            "separator": len(groups) > 1
        }
        func._menu_tags = [tag_value]
        func._menu_symbol = ""        # add if you want symbols
        return func
    return decorator